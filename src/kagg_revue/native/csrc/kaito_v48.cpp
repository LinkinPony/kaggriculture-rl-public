#include "kaito_v48.hpp"

#include <algorithm>
#include <array>
#include <cstdint>
#include <cstring>
#include <map>
#include <memory>
#include <stdexcept>
#include <utility>
#include <vector>

#include "action_codec.hpp"
#include "kaito_v48_support.hpp"

namespace kagg::kaito {
namespace {

constexpr int kCloneHorizon = 2;
constexpr int kCloneDetectionStart = 48;
constexpr int kCloneActiveStart = 160;
constexpr int kCloneActiveStop = 700;
constexpr int kCloneStreakRequired = 24;
constexpr int kCloneMaximumBatch = 10;
constexpr int kMaximumMarketOrders = 10;
constexpr int kReplaySteps = 8;

constexpr int kBakery = 0;
constexpr int kBrunchSpot = 1;
constexpr int kFarmersMarket = 2;
constexpr int kPetCafe = 4;
constexpr int kPizzaShop = 5;
constexpr int kYarnStore = 7;

UnitAction Pass() { return UnitAction{UnitOp::kPass, -1, 1}; }

int RouteIndex(Route route) { return static_cast<int>(route); }

Route RouteEvent(const Engine& engine) {
  const int step = engine.step_index();
  const auto& shops = engine.town_shops();
  if (!shops.empty() && shops[0] == kYarnStore && step >= 88) {
    return Route::kYarnFast;
  }
  if (!shops.empty() && shops[0] == kFarmersMarket && step >= 120) {
    return Route::kFarmFast;
  }
  if (shops.size() >= 2 && shops[0] != kYarnStore &&
      shops[0] != kFarmersMarket && shops[1] == kYarnStore && step >= 153) {
    return Route::kYarnSecond;
  }
  const bool allowed_prefix =
      shops.size() >= 2 &&
      ((shops[0] == kBrunchSpot && shops[1] == kPetCafe) ||
       (shops[0] == kPetCafe && shops[1] == kFarmersMarket));
  if (shops.size() >= 3 && shops[0] != kYarnStore &&
      shops[0] != kFarmersMarket && shops[1] != kYarnStore &&
      shops[2] == kYarnStore && allowed_prefix && step >= 216) {
    return Route::kYarnThird;
  }
  return Route::kDefault;
}

bool BakeryCapitalCandidate(const Engine& engine, int player) {
  const auto& shops = engine.town_shops();
  if (engine.step_index() != 160 || shops.size() < 2 ||
      shops[0] != kBakery || shops[1] != kPizzaShop) {
    return false;
  }
  const AssetCounts counts = PublicAssetCounts(engine.farm(1 - player));
  return counts.cow >= 3 && counts.sheep >= 2 && counts.melon >= 10 &&
         counts.goose <= 0;
}

bool CloneVetoCandidate(const Engine& engine, int player) {
  const auto& shops = engine.town_shops();
  if (engine.step_index() != 120 || shops.empty() || shops[0] != kBakery) {
    return false;
  }
  const AssetCounts counts = PublicAssetCounts(engine.farm(1 - player));
  return counts.sheep >= 4 && counts.cow <= 1 && counts.wheat >= 8 &&
         counts.melon >= 7 && counts.goose <= 0;
}

std::array<int64_t, kNumProducts> SellTotals(const PlayerAction& action) {
  std::array<int64_t, kNumProducts> totals{};
  for (const auto& slot : action.market) {
    if (slot.has_value() && slot->kind == OrderKind::kSell && slot->item >= 0 &&
        slot->item < kNumProducts) {
      totals[slot->item] += std::max<int64_t>(0, slot->remaining);
    }
  }
  return totals;
}

bool IsWeedAt(const Engine& engine, int player, int unit) {
  const Farm& farm = engine.farm(player);
  const int x = unit == 0 ? farm.farmer_x : farm.hands[unit - 1].first;
  const int y = unit == 0 ? farm.farmer_y : farm.hands[unit - 1].second;
  const int board_size = engine.config().board_size;
  if (x < 0 || y < 0 || x >= board_size || y >= board_size) return false;
  return farm.tiles[static_cast<size_t>(y) * board_size + x].kind ==
         TileKind::kWeed;
}

struct RepairTransaction {
  bool active = false;
  int start = 0;
  UnitAction intended = Pass();
};

struct RepairState {
  bool initialized = false;
  int last_step = -1;
  std::vector<RepairTransaction> active;
};

struct PreemptionState {
  bool initialized = false;
  int last_step = -1;
  int near_streak = 0;
  bool latched = false;
  Route route = Route::kDefault;
  std::map<int, std::array<int64_t, kNumProducts>> due;
  bool clone_veto = false;
};

struct SeatState {
  Route selected = Route::kDefault;
  int last_step = -1;
  std::array<RepairState, kRouteCount> repair;
  PreemptionState preemption;
};

PlayerAction ApplyRepair(const Portfolio& portfolio, const Engine& engine,
                         int player, Route route, PlayerAction action,
                         RepairState* state) {
  const int step = engine.step_index();
  AlignHands(engine, player, &action);
  const int unit_count = 1 + static_cast<int>(action.hands.size());
  if (step == 0 || !state->initialized || step < state->last_step) {
    *state = RepairState{};
    state->initialized = true;
  }
  state->last_step = step;
  state->active.resize(unit_count);

  const auto set_unit = [&action](int unit, const UnitAction& request) {
    if (unit == 0) {
      action.farmer = request;
    } else {
      action.hands[unit - 1] = request;
    }
  };
  const auto get_unit = [&action](int unit) -> UnitAction {
    return unit == 0 ? action.farmer : action.hands[unit - 1];
  };
  for (int unit = 0; unit < unit_count; ++unit) {
    RepairTransaction& transaction = state->active[unit];
    if (!transaction.active) continue;
    const int age = step - transaction.start;
    if (age == 1) {
      set_unit(unit, transaction.intended);
    } else if (age >= 2 && age <= 1 + kReplaySteps) {
      set_unit(unit, portfolio.unit_action(route, step - 1, unit));
    } else {
      transaction = RepairTransaction{};
    }
  }
  for (int unit = 0; unit < unit_count; ++unit) {
    RepairTransaction& transaction = state->active[unit];
    const UnitAction intended = get_unit(unit);
    if (transaction.active ||
        (intended.op != UnitOp::kBuildPasture && intended.op != UnitOp::kPlant) ||
        !IsWeedAt(engine, player, unit)) {
      continue;
    }
    transaction.active = true;
    transaction.start = step;
    transaction.intended = intended;
    set_unit(unit, UnitAction{UnitOp::kDig, -1, 1});
  }
  AlignHands(engine, player, &action);
  ReorderSellSlots(engine, &action,
                   engine.config().center_sell_interval >= 24 ? 0.25 : 0.0);
  return action;
}

PlayerAction ApplyPreemption(const Portfolio& portfolio, const Engine& engine,
                             int player, Route route, PlayerAction action,
                             PreemptionState* state) {
  AlignHands(engine, player, &action);
  const int step = engine.step_index();
  if (step == 0 || !state->initialized || step < state->last_step) {
    *state = PreemptionState{};
    state->initialized = true;
  }
  state->last_step = step;
  if (CloneVetoCandidate(engine, player)) state->clone_veto = true;

  if (CloneDistance(engine) <= 2.0) {
    ++state->near_streak;
  } else {
    state->near_streak = 0;
  }
  if (!state->latched && step >= kCloneDetectionStart &&
      state->near_streak >= kCloneStreakRequired) {
    state->latched = true;
  }
  if (route != state->route) {
    if (!state->due.empty()) state->due.clear();
    state->route = route;
  }

  std::array<int64_t, kNumProducts> due_now{};
  if (const auto found = state->due.find(step); found != state->due.end()) {
    due_now = found->second;
    state->due.erase(found);
  }
  std::vector<std::optional<MarketOrder>> adjusted;
  adjusted.reserve(action.market.size());
  for (auto slot : action.market) {
    if (slot.has_value() && slot->kind == OrderKind::kSell && slot->item >= 0 &&
        slot->item < kNumProducts) {
      int64_t& debt = due_now[slot->item];
      if (debt > 0) {
        const int64_t quantity = std::max<int64_t>(0, slot->remaining);
        const int64_t reduction = std::min(quantity, debt);
        slot->remaining = quantity - reduction;
        debt -= reduction;
        if (slot->remaining <= 0) continue;
      }
    }
    adjusted.push_back(std::move(slot));
  }
  if (step < 718) {
    auto& next_due = state->due[step + 1];
    bool retained = false;
    for (int product = 0; product < kNumProducts; ++product) {
      if (due_now[product] > 0) {
        next_due[product] += due_now[product];
        retained = true;
      }
    }
    if (!retained && std::all_of(next_due.begin(), next_due.end(),
                                 [](int64_t value) { return value == 0; })) {
      state->due.erase(step + 1);
    }
  }
  action.market = std::move(adjusted);

  const bool eligible =
      state->latched && !state->clone_veto && step >= kCloneActiveStart &&
      step < kCloneActiveStop && step + kCloneHorizon < kRouteTurns &&
      static_cast<int>(action.market.size()) < kMaximumMarketOrders;
  if (!eligible) return action;

  const auto future = portfolio.sell_totals(route, step + kCloneHorizon);
  const auto existing = SellTotals(action);
  auto available = ProjectedShed(engine, player, action);
  for (int product = 0; product < kNumProducts; ++product) {
    available[product] =
        std::max<int64_t>(0, available[product] - existing[product]);
  }
  struct Candidate {
    double value;
    int product;
    int64_t quantity;
  };
  std::vector<Candidate> candidates;
  for (int product = 0; product < kNumProducts; ++product) {
    const int64_t quantity = std::min(
        {std::max<int64_t>(0, future[product] - existing[product]),
         std::max<int64_t>(0, available[product]),
         static_cast<int64_t>(kCloneMaximumBatch)});
    if (quantity > 0) {
      candidates.push_back(Candidate{
          static_cast<double>(engine.market().prices[product]) * quantity,
          product, quantity});
    }
  }
  std::sort(candidates.begin(), candidates.end(), [](const Candidate& left,
                                                      const Candidate& right) {
    if (left.value != right.value) return left.value > right.value;
    return std::strcmp(kItemNames[left.product], kItemNames[right.product]) > 0;
  });
  int64_t remaining = kCloneMaximumBatch;
  int64_t shifted = 0;
  auto& due = state->due[step + kCloneHorizon];
  for (const Candidate& candidate : candidates) {
    if (static_cast<int>(action.market.size()) >= kMaximumMarketOrders ||
        remaining <= 0) {
      break;
    }
    const int64_t quantity = std::min(candidate.quantity, remaining);
    if (quantity <= 0) continue;
    action.market.push_back(
        MarketOrder{OrderKind::kSell, candidate.product, quantity});
    due[candidate.product] += quantity;
    remaining -= quantity;
    shifted += quantity;
  }
  if (shifted == 0) {
    if (std::all_of(due.begin(), due.end(),
                    [](int64_t value) { return value == 0; })) {
      state->due.erase(step + kCloneHorizon);
    }
    return action;
  }
  ReorderSellSlots(engine, &action, 0.25);
  return action;
}

}  // namespace

Portfolio::Portfolio(const int64_t* tokens, const int64_t* quantities,
                     const int64_t* decision_counts,
                     const int64_t* unit_counts, int width,
                     int maximum_market_orders) {
  if (tokens == nullptr || quantities == nullptr || decision_counts == nullptr ||
      unit_counts == nullptr || width < 1 || maximum_market_orders < 1) {
    throw std::invalid_argument("invalid Kaito v48 portfolio buffers");
  }
  actions_.reserve(static_cast<size_t>(kRouteCount) * kRouteTurns);
  for (int route = 0; route < kRouteCount; ++route) {
    for (int step = 0; step < kRouteTurns; ++step) {
      const size_t row = static_cast<size_t>(route) * kRouteTurns + step;
      const int64_t decisions = decision_counts[row];
      const int64_t units = unit_counts[row];
      if (decisions < units || decisions > width || units < 1) {
        throw std::invalid_argument("Kaito v48 route action shape is invalid");
      }
      const size_t offset = row * width;
      actions_.push_back(policy::DecodePlayerAction(
          tokens + offset, quantities + offset, static_cast<int>(decisions),
          static_cast<int>(units), maximum_market_orders));
    }
  }
}

size_t Portfolio::index(Route route, int step) const {
  const int route_index = RouteIndex(route);
  if (route_index < 0 || route_index >= kRouteCount) {
    throw std::out_of_range("Kaito v48 route is outside the portfolio");
  }
  const int bounded = std::clamp(step, 0, kRouteTurns - 1);
  return static_cast<size_t>(route_index) * kRouteTurns + bounded;
}

const PlayerAction& Portfolio::action(Route route, int step) const {
  return actions_[index(route, step)];
}

UnitAction Portfolio::unit_action(Route route, int step, int unit_index) const {
  const PlayerAction& route_action = action(route, step);
  if (unit_index == 0) return route_action.farmer;
  const int hand = unit_index - 1;
  return hand >= 0 && hand < static_cast<int>(route_action.hands.size())
             ? route_action.hands[hand]
             : Pass();
}

std::array<int64_t, kNumProducts> Portfolio::sell_totals(Route route,
                                                         int step) const {
  return SellTotals(action(route, step));
}

struct Session::Impl {
  explicit Impl(std::shared_ptr<const Portfolio> value)
      : portfolio(std::move(value)) {
    if (!portfolio) throw std::invalid_argument("Kaito v48 portfolio is null");
  }

