#include "programs/session.hpp"

#include <algorithm>
#include <stdexcept>

#include "action_codec.hpp"
#include "unit_phase.hpp"

namespace kagg::programs {
namespace {

bool InRange(int64_t value, int size) {
  return value >= 0 && value < size;
}

bool TaskNeedsTarget(Task task) {
  return task != Task::kWait;
}

bool TaskNeedsArgument(Task task) {
  return task == Task::kSafePlant || task == Task::kBuild ||
         task == Task::kDeployAnimal || task == Task::kFetch ||
         task == Task::kStore || task == Task::kPlant;
}

bool TaskNeedsQuantity(Task task) {
  return task == Task::kFetch || task == Task::kStore;
}

bool RawNeedsArgument(RawOperation operation) {
  return operation == RawOperation::kPickup ||
         operation == RawOperation::kPlace ||
         operation == RawOperation::kPlant;
}

bool RawNeedsQuantity(RawOperation operation) {
  return operation == RawOperation::kPickup ||
         operation == RawOperation::kPlace;
}

bool MarketNeedsItem(MarketOrderType order) {
  return order == MarketOrderType::kSell ||
         order == MarketOrderType::kBuySeed ||
         order == MarketOrderType::kBuyProduct ||
         order == MarketOrderType::kBuyAnimal;
}

bool SameUnitAction(const UnitAction& left, const UnitAction& right) {
  return left.op == right.op && left.arg == right.arg && left.n == right.n;
}

size_t TaskArgumentIndex(Task task, int argument) {
  return static_cast<size_t>(task) * kArgumentCount + argument;
}

size_t TaskTargetIndex(Task task, int argument, int target, int tiles) {
  return (static_cast<size_t>(task) * kArgumentCount + argument) * tiles +
         target;
}

size_t TaskQuantityModeIndex(Task task, int argument, QuantityMode mode) {
  return (static_cast<size_t>(task) * kArgumentCount + argument) *
             kQuantityModeCount +
         static_cast<int>(mode);
}

size_t TaskQuantityIndex(Task task, int argument) {
  return static_cast<size_t>(task) * kArgumentCount + argument;
}

size_t RawArgumentIndex(RawOperation operation, int argument) {
  return static_cast<size_t>(operation) * kArgumentCount + argument;
}

size_t RawQuantityModeIndex(RawOperation operation, int argument,
                            QuantityMode mode) {
  return (static_cast<size_t>(operation) * kArgumentCount + argument) *
             kQuantityModeCount +
         static_cast<int>(mode);
}

size_t RawQuantityIndex(RawOperation operation, int argument) {
  return static_cast<size_t>(operation) * kArgumentCount + argument;
}

size_t MarketItemIndex(MarketOrderType order, int item) {
  return static_cast<size_t>(order) * kNumItems + item;
}

size_t MarketQuantityModeIndex(MarketOrderType order, int item,
                               QuantityMode mode) {
  return (static_cast<size_t>(order) * kNumItems + item) *
             kQuantityModeCount +
         static_cast<int>(mode);
}

size_t MarketQuantityIndex(MarketOrderType order, int item) {
  return static_cast<size_t>(order) * kNumItems + item;
}

}  // namespace

Session::Session(Config config, int unit_limit)
    : config_(std::move(config)), unit_limit_(unit_limit) {
  if (unit_limit_ < 1) {
    throw std::invalid_argument("conditional program unit limit must be positive");
  }
  if (config_.board_size < 2 || config_.max_market_orders < 1 ||
      config_.turns_per_day < 1) {
    throw std::invalid_argument("conditional program environment is invalid");
  }
}

void Session::Reset() {
  options_.clear();
  forced_water_targets_.clear();
  forced_water_owners_.clear();
  shadow_farm_ = Farm{};
  shadow_priv_ = PrivateState{};
  shadow_market_ = MarketState{};
  action_ = PlayerAction{};
  phase_ = Phase::kDone;
  player_ = -1;
  step_ = -1;
  day_ = -1;
  unit_count_ = 0;
  unit_index_ = 0;
  market_slot_ = 0;
}

void Session::Refresh(const Farm& farm, const PrivateState& priv,
                      const MarketState& market, int step, int player) {
  if (player < 0 || player > 1) {
    throw std::invalid_argument("conditional program player must be 0 or 1");
  }
  if ((player_ >= 0 && player_ != player) ||
      (step_ >= 0 && step != step_ && step != step_ + 1)) {
    Reset();
  }
  if (step_ == step) return;

  const int count = 1 + static_cast<int>(farm.hands.size());
  if (count > unit_limit_) {
    throw std::runtime_error(
        "conditional program unit capacity is below the visible unit count");
  }
  const int day = step / config_.turns_per_day;
  if (options_.empty()) options_.resize(1);
  if (day_ >= 0 && day != day_) {
    options_.resize(1);
  }
  options_.resize(static_cast<size_t>(count));
  shadow_farm_ = farm;
  shadow_priv_ = priv;
  shadow_market_ = market;
  while (shadow_priv_.inventories.size() < static_cast<size_t>(count)) {
    shadow_priv_.inventories.emplace_back();
  }
  action_ = PlayerAction{};
  action_.farmer = UnitAction{UnitOp::kPass, -1, 1};
  action_.hands.assign(static_cast<size_t>(count - 1),
                       UnitAction{UnitOp::kPass, -1, 1});
  forced_water_targets_.assign(static_cast<size_t>(count), -1);
  forced_water_owners_.assign(static_cast<size_t>(count), -1);
  phase_ = Phase::kUnit;
  player_ = player;
  step_ = step;
  day_ = day;
  unit_count_ = count;
  unit_index_ = 0;
  market_slot_ = 0;
}

bool Session::DecisionRequired(const Engine& engine, int player) {
  Refresh(engine.farm(player), engine.priv(player), engine.market(),
          engine.step_index(), player);
  return phase_ != Phase::kDone;
}

Decision Session::Observe(const Engine& engine, int player) {
  Refresh(engine.farm(player), engine.priv(player), engine.market(),
          engine.step_index(), player);
  if (phase_ == Phase::kDone) {
    throw std::logic_error("conditional program has no pending decision");
  }
  return BuildDecision();
}

void Session::Select(const Engine& engine, int player,
                     const Selection& selection) {
  Refresh(engine.farm(player), engine.priv(player), engine.market(),
          engine.step_index(), player);
  SelectCurrent(selection);
}

void Session::SelectCurrent(const Selection& selection) {
  if (phase_ == Phase::kDone) {
    throw std::logic_error("conditional program selection is already complete");
  }
  const Decision masks = BuildDecision();
  if (phase_ == Phase::kUnit) {
    if (!InRange(selection.control, kControlCount) ||
        !masks.control_mask[selection.control]) {
      throw std::invalid_argument("conditional program control is masked");
    }
    const Control control = static_cast<Control>(selection.control);
    if (control == Control::kAssign) {
      if (!InRange(selection.task, kTaskCount) ||
          !masks.task_mask[selection.task]) {
        throw std::invalid_argument("conditional program task is masked");
      }
      const Task task = static_cast<Task>(selection.task);
      if (TaskNeedsArgument(task) &&
          (!InRange(selection.argument, kArgumentCount) ||
           !masks.task_argument_mask[
               TaskArgumentIndex(task, static_cast<int>(selection.argument))])) {
        throw std::invalid_argument("conditional program task argument is masked");
      }
      const int tiles = config_.board_size * config_.board_size;
      if (TaskNeedsTarget(task) &&
          (!InRange(selection.target, tiles) ||
           !masks.task_target_mask[
               TaskTargetIndex(
                   task,
                   TaskNeedsArgument(task) ? static_cast<int>(selection.argument)
                                           : kNoneArgument,
                   static_cast<int>(selection.target), tiles)])) {
        throw std::invalid_argument("conditional program task target is masked");
      }
      if (TaskNeedsQuantity(task) &&
          (!InRange(selection.quantity_mode, kQuantityModeCount) ||
           !masks.task_quantity_mode_mask[TaskQuantityModeIndex(
               task, static_cast<int>(selection.argument),
               static_cast<QuantityMode>(selection.quantity_mode))])) {
        throw std::invalid_argument("conditional program task quantity mode is masked");
      }
      if (TaskNeedsQuantity(task) &&
          selection.quantity_mode == static_cast<int>(QuantityMode::kExact)) {
        const int64_t maximum = masks.task_quantity_max[TaskQuantityIndex(
            task, static_cast<int>(selection.argument))];
        if (selection.exact_quantity < 1 ||
            selection.exact_quantity > maximum) {
          throw std::invalid_argument(
              "conditional program task exact quantity is outside its mask");
        }
      }
    } else if (control == Control::kStep) {
      if (!InRange(selection.direction, kDirectionCount) ||
          !masks.direction_mask[selection.direction]) {
        throw std::invalid_argument("conditional program direction is masked");
      }
    } else if (control == Control::kRawLocal) {
      if (!InRange(selection.raw_operation, kRawOperationCount) ||
          !masks.raw_operation_mask[selection.raw_operation]) {
        throw std::invalid_argument("conditional program raw operation is masked");
      }
      const RawOperation operation =
          static_cast<RawOperation>(selection.raw_operation);
      if (RawNeedsArgument(operation) &&
          (!InRange(selection.argument, kArgumentCount) ||
           !masks.raw_argument_mask[RawArgumentIndex(
               operation, static_cast<int>(selection.argument))])) {
        throw std::invalid_argument("conditional program raw argument is masked");
      }
      if (RawNeedsQuantity(operation) &&
          (!InRange(selection.quantity_mode, kQuantityModeCount) ||
           !masks.raw_quantity_mode_mask[RawQuantityModeIndex(
               operation, static_cast<int>(selection.argument),
               static_cast<QuantityMode>(selection.quantity_mode))])) {
        throw std::invalid_argument("conditional program raw quantity mode is masked");
      }
      if (RawNeedsQuantity(operation) &&
          selection.quantity_mode == static_cast<int>(QuantityMode::kExact)) {
        const int64_t maximum = masks.raw_quantity_max[RawQuantityIndex(
            operation, static_cast<int>(selection.argument))];
        if (selection.exact_quantity < 1 ||
            selection.exact_quantity > maximum) {
          throw std::invalid_argument(
              "conditional program raw exact quantity is outside its mask");
        }
      }
    }
    SelectUnit(selection);
    return;
  }

  if (!InRange(selection.task, kMarketOrderCount) ||
      !masks.market_order_mask[selection.task]) {
    throw std::invalid_argument("conditional program market order is masked");
  }
  const MarketOrderType order = static_cast<MarketOrderType>(selection.task);
  if (MarketNeedsItem(order) &&
      (!InRange(selection.argument, kNumItems) ||
       !masks.market_item_mask[
           MarketItemIndex(order, static_cast<int>(selection.argument))])) {
    throw std::invalid_argument("conditional program market item is masked");
  }
  if (MarketNeedsItem(order) &&
      (!InRange(selection.quantity_mode, kQuantityModeCount) ||
       !masks.market_quantity_mode_mask[MarketQuantityModeIndex(
           order, static_cast<int>(selection.argument),
           static_cast<QuantityMode>(selection.quantity_mode))])) {
    throw std::invalid_argument("conditional program market quantity mode is masked");
  }
  if (MarketNeedsItem(order) &&
      selection.quantity_mode == static_cast<int>(QuantityMode::kExact)) {
    const int64_t maximum = masks.market_quantity_max[MarketQuantityIndex(
        order, static_cast<int>(selection.argument))];
    if (selection.exact_quantity < 1 ||
        selection.exact_quantity > maximum) {
      throw std::invalid_argument(
          "conditional program market exact quantity is outside its mask");
    }
  }
  SelectMarket(selection);
}

void Session::AdvanceUnit() {
  ++unit_index_;
  if (unit_index_ >= unit_count_) {
    phase_ = Phase::kMarket;
    market_slot_ = 0;
  }
}

void Session::SelectUnit(const Selection& selection) {
  const int unit = unit_index_;
  bool completed = false;
  UnitAction action{UnitOp::kPass, -1, 1};
  if (forced_water_targets_[unit] >= 0) {
    action = CompileForcedWater(unit, &completed);
  } else {
    const Control control = static_cast<Control>(selection.control);
    switch (control) {
      case Control::kKeep:
        action = CompileOption(unit, &completed);
        break;
      case Control::kAssign: {
        const Task task = static_cast<Task>(selection.task);
        options_[unit] = Option{
            task,
            TaskNeedsTarget(task) ? static_cast<int>(selection.target) : -1,
            TaskNeedsArgument(task) ? static_cast<int>(selection.argument)
                                    : kNoneArgument,
            static_cast<QuantityMode>(selection.quantity_mode),
            selection.exact_quantity,
            OptionPhase::kApproach,
            step_};
        action = CompileOption(unit, &completed);
        break;
      }
      case Control::kStep:
        options_[unit].reset();
        switch (static_cast<Direction>(selection.direction)) {
          case Direction::kNorth:
            action = UnitAction{UnitOp::kNorth, -1, 1};
            break;
          case Direction::kSouth:
            action = UnitAction{UnitOp::kSouth, -1, 1};
            break;
          case Direction::kEast:
            action = UnitAction{UnitOp::kEast, -1, 1};
            break;
          case Direction::kWest:
            action = UnitAction{UnitOp::kWest, -1, 1};
            break;
        }
        break;
      case Control::kRawLocal:
        options_[unit].reset();
        action = CompileRaw(selection);
        break;
      case Control::kCancelPass:
        options_[unit].reset();
        completed = true;
        break;
    }
  }
  ApplyUnit(unit, action);
  if (completed) options_[unit].reset();
  AdvanceUnit();
}

void Session::ApplyUnit(int unit_index, const UnitAction& action) {
  const UnitActionTrace trace = ApplyUnitAction(
      config_, &shadow_farm_, &shadow_priv_, unit_index, action, day_);
  if (trace.status != UnitActionStatus::kApplied &&
      trace.status != UnitActionStatus::kPass) {
    throw std::logic_error("conditional program compiler emitted an illegal unit action");
  }
  if (unit_index == 0) {
    action_.farmer = action;
  } else {
    action_.hands[unit_index - 1] = action;
  }
}

void Session::SelectMarket(const Selection& selection) {
  const MarketOrderType order_type =
      static_cast<MarketOrderType>(selection.task);
  if (order_type == MarketOrderType::kEnd) {
    phase_ = Phase::kDone;
    return;
  }
  MarketOrder order;
  switch (order_type) {
    case MarketOrderType::kSell:
      order.kind = OrderKind::kSell;
      order.item = static_cast<int>(selection.argument);
      break;
    case MarketOrderType::kBuySeed:
      order.kind = OrderKind::kBuySeed;
      order.item = static_cast<int>(selection.argument);
      break;
    case MarketOrderType::kBuyProduct:
      order.kind = OrderKind::kBuyProduct;
      order.item = static_cast<int>(selection.argument);
      break;
    case MarketOrderType::kBuyAnimal:
      order.kind = OrderKind::kBuyAnimal;
      order.item = static_cast<int>(selection.argument) - item::kGoose;
      break;
    case MarketOrderType::kHire:
      order.kind = OrderKind::kHire;
      break;
    case MarketOrderType::kBuyLand:
      order.kind = OrderKind::kBuyLand;
      break;
    case MarketOrderType::kEnd:
      throw std::logic_error("market END was not handled");
  }
  if (MarketNeedsItem(order_type)) {
    order.remaining = ResolveMarketQuantity(
        order_type, static_cast<int>(selection.argument),
        static_cast<QuantityMode>(selection.quantity_mode),
        selection.exact_quantity);
  }
  action_.market.emplace_back(order);
  ProjectMarket(order);
  ++market_slot_;
  if (market_slot_ >= config_.max_market_orders) phase_ = Phase::kDone;
}

NumericAction Session::Action(const Engine& engine, int player) {
  Refresh(engine.farm(player), engine.priv(player), engine.market(),
          engine.step_index(), player);
  if (phase_ != Phase::kDone) {
    NumericAction blocked;
    blocked.unit_count = unit_count_;
    blocked.requires_decision = true;
    return blocked;
  }
  NumericAction result;
  result.tokens.assign(static_cast<size_t>(maximum_decisions()), 0);
  result.quantities.assign(static_cast<size_t>(maximum_decisions()), 0);
  result.unit_count = unit_count_;
  result.decision_count = policy::EncodePlayerAction(
      action_, unit_count_, result.tokens.data(), result.quantities.data(),
      maximum_decisions());
  result.action = action_;
  return result;
}

bool Session::DecisionRequiredVisible(const VisibleState& state) {
  Refresh(state.farm, state.priv, state.market, state.step, state.player);
  return phase_ != Phase::kDone;
}

Decision Session::ObserveVisible(const VisibleState& state) {
  Refresh(state.farm, state.priv, state.market, state.step, state.player);
  if (phase_ == Phase::kDone) {
    throw std::logic_error("conditional program has no pending visible decision");
  }
  return BuildDecision();
}

void Session::SelectVisible(const VisibleState& state,
                            const Selection& selection) {
  Refresh(state.farm, state.priv, state.market, state.step, state.player);
  SelectCurrent(selection);
}

Selection Session::SelectReplayUnitVisible(
    const VisibleState& state, const Selection& fallback,
    const std::vector<Selection>& proposals) {
  Refresh(state.farm, state.priv, state.market, state.step, state.player);
  if (phase_ != Phase::kUnit) {
    throw std::logic_error(
        "conditional replay selection requires a pending unit decision");
  }
  const int unit = unit_index_;
  const auto selected_action = [this, unit](const Selection& selection) {
    Session probe = *this;
    probe.SelectCurrent(selection);
    return unit == 0 ? probe.action_.farmer
                     : probe.action_.hands.at(static_cast<size_t>(unit - 1));
  };
  const UnitAction expected = selected_action(fallback);
  const Decision masks = BuildDecision();

  Selection keep;
  keep.control = static_cast<int64_t>(Control::kKeep);
  if (masks.control_mask[static_cast<int>(Control::kKeep)] &&
      SameUnitAction(selected_action(keep), expected)) {
    SelectCurrent(keep);
    return keep;
  }

  if (masks.control_mask[static_cast<int>(Control::kAssign)]) {
    for (const Selection& proposal : proposals) {
      if (proposal.control != static_cast<int64_t>(Control::kAssign)) continue;
      try {
        if (SameUnitAction(selected_action(proposal), expected)) {
          SelectCurrent(proposal);
          return proposal;
        }
      } catch (const std::invalid_argument&) {
        // A suffix-derived semantic proposal may be masked by the live shadow
        // state. Continue through the ordered candidates before falling back.
      }
    }
  }

  SelectCurrent(fallback);
  return fallback;
}

NumericAction Session::ActionVisible(const VisibleState& state) {
  Refresh(state.farm, state.priv, state.market, state.step, state.player);
  if (phase_ != Phase::kDone) {
    NumericAction blocked;
    blocked.unit_count = unit_count_;
    blocked.requires_decision = true;
    return blocked;
  }
  NumericAction result;
  result.tokens.assign(static_cast<size_t>(maximum_decisions()), 0);
  result.quantities.assign(static_cast<size_t>(maximum_decisions()), 0);
  result.unit_count = unit_count_;
  result.decision_count = policy::EncodePlayerAction(
      action_, unit_count_, result.tokens.data(), result.quantities.data(),
      maximum_decisions());
  result.action = action_;
  return result;
}

}  // namespace kagg::programs
