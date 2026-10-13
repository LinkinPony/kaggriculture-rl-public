#include "opponents/portfolio.hpp"

#include <algorithm>
#include <numeric>
#include <stdexcept>

namespace kagg::opponents {

void Portfolio::Prepare() {
  if (routes.empty()) throw std::invalid_argument("empty opponent portfolio");
  for (const auto& route : routes) {
    if (route.size() < 719 || route.size() > 720) {
      throw std::invalid_argument(
          "opponent route must have 719 or 720 actions");
    }
    std::vector<Products> suffix(route.size() + 1);
    for (int step = static_cast<int>(route.size()) - 1; step >= 0; --step) {
      suffix[step] = suffix[step + 1];
      const auto sold = SellTotals(route[step]);
      for (int item = 0; item < kNumProducts; ++item)
        suffix[step][item] += sold[item];
    }
    suffix_sells.push_back(std::move(suffix));
  }
}

const PlayerAction& Portfolio::Action(int route, int step) const {
  const auto& tape = routes.at(route);
  return tape[std::clamp(step, 0, static_cast<int>(tape.size()) - 1)];
}

UnitAction Portfolio::Unit(int route, int step, int unit) const {
  const auto& action = Action(route, step);
  return unit == 0 ? action.farmer
                   : (unit <= static_cast<int>(action.hands.size())
                          ? action.hands[unit - 1]
                          : UnitAction{});
}

int64_t Portfolio::FutureSells(int route, int step, int item) const {
  const auto& suffix = suffix_sells.at(route);
  return step < static_cast<int>(suffix.size())
             ? suffix[std::max(0, step)][item]
             : 0;
}

UnitAction& Unit(PlayerAction& action, int index) {
  return index == 0 ? action.farmer : action.hands[index - 1];
}

const UnitAction& Unit(const PlayerAction& action, int index) {
  return index == 0 ? action.farmer : action.hands[index - 1];
}

std::pair<int, int> Position(const Farm& farm, int unit) {
  return unit == 0 ? std::pair{farm.farmer_x, farm.farmer_y}
                   : farm.hands[unit - 1];
}

const Tile& UnitTile(const Engine& engine, int player, int unit) {
  const auto [x, y] = Position(engine.farm(player), unit);
  return engine.farm(player).tiles[y * engine.config().board_size + x];
}

Products SellTotals(const PlayerAction& action) {
  Products result{};
  for (const auto& order : action.market) {
    if (order && order->kind == OrderKind::kSell &&
        order->item < kNumProducts) {
      result[order->item] += std::max<int64_t>(0, order->remaining);
    }
  }
  return result;
}

int64_t PickupReserve(const PlayerAction& action, int item) {
  int64_t result = 0;
  for (int i = 0; i <= static_cast<int>(action.hands.size()); ++i) {
    const auto& unit = Unit(action, i);
    if (unit.op == UnitOp::kPickup && unit.arg == item)
      result += std::max<int64_t>(0, unit.n);
  }
  return result;
}

int64_t Total(const Stock& stock) {
  return std::accumulate(stock.begin(), stock.end(), int64_t{0});
}

int64_t Carried(const PrivateState& state, int item) {
  int64_t result = 0;
  for (const auto& inventory : state.inventories)
    result += std::max<int64_t>(0, inventory.Get(item));
  return result;
}

int64_t Fibonacci(int index) {
  int64_t a = 1, b = 1;
  for (int i = 0; i < index; ++i) {
    const int64_t next = a + b;
    a = b;
    b = next;
  }
  return a;
}

int ShopDemand(const std::vector<int>& shops, int item) {
  int result = 0;
  for (int id : shops) {
    const auto& shop = kShops[id];
    for (int j = 0; j < shop.n_products; ++j) {
      if (shop.products[j] == item) result += shop.n_products == 1 ? 2 : 1;
    }
  }
  return result;
}

int Demand(const std::vector<int>& shops, int item, int step, int shop_interval,
           int center_interval) {
  return (step % center_interval == 0 && item != item::kFertilizer ? 1 : 0) +
         (step % shop_interval == 0 ? ShopDemand(shops, item) : 0);
}

void Align(const Engine& engine, int player, PlayerAction* action) {
  action->hands.resize(engine.farm(player).hands.size());
}

void WeedRepair(const Portfolio& portfolio, int route, const Engine& engine,
                int player, PlayerAction* action, RepairState* state) {
  const int step = engine.step_index();
  if (step == 0 || step < state->last) *state = RepairState{};
  state->last = step;
  Align(engine, player, action);
  const int count = static_cast<int>(action->hands.size()) + 1;
  state->units.resize(count);
  for (int i = 0; i < count; ++i) {
    auto& repair = state->units[i];
    const int age = step - repair.start;
    if (age == 1)
      Unit(*action, i) = repair.intended;
    else if (age >= 2 && age <= 9)
      Unit(*action, i) = portfolio.Unit(route, step - 1, i);
    else
      repair.start = -100;
  }
  for (int i = 0; i < count; ++i) {
    auto& repair = state->units[i];
    auto& unit = Unit(*action, i);
    if (repair.start != -100 ||
        (unit.op != UnitOp::kPlant && unit.op != UnitOp::kBuildPasture) ||
        UnitTile(engine, player, i).kind != TileKind::kWeed)
      continue;
    repair = {step, unit};
    unit = {UnitOp::kDig, -1, 1};
  }
}

bool MergeSale(PlayerAction* action, int item, int64_t quantity, bool front) {
  for (auto& order : action->market) {
    if (order && order->kind == OrderKind::kSell && order->item == item) {
      order->remaining = std::max<int64_t>(0, order->remaining) + quantity;
      return true;
    }
  }
  if (action->market.size() >= 10) return false;
  MarketOrder sale{OrderKind::kSell, item, quantity};
  if (front)
    action->market.insert(action->market.begin(), sale);
  else
    action->market.push_back(sale);
  return true;
}

Stock ProjectShed(const Engine& engine, int player, const PlayerAction& action,
                  bool pickups, bool animal_place, int64_t capacity,
                  int64_t minimum_quantity) {
  Stock shed = engine.priv(player).shed;
  const auto& priv = engine.priv(player);
  for (int i = 0; i <= static_cast<int>(action.hands.size()); ++i) {
    if (i >= static_cast<int>(priv.inventories.size())) continue;
    const auto [x, y] = Position(engine.farm(player), i);
    if (!IsShedAdjacent(x, y, engine.config().board_size)) continue;
    const auto& unit = Unit(action, i);
    const auto& inv = priv.inventories[i];
    auto deposit = [&](int item, int64_t count) {
      shed[item] += std::min(std::max<int64_t>(0, count),
                             std::max<int64_t>(0, capacity - Total(shed)));
    };
    if (pickups && unit.op == UnitOp::kPickup && unit.arg >= 0) {
      shed[unit.arg] -=
          std::min(shed[unit.arg], std::max(minimum_quantity, unit.n));
    } else if (unit.op == UnitOp::kDrop) {
      for (auto [item, count] : inv.items) deposit(item, count);
    } else if (unit.op == UnitOp::kPlace && unit.arg >= 0) {
      if (unit.arg >= item::kGoose) {
        if (!animal_place) continue;
        const auto& tile = UnitTile(engine, player, i);
        if (tile.kind == TileKind::kStructure && !tile.has_animal &&
            tile.structure == kAnimals[unit.arg - item::kGoose].structure)
          continue;
      }
      deposit(unit.arg,
              std::min(std::max(minimum_quantity, unit.n), inv.Get(unit.arg)));
    }
  }
  return shed;
}

}  // namespace kagg::opponents
