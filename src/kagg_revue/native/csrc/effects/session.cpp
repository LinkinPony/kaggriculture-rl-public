#include "effects/session.hpp"

#include <algorithm>
#include <stdexcept>
#include <utility>

#include "effects/internal.hpp"

namespace kagg::effects {

bool IsWork(RequestKind kind) {
  return (kind >= RequestKind::kPlant && kind <= RequestKind::kCancel) ||
         kind == RequestKind::kLoad || kind == RequestKind::kUnload;
}

bool IsMarket(RequestKind kind) {
  return (kind >= RequestKind::kBuySeed && kind <= RequestKind::kBuyLand) ||
         kind == RequestKind::kSkipMarketSlot;
}

const char* PhaseName(Phase phase) {
  switch (phase) {
    case Phase::kWork:
      return "WORK";
    case Phase::kMarket:
      return "MARKET";
    case Phase::kDone:
      return "DONE";
  }
  return "DONE";
}

const char* RequestKindName(RequestKind kind) {
  switch (kind) {
    case RequestKind::kStop:
      return "STOP";
    case RequestKind::kPlant:
      return "PLANT";
    case RequestKind::kWater:
      return "WATER";
    case RequestKind::kHarvest:
      return "HARVEST";
    case RequestKind::kFertilize:
      return "FERTILIZE";
    case RequestKind::kDig:
      return "DIG";
    case RequestKind::kBuildCoop:
      return "BUILD_COOP";
    case RequestKind::kBuildPasture:
      return "BUILD_PASTURE";
    case RequestKind::kPlaceAnimal:
      return "PLACE_ANIMAL";
    case RequestKind::kFeed:
      return "FEED";
    case RequestKind::kCare:
      return "CARE";
    case RequestKind::kCollectFertilizer:
      return "COLLECT_FERTILIZER";
    case RequestKind::kBank:
      return "BANK";
    case RequestKind::kStage:
      return "STAGE";
    case RequestKind::kCancel:
      return "CANCEL";
    case RequestKind::kBuySeed:
      return "BUY_SEED";
    case RequestKind::kBuyProduct:
      return "BUY_PRODUCT";
    case RequestKind::kBuyAnimal:
      return "BUY_ANIMAL";
    case RequestKind::kSell:
      return "SELL";
    case RequestKind::kHire:
      return "HIRE";
    case RequestKind::kBuyLand:
      return "BUY_LAND";
    case RequestKind::kLoad:
      return "LOAD";
    case RequestKind::kUnload:
      return "UNLOAD";
    case RequestKind::kSkipMarketSlot:
      return "SKIP_MARKET_SLOT";
  }
  return "STOP";
}

const char* ResourceKindName(ResourceKind kind) {
  switch (kind) {
    case ResourceKind::kNone:
      return "NONE";
    case ResourceKind::kSeed:
      return "SEED";
    case ResourceKind::kItem:
      return "ITEM";
    case ResourceKind::kShedRoom:
      return "SHED_ROOM";
  }
  return "NONE";
}

std::vector<std::string> CandidateFeatureNames() {
  return {"completion_steps", "needs_shed",       "required_quantity",
          "resource_available", "episode_slack", "day_slack",
          "target_x",           "target_y",       "target_kind",
          "target_state",       "inventory_load", "prefix_fill"};
}

Session::Session(Config config, int unit_limit, int maximum_quantity,
                 bool task_conditioning, bool destination_tasks)
    : config_(std::move(config)),
      unit_limit_(unit_limit),
      maximum_quantity_(maximum_quantity),
      task_conditioning_(task_conditioning),
      destination_tasks_(destination_tasks) {
  if (config_.board_size < 1 || config_.episode_steps < 2 ||
      unit_limit_ < 1 || maximum_quantity_ < 1) {
    throw std::invalid_argument("effect policy dimensions must be positive");
  }
  config_.turns_per_day = std::max(1, config_.turns_per_day);
  config_.max_market_orders = std::max(1, config_.max_market_orders);
}

void Session::Reset() {
  jobs_.clear();
  next_job_id_ = 1;
  phase_ = Phase::kWork;
  turn_step_ = -1;
  player_ = -1;
  work_limit_ = 1;
  idle_units_ = 0;
  selected_new_jobs_ = 0;
  candidates_.clear();
  candidate_mask_.clear();
  selected_work_.clear();
  turn_work_.clear();
  turn_market_.clear();
  previous_action_.clear();
  compiled_ready_ = false;
  compiled_action_ = {};
  projected_farm_ = {};
  projected_priv_ = {};
  projected_market_ = {};
  last_action_step_ = -1;
  cached_action_ = {};
}

void Session::Reconcile(const Engine& engine, int player) {
  const Farm& farm = engine.farm(player);
  const PrivateState& priv = engine.priv(player);
  const int day = engine.step_index() / config_.turns_per_day;
  jobs_.erase(
      std::remove_if(jobs_.begin(), jobs_.end(), [&](const Job& job) {
        if (job.unit < 0 ||
            job.unit >= static_cast<int>(priv.inventories.size())) {
          return true;
        }
        if (job.kind == RequestKind::kStage) {
          const auto [x, y] = internal::UnitPosition(farm, job.unit);
          const auto [target_x, target_y] =
              internal::TargetPosition(job.target, config_.board_size);
          return x == target_x && y == target_y;
        }
        if (job.kind == RequestKind::kBank) {
          return priv.inventories[job.unit].items.empty();
        }
        if (job.kind == RequestKind::kLoad) {
          return job.item < 0 || job.item >= kNumItems || job.quantity <= 0;
        }
        if (job.kind == RequestKind::kUnload) {
          return job.item < 0 || job.item >= kNumItems || job.quantity <= 0 ||
                 priv.inventories[job.unit].Get(job.item) < job.quantity;
        }
        return !internal::TargetSupports(farm, day, job.kind, job.target,
                                         job.item);
      }),
      jobs_.end());
}

void Session::BeginTurn(const Engine& engine, int player) {
  if (player < 0 || player > 1) {
    throw std::invalid_argument("effect policy player must be 0 or 1");
  }
  if (engine.config().board_size != config_.board_size ||
      engine.config().episode_steps != config_.episode_steps ||
      engine.config().turns_per_day != config_.turns_per_day ||
      engine.config().max_market_orders != config_.max_market_orders ||
      engine.config().shed_capacity != config_.shed_capacity) {
    throw std::invalid_argument(
        "effect session and engine configurations differ");
  }
  const int step = engine.step_index();
  if ((turn_step_ >= 0 && step < turn_step_) ||
      (player_ >= 0 && player != player_)) {
    Reset();
  }
  if (step == turn_step_ && player == player_) return;

  if (turn_step_ >= 0) {
    previous_action_ = turn_work_;
    previous_action_.insert(previous_action_.end(), turn_market_.begin(),
                            turn_market_.end());
  }
  Reconcile(engine, player);
  phase_ = Phase::kWork;
  turn_step_ = step;
  player_ = player;
  selected_new_jobs_ = 0;
  selected_work_.clear();
  turn_work_.clear();
  turn_market_.clear();
  candidates_.clear();
  candidate_mask_.clear();
  compiled_ready_ = false;
  compiled_action_ = {};
  last_action_step_ = -1;
  cached_action_ = {};

  const int unit_count = static_cast<int>(engine.priv(player).inventories.size());
  std::vector<uint8_t> busy(static_cast<std::size_t>(unit_count), 0);
  for (const Job& job : jobs_) {
    if (job.unit >= 0 && job.unit < unit_count) busy[job.unit] = 1;
  }
  idle_units_ = static_cast<int>(
      std::count(busy.begin(), busy.end(), static_cast<uint8_t>(0)));
  // With no idle unit, one cancellation decision remains available.  A
  // cancellation never silently creates a replacement request in this turn.
  work_limit_ = std::max(1, idle_units_);
  GenerateWorkCandidates(engine, player);
  RefreshWorkMask(engine, player);
}

std::array<int64_t, kJobFieldCount> Session::EncodeJob(
    const Engine& engine, int player, const Job& job) const {
  const Farm& farm = engine.farm(player);
  const PrivateState& priv = engine.priv(player);
  const auto [x, y] = internal::UnitPosition(farm, job.unit);
  int completion = 0;
  if (job.kind == RequestKind::kStage) {
    const auto target = internal::TargetPosition(job.target, config_.board_size);
    completion = internal::Distance(x, y, target.first, target.second);
  } else if (job.kind == RequestKind::kBank ||
             job.kind == RequestKind::kLoad ||
             job.kind == RequestKind::kUnload) {
    const auto shed = internal::NearestShed(x, y, config_.board_size);
    completion = internal::Distance(x, y, shed.first, shed.second) + 1;
  } else {
    const auto target = internal::TargetPosition(job.target, config_.board_size);
    const int required = internal::RequiredItem(job.kind, job.item);
    if (required >= 0 && priv.inventories[job.unit].Get(required) <= 0) {
      const auto shed = internal::BestShedForRoute(
          x, y, target.first, target.second, config_.board_size);
      completion = internal::Distance(x, y, shed.first, shed.second) + 1 +
                   internal::Distance(shed.first, shed.second, target.first,
                                      target.second) +
                   1;
    } else {
      completion =
          internal::Distance(x, y, target.first, target.second) + 1;
    }
  }
  return {static_cast<int64_t>(job.id), static_cast<int64_t>(job.kind),
          job.target, job.item + 1, job.unit + 1, job.created_step,
          completion, job.quantity};
}

Observation Session::Observe(const Engine& engine, int player) {
  BeginTurn(engine, player);
  Observation result;
  result.phase = phase_;
  result.candidates = candidates_;
  result.candidate_mask = candidate_mask_;
  result.work_limit = work_limit_;
  result.jobs.reserve(jobs_.size());
  for (const Job& job : jobs_) result.jobs.push_back(EncodeJob(engine, player, job));
  result.work_prefix.reserve(turn_work_.size());
  for (const SemanticAction& action : turn_work_) {
    result.work_prefix.push_back(internal::EncodeAction(action));
  }
  result.market_prefix.reserve(turn_market_.size());
  for (const SemanticAction& action : turn_market_) {
    result.market_prefix.push_back(internal::EncodeAction(action));
  }
  result.previous_action.reserve(previous_action_.size());
  for (const SemanticAction& action : previous_action_) {
    result.previous_action.push_back(internal::EncodeAction(action));
  }
  return result;
}

Phase Session::Select(const Engine& engine, int player, int candidate_index) {
  BeginTurn(engine, player);
  if (phase_ == Phase::kDone) {
    throw std::logic_error("effect turn is already committed");
  }
  if (candidate_index < 0 ||
      candidate_index >= static_cast<int>(candidates_.size()) ||
      !candidate_mask_[candidate_index]) {
    throw std::out_of_range("effect candidate is unavailable");
  }
  const Candidate candidate = candidates_[candidate_index];
  if (phase_ == Phase::kWork) {
    if (candidate.kind == RequestKind::kStop) {
      FinalizeWork(engine, player);
      return phase_;
    }
    if (!IsWork(candidate.kind)) {
      throw std::logic_error("market request appeared in the work phase");
    }
    selected_work_.push_back(candidate_index);
    SemanticAction action{
        .kind = candidate.kind,
        .target = static_cast<int>(candidate.fields[1]),
        .item = static_cast<int>(candidate.fields[2]) - 1,
        .quantity = candidate.fields[3],
        .job_id = static_cast<uint64_t>(candidate.fields[4]),
        .unit = static_cast<int>(candidate.fields[5]) - 1,
    };
    turn_work_.push_back(action);
    if (candidate.kind != RequestKind::kCancel) ++selected_new_jobs_;
    if (static_cast<int>(selected_work_.size()) >= work_limit_) {
      FinalizeWork(engine, player);
    } else {
      RefreshWorkMask(engine, player);
    }
    return phase_;
  }

  if (candidate.kind == RequestKind::kStop) {
    phase_ = Phase::kDone;
    candidates_.clear();
    candidate_mask_.clear();
    return phase_;
  }
  if (!IsMarket(candidate.kind)) {
    throw std::logic_error("work request appeared in the market phase");
  }
  if (candidate.kind == RequestKind::kSkipMarketSlot) {
    compiled_action_.market.push_back(std::nullopt);
    turn_market_.push_back(SemanticAction{
        .kind = candidate.kind,
        .target = -1,
        .item = -1,
        .quantity = 0,
        .job_id = 0,
        .unit = -1,
    });
    if (static_cast<int>(turn_market_.size()) >= config_.max_market_orders) {
      phase_ = Phase::kDone;
      candidates_.clear();
      candidate_mask_.clear();
    } else {
      GenerateMarketCandidates(engine, player);
    }
    return phase_;
  }
  const int semantic_item = static_cast<int>(candidate.fields[2]) - 1;
  const int64_t quantity = candidate.fields[3];
  OrderKind order_kind = OrderKind::kHire;
  int order_item = semantic_item;
  switch (candidate.kind) {
    case RequestKind::kBuySeed:
      order_kind = OrderKind::kBuySeed;
      break;
    case RequestKind::kBuyProduct:
      order_kind = OrderKind::kBuyProduct;
      break;
    case RequestKind::kBuyAnimal:
      order_kind = OrderKind::kBuyAnimal;
      order_item -= item::kGoose;
      break;
    case RequestKind::kSell:
      order_kind = OrderKind::kSell;
      break;
    case RequestKind::kHire:
      order_kind = OrderKind::kHire;
      order_item = 0;
      break;
    case RequestKind::kBuyLand:
      order_kind = OrderKind::kBuyLand;
      order_item = 0;
      break;
    default:
      throw std::logic_error("invalid market effect request");
  }
  MarketOrder order{order_kind, order_item, quantity};
  compiled_action_.market.push_back(order);
  turn_market_.push_back(SemanticAction{
      .kind = candidate.kind,
      .target = -1,
      .item = semantic_item,
      .quantity = quantity,
      .job_id = 0,
      .unit = -1,
  });
  ProjectMarketOrder(order);
  if (static_cast<int>(turn_market_.size()) >= config_.max_market_orders) {
    phase_ = Phase::kDone;
    candidates_.clear();
    candidate_mask_.clear();
  } else {
    GenerateMarketCandidates(engine, player);
  }
  return phase_;
}

void Session::ProjectMarketOrder(const MarketOrder& order) {
  PlayerAction own;
  own.market.push_back(order);
  PlayerAction empty;
  Farm dummy_farm;
  dummy_farm.tiles.assign(projected_farm_.tiles.size(), Tile{});
  PrivateState dummy_priv;
  dummy_priv.inventories.emplace_back();
  std::array<Farm*, 2> farms = {&projected_farm_, &dummy_farm};
  std::array<PrivateState*, 2> privates = {&projected_priv_, &dummy_priv};
  ApplyMarketPhase(config_, farms, privates, &projected_market_, own, empty,
                   nullptr);
}

int64_t Session::MarketQuantityUpper(OrderKind kind, int item_index) const {
  const int64_t limit = maximum_quantity_;
  if (kind == OrderKind::kSell) {
    return item_index >= 0 && item_index < kNumProducts
               ? std::min(limit, projected_priv_.shed[item_index])
               : 0;
  }
  if (kind == OrderKind::kBuySeed) {
    if (item_index < 0 || item_index >= kNumCrops) return 0;
    return std::min<int64_t>(
        limit, static_cast<int64_t>(projected_farm_.money) /
                   std::max<int64_t>(1, kCrops[item_index].seed_cost));
  }
  const int64_t room =
      std::max<int64_t>(0, config_.shed_capacity - ShedTotal(projected_priv_));
  if (kind == OrderKind::kBuyAnimal) {
    if (item_index < 0 || item_index >= kNumAnimals) return 0;
    return std::min(
        {limit, room,
         static_cast<int64_t>(projected_farm_.money) /
             std::max<int64_t>(1, kAnimals[item_index].cost)});
  }
  if (kind != OrderKind::kBuyProduct || item_index < 0 ||
      item_index >= kNumProducts ||
      (item_index != item::kWheat && item_index != item::kFertilizer)) {
    return 0;
  }
  double money = projected_farm_.money;
  int64_t inventory = projected_market_.inventory[item_index];
  int64_t result = 0;
  while (result < std::min(limit, room)) {
    const int64_t price =
        ComputeMarketPrice(config_, item_index, inventory - 1);
    if (money < static_cast<double>(price)) break;
    money -= static_cast<double>(price);
    --inventory;
    ++result;
  }
  return result;
}

PlayerAction Session::CompileAction(const Engine& engine, int player) {
  if (phase_ != Phase::kDone || !compiled_ready_) {
    throw std::logic_error("effect action requested before STOP");
  }
  if (last_action_step_ == engine.step_index()) return cached_action_;
  if (player != player_ || engine.step_index() != turn_step_) {
    throw std::logic_error("effect action no longer matches its turn");
  }
  cached_action_ = compiled_action_;
  last_action_step_ = engine.step_index();
  return cached_action_;
}

PlayerAction Session::Action(const Engine& engine, int player) {
  BeginTurn(engine, player);
  return CompileAction(engine, player);
}

NumericAction Session::ActionNumeric(const Engine& engine, int player) {
  const PlayerAction action = Action(engine, player);
  NumericAction result;
  result.unit_count = 1 + engine.farm(player).hands.size();
  const int capacity = static_cast<int>(result.unit_count) +
                       static_cast<int>(action.market.size());
  result.tokens.resize(static_cast<std::size_t>(capacity));
  result.quantities.resize(static_cast<std::size_t>(capacity));
  result.decision_count = policy::EncodePlayerAction(
      action, static_cast<int>(result.unit_count), result.tokens.data(),
      result.quantities.data(), capacity);
  return result;
}

bool Session::DecisionRequired(const Engine& engine, int player) {
  BeginTurn(engine, player);
  return phase_ != Phase::kDone;
}

}  // namespace kagg::effects
