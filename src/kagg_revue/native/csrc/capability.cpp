#include "capability_internal.hpp"

#include <algorithm>
#include <limits>
#include <numeric>
#include <stdexcept>
#include <utility>

namespace kagg::capability {
namespace {

int UnitToken(const UnitAction& action) {
  switch (action.op) {
    case UnitOp::kNorth: return 1;
    case UnitOp::kSouth: return 2;
    case UnitOp::kEast: return 3;
    case UnitOp::kWest: return 4;
    case UnitOp::kPickup:
      return action.arg >= 0 && action.arg < kNumItems ? 5 + action.arg : 0;
    case UnitOp::kDrop: return 17;
    case UnitOp::kPlace:
      return action.arg >= 0 && action.arg < kNumItems ? 18 + action.arg : 0;
    case UnitOp::kPlant:
      return action.arg >= 0 && action.arg < kNumCrops ? 30 + action.arg : 0;
    case UnitOp::kWater: return 35;
    case UnitOp::kHarvest: return 36;
    case UnitOp::kFertilize: return 37;
    case UnitOp::kDig: return 38;
    case UnitOp::kBuildCoop: return 39;
    case UnitOp::kBuildPasture: return 40;
    case UnitOp::kFeed: return 41;
    case UnitOp::kCollectFertilizer: return 42;
    case UnitOp::kCare: return 43;
    case UnitOp::kPass:
    case UnitOp::kInvalid: return 0;
  }
  return 0;
}

int MarketToken(const std::optional<MarketOrder>& order) {
  if (!order) return policy::kUnitActionTokens + 1;
  switch (order->kind) {
    case OrderKind::kSell:
      return order->item >= 0 && order->item < kNumProducts
                 ? policy::kUnitActionTokens + 2 + order->item
                 : policy::kUnitActionTokens + 1;
    case OrderKind::kBuySeed:
      return order->item >= 0 && order->item < kNumCrops
                 ? policy::kUnitActionTokens + 11 + order->item
                 : policy::kUnitActionTokens + 1;
    case OrderKind::kBuyProduct:
      if (order->item == item::kWheat) return policy::kUnitActionTokens + 16;
      if (order->item == item::kFertilizer) return policy::kUnitActionTokens + 17;
      return policy::kUnitActionTokens + 1;
    case OrderKind::kBuyAnimal:
      return order->item >= 0 && order->item < kNumAnimals
                 ? policy::kUnitActionTokens + 18 + order->item
                 : policy::kUnitActionTokens + 1;
    case OrderKind::kHire: return policy::kUnitActionTokens + 21;
    case OrderKind::kBuyLand: return policy::kUnitActionTokens + 22;
  }
  return policy::kUnitActionTokens + 1;
}

NumericAction EncodeAction(const PlayerAction& action, int unit_count,
                           bool requires_direct) {
  NumericAction out;
  out.requires_direct = requires_direct;
  out.unit_count = std::max(1, unit_count);
  out.tokens.reserve(static_cast<size_t>(out.unit_count) + action.market.size());
  out.quantities.reserve(out.tokens.capacity());
  const auto append_unit = [&](const UnitAction& unit, NumericAction* result) {
    result->tokens.push_back(UnitToken(unit));
    result->quantities.push_back(
        policy::TokenHasQuantity(result->tokens.back()) ? unit.n : 0);
  };
  append_unit(action.farmer, &out);
  for (int index = 1; index < out.unit_count; ++index) {
    const UnitAction unit = index - 1 < static_cast<int>(action.hands.size())
                                ? action.hands[index - 1]
                                : UnitAction{UnitOp::kPass, -1, 1};
    append_unit(unit, &out);
  }
  for (const std::optional<MarketOrder>& order : action.market) {
    const int token = MarketToken(order);
    out.tokens.push_back(token);
    out.quantities.push_back(order && policy::TokenHasQuantity(token)
                                 ? order->remaining
                                 : 0);
  }
  out.decision_count = static_cast<int64_t>(out.tokens.size());
  return out;
}

}  // namespace

Session::Session(Config config, int max_candidates, int max_edits)
    : config_(std::move(config)), max_candidates_(max_candidates),
      max_edits_(max_edits) {
  if (max_candidates_ < 1) {
    throw std::invalid_argument("max_candidates must be positive");
  }
  if (max_edits_ < 1) {
    throw std::invalid_argument("max_edits must be positive");
  }
  candidates_.reserve(static_cast<size_t>(max_candidates_));
}

Session::~Session() = default;
Session::Session(Session&&) noexcept = default;
Session& Session::operator=(Session&&) noexcept = default;

void Session::Reset() {
  ledger_ = GoalLedger{};
  proposal_base_ = GoalLedger{};
  candidates_.clear();
  planner_.reset();
  selected_mode_ = Mode::kDirectTurn;
  selected_canonical_id_ = 0;
  selected_day_ = -1;
  generated_step_ = -1;
  generated_player_ = -1;
  last_seen_step_ = -1;
  player_ = -1;
}

void Session::ObserveEpisode(const Engine& engine, int player) {
  if (player < 0 || player > 1) {
    throw std::invalid_argument("capability player must be 0 or 1");
  }
  if (engine.config().board_size != config_.board_size ||
      engine.config().episode_steps != config_.episode_steps ||
      engine.config().turns_per_day != config_.turns_per_day) {
    throw std::invalid_argument(
        "capability session and engine configurations differ");
  }
  const int step = engine.step_index();
  if ((last_seen_step_ >= 0 && step < last_seen_step_) ||
      (player_ >= 0 && player != player_)) {
    Reset();
  }
  last_seen_step_ = step;
  player_ = player;
}

GoalLedger Session::LedgerFromState(const Engine& engine, int player) const {
  const internal::StateSummary state = internal::Summarize(engine, player);
  GoalLedger ledger;
  ledger.workers.lower = state.farm.workers;
  ledger.land.lower = state.farm.quadrants;
  for (int crop = 0; crop < kNumCrops; ++crop) {
    ledger.crops[crop].lower = state.farm.crop_counts[crop];
  }
  for (int animal = 0; animal < kNumAnimals; ++animal) {
    ledger.animals[animal].lower = state.farm.animal_counts[animal];
  }
  for (int product = 0; product < kNumProducts; ++product) {
    ledger.products[product].lower = static_cast<int>(std::min<int64_t>(
        state.owned_items[product], std::numeric_limits<int>::max()));
  }
  return ledger;
}

Mode Session::Select(int candidate_index) {
  if (generated_step_ < 0 || generated_player_ < 0) {
    throw std::logic_error("capability select requires a generated candidate set");
  }
  if (candidate_index < 0 ||
      candidate_index >= static_cast<int>(candidates_.size()) ||
      !candidates_[candidate_index].valid) {
    throw std::out_of_range("capability candidate index is invalid");
  }
  const Candidate& candidate = candidates_[candidate_index];
  selected_mode_ = candidate.mode;
  selected_canonical_id_ = candidate.canonical_id;
  selected_day_ = generated_step_ / std::max(1, config_.turns_per_day);
  switch (candidate.mode) {
    case Mode::kPatch:
      ledger_ = candidate.projected;
      RebuildPlanner();
      break;
    case Mode::kCancel:
      ledger_ = GoalLedger{};
      planner_.reset();
      break;
    case Mode::kContinue:
      if (!ledger_.active) {
        throw std::logic_error("cannot continue an inactive capability");
      }
      break;
    case Mode::kDirectTurn: break;
  }
  return selected_mode_;
}

planner::PlannerOptions Session::PlannerOptionsFromLedger() const {
  planner::PlannerOptions options;
  options.strategy.explicit_control = true;
  options.strategy.enforce_production_targets = true;
  options.strategy.target_workers = std::max(1, ledger_.workers.lower);
  options.strategy.target_land_quadrants = std::clamp(ledger_.land.lower, 1, 4);
  options.strategy.allow_land = true;
  options.strategy.allow_crop_investment = true;
  options.strategy.allow_animal_investment = true;
  options.strategy.has_crop_targets = true;
  options.strategy.has_animal_targets = true;
  options.strategy.target_plants = 0;
  for (int crop = 0; crop < kNumCrops; ++crop) {
    options.strategy.target_crops[crop] = std::max(0, ledger_.crops[crop].lower);
    options.strategy.target_plants += options.strategy.target_crops[crop];
  }
  options.strategy.preferred_crop = static_cast<int>(std::distance(
      options.strategy.target_crops.begin(),
      std::max_element(options.strategy.target_crops.begin(),
                       options.strategy.target_crops.end())));
  for (int animal = 0; animal < kNumAnimals; ++animal) {
    options.strategy.target_animals[animal] =
        std::max(0, ledger_.animals[animal].lower);
  }
  options.strategy.preferred_animal = static_cast<int>(std::distance(
      options.strategy.target_animals.begin(),
      std::max_element(options.strategy.target_animals.begin(),
                       options.strategy.target_animals.end())));
  if (std::accumulate(options.strategy.target_animals.begin(),
                      options.strategy.target_animals.end(), 0) == 0) {
    options.strategy.preferred_animal = -1;
  }
  for (int product = 0; product < kNumProducts; ++product) {
    options.strategy.product_reserves[product] =
        std::max(0, ledger_.products[product].lower);
    options.strategy.minimum_sale_prices[product] =
        std::max(0.0F, ledger_.products[product].price_guard);
  }
  options.strategy.replenish_product_reserves = true;
  options.strategy.sale_mode = planner::SaleMode::kAggressive;
  options.scheduler = planner::SchedulerKind::kRouteAware;
  options.supply_route_mode = planner::SupplyRouteMode::kTaskBound;
  options.task_continuation_mode = planner::TaskContinuationMode::kRegret;
  return options;
}

void Session::RebuildPlanner() {
  planner_ = std::make_unique<planner::NativePlanner>(
      config_, PlannerOptionsFromLedger());
}

NumericAction Session::Action(const Engine& engine, int player) {
  ObserveEpisode(engine, player);
  const int unit_count = 1 + static_cast<int>(engine.farm(player).hands.size());
  if (!ledger_.active || selected_mode_ == Mode::kDirectTurn ||
      selected_mode_ == Mode::kCancel) {
    PlayerAction pass;
    pass.farmer = UnitAction{UnitOp::kPass, -1, 1};
    pass.hands.assign(static_cast<size_t>(std::max(0, unit_count - 1)),
                      UnitAction{UnitOp::kPass, -1, 1});
    return EncodeAction(pass, unit_count, true);
  }
  if (!planner_) RebuildPlanner();
  const planner::PlanResult plan = planner_->Plan(
      engine.farm(player), engine.farm(1 - player), engine.priv(player),
      engine.market(), player, engine.step_index());
  return EncodeAction(plan.action, unit_count, false);
}

bool Session::DecisionRequired(const Engine& engine, int player) {
  ObserveEpisode(engine, player);
  if (selected_day_ < 0) return true;
  const int day = engine.step_index() / std::max(1, config_.turns_per_day);
  return day != selected_day_;
}

const char* ModeName(Mode mode) {
  switch (mode) {
    case Mode::kDirectTurn: return "direct_turn";
    case Mode::kContinue: return "continue";
    case Mode::kCancel: return "cancel";
    case Mode::kPatch: return "patch";
  }
  return "direct_turn";
}

const char* EditTypeName(EditType type) {
  switch (type) {
    case EditType::kNone: return "none";
    case EditType::kEnsure: return "ensure";
    case EditType::kReduce: return "reduce";
    case EditType::kTrade: return "trade";
  }
  return "none";
}

const char* ObjectKindName(ObjectKind kind) {
  switch (kind) {
    case ObjectKind::kNone: return "none";
    case ObjectKind::kWorker: return "worker";
    case ObjectKind::kLand: return "land";
    case ObjectKind::kCrop: return "crop";
    case ObjectKind::kAnimal: return "animal";
    case ObjectKind::kProduct: return "product";
  }
  return "none";
}

}  // namespace kagg::capability
