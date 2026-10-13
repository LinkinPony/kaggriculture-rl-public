#include "boatlee/detail.hpp"

#include <algorithm>
#include <array>
#include <cstdint>
#include <optional>
#include <utility>
#include <vector>

namespace kagg::boatlee::detail {
namespace {

constexpr int kIceCreamShop = 3;
constexpr int kPizzaShop = 5;
constexpr int kSmoothieShop = 6;
constexpr int kYarnStore = 7;
constexpr int kWeedReplaySteps = 8;

constexpr std::array<int, 4> kFrontRunItems = {
    item::kWool, item::kMilk, item::kMelon, item::kStrawberry};

bool Contains(const std::vector<int>& values, int expected, size_t limit) {
  const size_t stop = std::min(values.size(), limit);
  return std::find(values.begin(), values.begin() + stop, expected) !=
         values.begin() + stop;
}

bool UsesMilk(const std::vector<int>& shops) {
  return Contains(shops, kPizzaShop, 3) ||
         Contains(shops, kIceCreamShop, 3) ||
         Contains(shops, kSmoothieShop, 3);
}

bool LegacyLayout(const Engine& engine, int player, MoonState* state) {
  const int step = engine.step_index();
  if (step == 0) state->legacy_layout.reset();
  if (!state->legacy_layout.has_value() && step >= 24 && step < 72) {
    int wheat = 0;
    int melon = 0;
    int cow = 0;
    int sheep = 0;
    int bare_pasture = 0;
    const Farm& opponent = engine.farm(1 - player);
    for (const Tile& tile : opponent.tiles) {
      if (tile.kind == TileKind::kPlant) {
        if (tile.crop == item::kWheat) ++wheat;
        if (tile.crop == item::kMelon) ++melon;
      } else if (tile.kind == TileKind::kStructure && tile.has_animal) {
        if (tile.animal == 1) ++cow;
        if (tile.animal == 2) ++sheep;
      } else if (tile.kind == TileKind::kStructure &&
                 tile.structure == StructureKind::kPasture) {
        ++bare_pasture;
      }
    }
    state->legacy_layout =
        wheat == 5 && melon == 5 && cow == 1 && sheep == 4 &&
        bare_pasture == 0 && opponent.money <= 12.0;
  }
  return state->legacy_layout.value_or(false);
}

int64_t PickupReserve(const PlayerAction& action, int product) {
  int64_t reserve = 0;
  const auto add = [&](const UnitAction& order) {
    if (order.op == UnitOp::kPickup && order.arg == product) {
      reserve += std::max<int64_t>(0, order.n);
    }
  };
  add(action.farmer);
  for (const UnitAction& order : action.hands) add(order);
  return reserve;
}

bool ShopSells(int shop, int product) {
  const ShopData& data = kShops[shop];
  return std::find(data.products.begin(),
                   data.products.begin() + data.n_products,
                   product) != data.products.begin() + data.n_products;
}

bool TownDemandNow(const Engine& engine, int product, int step) {
  if (product != item::kFertilizer && step % 24 == 0) return true;
  if (step % 4 != 0) return false;
  for (const int shop : engine.town_shops()) {
    if (ShopSells(shop, product)) return true;
  }
  return false;
}

PlayerAction RepayFrontRun(PlayerAction action, FrontRunState* state,
                           int step) {
  if (state->due_step != step) return action;
  std::vector<std::optional<MarketOrder>> market;
  market.reserve(action.market.size());
  for (auto slot : action.market) {
    if (IsSell(slot) && state->due[slot->item] > 0) {
      int64_t requested = std::max<int64_t>(0, slot->remaining);
      const int64_t reduction =
          std::min(requested, state->due[slot->item]);
      requested -= reduction;
      state->due[slot->item] -= reduction;
      if (requested <= 0) continue;
      slot->remaining = requested;
    }
    market.push_back(std::move(slot));
  }
  action.market = std::move(market);
  state->due_step = -1;
  state->due.fill(0);
  return action;
}

PlayerAction ApplyFrontRun(const Portfolio& portfolio, const Engine& engine,
                           int player, PlayerAction action,
                           FrontRunState* state) {
  const int step = engine.step_index();
  const auto future = portfolio.sell_totals(Tape::kMunib, step + 1);
  std::array<int64_t, kNumProducts> moved{};
  for (const int product : kFrontRunItems) {
    const int64_t target = std::max<int64_t>(0, future[product]);
    if (target <= 0 || TownDemandNow(engine, product, step)) continue;
    const int64_t stock =
        std::max<int64_t>(0, engine.priv(player).shed[product]);
    const int64_t reserve =
        PickupReserve(action, product) + SellTotals(action)[product];
    const int64_t quantity =
        std::min(target, std::max<int64_t>(0, stock - reserve));
    if (quantity <= 0) continue;
    const size_t before = action.market.size();
    AddSell(&action, product, quantity);
    if (FirstSell(&action, product) != nullptr &&
        (before == action.market.size() || before < kMaximumOrders)) {
      moved[product] += quantity;
    }
  }
  if (std::any_of(moved.begin(), moved.end(),
                  [](int64_t value) { return value > 0; })) {
    state->due_step = step + 1;
    state->due = moved;
  }
  return action;
}

}  // namespace

Tape SelectMoonTape(const Engine& engine, int player, MoonState* state) {
  const auto& shops = engine.town_shops();
  int route;
  if (!shops.empty() && shops[0] == kYarnStore) {
    route = 3;
  } else if (Contains(shops, kYarnStore, 2)) {
    route = 4;
  } else if (Contains(shops, kYarnStore, 3)) {
    route = 2;
  } else if (UsesMilk(shops)) {
    route = 0;
  } else {
    route = 1;
  }
  if (LegacyLayout(engine, player, state)) route += 5;
  return static_cast<Tape>(route);
}

PlayerAction ApplyWeedRepair(const Portfolio& portfolio, const Engine& engine,
                             int player, Tape tape, PlayerAction action,
                             RepairState* state) {
  AlignHands(engine, player, &action);
  const int step = engine.step_index();
  const Farm& farm = engine.farm(player);
  const int unit_count = 1 + static_cast<int>(farm.hands.size());
  state->active.resize(unit_count);
  for (int actor = 0; actor < unit_count; ++actor) {
    RepairTransaction& transaction = state->active[actor];
    if (!transaction.active) continue;
    const int age = step - transaction.start;
    if (age == 1) {
      *MutableUnit(&action, actor) = transaction.intended;
    } else if (age >= 2 && age <= 1 + kWeedReplaySteps) {
      *MutableUnit(&action, actor) =
          portfolio.unit_action(tape, step - 1, actor);
    } else {
      transaction = RepairTransaction{};
    }
  }
  for (int actor = 0; actor < unit_count; ++actor) {
    RepairTransaction& transaction = state->active[actor];
    const UnitAction intended = Unit(action, actor);
    if (transaction.active ||
        (intended.op != UnitOp::kBuildPasture &&
         intended.op != UnitOp::kPlant)) {
      continue;
    }
    const Tile* tile = TileAt(engine, farm, Position(farm, actor));
    if (tile == nullptr || tile->kind != TileKind::kWeed) continue;
    transaction.active = true;
    transaction.start = step;
    transaction.intended = intended;
    *MutableUnit(&action, actor) = UnitAction{UnitOp::kDig, -1, 1};
  }
  AlignHands(engine, player, &action);
  return action;
}

PlayerAction ReplayAct(const Portfolio& portfolio, const Engine& engine,
                       int player, Tape tape, bool front_run,
                       ReplayState* state) {
  const int step = engine.step_index();
  if (step == 0 || step < state->last_step) *state = ReplayState{};
  state->last_step = step;
  if (state->front_run.due_step >= 0 &&
      state->front_run.due_step < step) {
    state->front_run.due_step = -1;
    state->front_run.due.fill(0);
  }
  PlayerAction action = portfolio.action(tape, step);
  action = ApplyWeedRepair(portfolio, engine, player, tape,
                           std::move(action), &state->repair);
  action = RepayFrontRun(std::move(action), &state->front_run, step);
  if (front_run) {
    action = ApplyFrontRun(portfolio, engine, player, std::move(action),
                           &state->front_run);
  }
  AlignHands(engine, player, &action);
  return action;
}

}  // namespace kagg::boatlee::detail