  std::shared_ptr<const Portfolio> portfolio;
  std::array<SeatState, 2> seats;
};

Session::Session(std::shared_ptr<const Portfolio> portfolio)
    : impl_(std::make_unique<Impl>(std::move(portfolio))) {}

Session::Session(const Session& other)
    : impl_(std::make_unique<Impl>(*other.impl_)) {}

Session::~Session() = default;
Session::Session(Session&&) noexcept = default;
Session& Session::operator=(Session&&) noexcept = default;

Route ProposedRoute(const Engine& engine, int player, Route selected) {
  if (player < 0 || player > 1) {
    throw std::invalid_argument("Kaito v48 player must be 0 or 1");
  }
  if (selected != Route::kDefault) return selected;
  Route event = RouteEvent(engine);
  if (event == Route::kDefault && BakeryCapitalCandidate(engine, player)) {
    event = Route::kBakeryCapital;
  }
  return event;
}

PlayerAction Session::Act(const Engine& engine, int player) {
  try {
    if (player < 0 || player > 1) {
      throw std::invalid_argument("Kaito v48 player must be 0 or 1");
    }
    SeatState& seat = impl_->seats[player];
    const int step = engine.step_index();
    if (step == 0 || step < seat.last_step) seat = SeatState{};
    seat.last_step = step;
    if (seat.selected == Route::kDefault) {
      const Route event = ProposedRoute(engine, player, seat.selected);
      if (event != Route::kDefault) seat.selected = event;
    }
    return ActRoute(engine, player, seat.selected);
  } catch (...) {
    PlayerAction fallback;
    AlignHands(engine, player == 1 ? 1 : 0, &fallback);
    return fallback;
  }
}

PlayerAction Session::ActRoute(const Engine& engine, int player, Route route) {
  try {
    if (player < 0 || player > 1) {
      throw std::invalid_argument("Kaito v48 player must be 0 or 1");
    }
    const int route_index = RouteIndex(route);
    if (route_index < 0 || route_index >= kRouteCount) {
      throw std::invalid_argument("Kaito v48 route is outside the portfolio");
    }
    SeatState& seat = impl_->seats[player];
    const int step = engine.step_index();
    if (step == 0 || step < seat.last_step) seat = SeatState{};
    seat.last_step = step;
    seat.selected = route;
    PlayerAction result = impl_->portfolio->action(route, step);
    result = ApplyRepair(*impl_->portfolio, engine, player, route,
                         std::move(result), &seat.repair[RouteIndex(route)]);
    result = ApplyPreemption(*impl_->portfolio, engine, player, route,
                             std::move(result), &seat.preemption);
    if (step == 718) ReplaceTerminalMarket(engine, player, &result);
    return result;
  } catch (...) {
    PlayerAction fallback;
    AlignHands(engine, player == 1 ? 1 : 0, &fallback);
    return fallback;
  }
}

}  // namespace kagg::kaito
