// Python boundary for the fully native deterministic planner.

#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include <algorithm>
#include <array>
#include <numeric>
#include <optional>
#include <string>
#include <utility>
#include <vector>

#include "planner.hpp"
#include "py_convert.hpp"

namespace py = pybind11;

namespace kagg {
namespace {

planner::SchedulerKind ParseScheduler(const std::string& name) {
  if (name == "greedy") return planner::SchedulerKind::kGreedy;
  if (name == "deadline_aware") return planner::SchedulerKind::kDeadlineAware;
  if (name == "min_cost") return planner::SchedulerKind::kMinCost;
  if (name == "route_aware") return planner::SchedulerKind::kRouteAware;
  if (name == "territory_aware") {
    return planner::SchedulerKind::kTerritoryAware;
  }
  throw py::value_error("native planner does not support scheduler: " + name);
}

planner::ProjectLayoutKind ParseProjectLayout(const std::string& name) {
  if (name == "adaptive") return planner::ProjectLayoutKind::kAdaptive;
  if (name == "service_zones") {
    return planner::ProjectLayoutKind::kServiceZones;
  }
  if (name == "crop_core") return planner::ProjectLayoutKind::kCropCore;
  throw py::value_error("native planner does not support project layout: " + name);
}

planner::SupplyRouteMode ParseSupplyRouteMode(const std::string& name) {
  if (name == "unbound") return planner::SupplyRouteMode::kUnbound;
  if (name == "task_bound") return planner::SupplyRouteMode::kTaskBound;
  throw py::value_error("native planner does not support supply route mode: " +
                        name);
}

planner::TaskContinuationMode ParseTaskContinuationMode(
    const std::string& name) {
  if (name == "release") return planner::TaskContinuationMode::kRelease;
  if (name == "sticky") return planner::TaskContinuationMode::kSticky;
  if (name == "regret") return planner::TaskContinuationMode::kRegret;
  throw py::value_error(
      "native planner does not support task continuation mode: " + name);
}

planner::SoftServiceMode ParseSoftServiceMode(const std::string& name) {
  if (name == "eager") return planner::SoftServiceMode::kEager;
  if (name == "survival_first") {
    return planner::SoftServiceMode::kSurvivalFirst;
  }
  throw py::value_error("native planner does not support soft service mode: " +
                        name);
}

bool DictBool(const py::dict& values, const char* key, bool fallback) {
  return values.contains(key) ? py::cast<bool>(values[key]) : fallback;
}

int DictInt(const py::dict& values, const char* key, int fallback) {
  return values.contains(key) ? py::cast<int>(values[key]) : fallback;
}

double DictDouble(const py::dict& values, const char* key, double fallback) {
  return values.contains(key) ? py::cast<double>(values[key]) : fallback;
}

planner::SaleMode ParseSaleMode(const std::string& name) {
  if (name == "hold") return planner::SaleMode::kHold;
  if (name == "capacity") return planner::SaleMode::kCapacity;
  if (name == "value") return planner::SaleMode::kValue;
  if (name == "impact") return planner::SaleMode::kImpact;
  if (name == "aggressive") return planner::SaleMode::kAggressive;
  throw py::value_error("native planner does not support sale mode: " + name);
}

planner::PlannerOptions ParsePlannerOptions(py::object value) {
  planner::PlannerOptions options;
  if (value.is_none()) return options;
  const py::dict root = py::cast<py::dict>(value);
  if (root.contains("scheduler")) {
    options.scheduler = ParseScheduler(py::cast<std::string>(root["scheduler"]));
  }
  options.supply_route_capacity = DictInt(
      root, "supply_route_capacity", options.supply_route_capacity);
  if (options.supply_route_capacity < 0) {
    throw py::value_error("supply_route_capacity must be non-negative");
  }
  if (root.contains("supply_route_mode")) {
    options.supply_route_mode = ParseSupplyRouteMode(
        py::cast<std::string>(root["supply_route_mode"]));
  }
  if (root.contains("task_continuation_mode")) {
    options.task_continuation_mode = ParseTaskContinuationMode(
        py::cast<std::string>(root["task_continuation_mode"]));
  }
  options.continuation_travel_value = DictInt(
      root, "continuation_travel_value", options.continuation_travel_value);
  if (options.continuation_travel_value < 0) {
    throw py::value_error("continuation_travel_value must be non-negative");
  }
  if (root.contains("project_layout")) {
    options.project_layout =
        ParseProjectLayout(py::cast<std::string>(root["project_layout"]));
  }
  options.animal_zone_cells =
      DictInt(root, "animal_zone_cells", options.animal_zone_cells);
  if (options.animal_zone_cells < 0) {
    throw py::value_error("animal_zone_cells must be non-negative");
  }
  options.crop_zone_cells =
      DictInt(root, "crop_zone_cells", options.crop_zone_cells);
  if (options.crop_zone_cells < 0) {
    throw py::value_error("crop_zone_cells must be non-negative");
  }
  options.project_layout_start_day = DictInt(
      root, "project_layout_start_day", options.project_layout_start_day);
  if (options.project_layout_start_day < 0) {
    throw py::value_error("project_layout_start_day must be non-negative");
  }
  const py::dict strategy =
      root.contains("strategy") ? py::cast<py::dict>(root["strategy"])
                                : py::dict();
  if (strategy.contains("strategic_control_mode")) {
    const std::string mode =
        py::cast<std::string>(strategy["strategic_control_mode"]);
    if (mode == "explicit") {
      options.strategy.explicit_control = true;
    } else if (mode != "heuristic") {
      throw py::value_error("unknown strategic control mode");
    }
  }
  if (options.strategy.explicit_control) {
    constexpr std::array<const char*, 18> required_fields = {
        "target_workers",
        "target_plants",
        "preferred_crop",
        "enforce_production_targets",
        "allow_land",
        "allow_crop_investment",
        "allow_animal_investment",
        "liquidation_only",
        "target_land_quadrants",
        "target_crops",
        "target_animals",
        "cash_reserve_fraction",
        "cash_reserve_amount",
        "product_reserves",
        "minimum_sale_prices",
        "sale_mode",
        "one_time_harvest",
        "soft_service_mode",
    };
    for (const char* field : required_fields) {
      if (!strategy.contains(field) || strategy[field].is_none()) {
        throw py::value_error(
            "explicit strategic control is missing a required field");
      }
    }
    if (!strategy.contains("preferred_animal")) {
      throw py::value_error(
          "explicit strategic control is missing a required field");
    }
  }
  options.strategy.target_workers =
      DictInt(strategy, "target_workers", options.strategy.target_workers);
  options.strategy.target_plants =
      DictInt(strategy, "target_plants", options.strategy.target_plants);
  if (strategy.contains("preferred_crop")) {
    options.strategy.preferred_crop = pyconv::LookupItem(
        py::cast<std::string>(strategy["preferred_crop"]), kNumCrops);
    if (options.strategy.preferred_crop < 0) {
      throw py::value_error("unknown preferred crop");
    }
  }
  options.strategy.enforce_production_targets = DictBool(
      strategy, "enforce_production_targets",
      options.strategy.enforce_production_targets);
  options.strategy.allow_land =
      DictBool(strategy, "allow_land", options.strategy.allow_land);
  options.strategy.allow_crop_investment = DictBool(
      strategy, "allow_crop_investment",
      options.strategy.allow_crop_investment);
  options.strategy.allow_animal_investment = DictBool(
      strategy, "allow_animal_investment",
      options.strategy.allow_animal_investment);
  if (strategy.contains("preferred_animal") &&
      !strategy["preferred_animal"].is_none()) {
    const int item_index = pyconv::LookupItem(
        py::cast<std::string>(strategy["preferred_animal"]), kNumItems);
    if (item_index < item::kGoose) {
      throw py::value_error("unknown preferred animal");
    }
    options.strategy.preferred_animal = item_index - item::kGoose;
  }
  options.strategy.liquidation_only = DictBool(
      strategy, "liquidation_only", options.strategy.liquidation_only);
  if (strategy.contains("one_time_harvest")) {
    const std::string mode =
        py::cast<std::string>(strategy["one_time_harvest"]);
    if (mode == "earliest") {
      options.strategy.defer_one_time_harvest = false;
    } else if (mode == "max_yield") {
      options.strategy.defer_one_time_harvest = true;
    } else {
      throw py::value_error("unknown one-time harvest mode");
    }
  }
  if (strategy.contains("soft_service_mode")) {
    options.strategy.soft_service_mode = ParseSoftServiceMode(
        py::cast<std::string>(strategy["soft_service_mode"]));
  }
  if (strategy.contains("target_land_quadrants") &&
      !strategy["target_land_quadrants"].is_none()) {
    options.strategy.target_land_quadrants =
        py::cast<int>(strategy["target_land_quadrants"]);
  }
  if (options.strategy.target_land_quadrants < 0 ||
      options.strategy.target_land_quadrants > 4) {
    throw py::value_error("target_land_quadrants must be in [0, 4]");
  }
  if (strategy.contains("target_crops") &&
      !strategy["target_crops"].is_none()) {
    const auto targets = py::cast<std::vector<int>>(strategy["target_crops"]);
    if (targets.size() != kNumCrops ||
        std::any_of(targets.begin(), targets.end(),
                    [](int target) { return target < 0; })) {
      throw py::value_error(
          "target_crops must contain one non-negative target per crop");
    }
    options.strategy.has_crop_targets = true;
    std::copy(targets.begin(), targets.end(),
              options.strategy.target_crops.begin());
  }
  if (strategy.contains("target_animals") &&
      !strategy["target_animals"].is_none()) {
    const auto targets =
        py::cast<std::vector<int>>(strategy["target_animals"]);
    if (targets.size() != kNumAnimals ||
        std::any_of(targets.begin(), targets.end(),
                    [](int target) { return target < 0; })) {
      throw py::value_error(
          "target_animals must contain one non-negative target per animal");
    }
    options.strategy.has_animal_targets = true;
    std::copy(targets.begin(), targets.end(),
              options.strategy.target_animals.begin());
  }
  options.strategy.cash_reserve_fraction = DictDouble(
      strategy, "cash_reserve_fraction",
      options.strategy.cash_reserve_fraction);
  if (options.strategy.cash_reserve_fraction < 0.0 ||
      options.strategy.cash_reserve_fraction > 1.0) {
    throw py::value_error("cash_reserve_fraction must be in [0, 1]");
  }
  options.strategy.cash_reserve_amount = DictDouble(
      strategy, "cash_reserve_amount", options.strategy.cash_reserve_amount);
  if (options.strategy.cash_reserve_amount < 0.0) {
    throw py::value_error("cash_reserve_amount must be non-negative");
  }
  if (strategy.contains("product_reserves") &&
      !strategy["product_reserves"].is_none()) {
    const auto reserves =
        py::cast<std::vector<int64_t>>(strategy["product_reserves"]);
    if (reserves.size() != kNumProducts ||
        std::any_of(reserves.begin(), reserves.end(),
                    [](int64_t reserve) { return reserve < 0; })) {
      throw py::value_error(
          "product_reserves must contain one non-negative value per product");
    }
    std::copy(reserves.begin(), reserves.end(),
              options.strategy.product_reserves.begin());
  }
  if (strategy.contains("minimum_sale_prices") &&
      !strategy["minimum_sale_prices"].is_none()) {
    const auto prices =
        py::cast<std::vector<double>>(strategy["minimum_sale_prices"]);
    if (prices.size() != kNumProducts ||
        std::any_of(prices.begin(), prices.end(),
                    [](double price) { return price < 0.0; })) {
      throw py::value_error(
          "minimum_sale_prices must contain one non-negative value per product");
    }
    std::copy(prices.begin(), prices.end(),
              options.strategy.minimum_sale_prices.begin());
  }
  if (strategy.contains("sale_mode")) {
    options.strategy.sale_mode =
        ParseSaleMode(py::cast<std::string>(strategy["sale_mode"]));
  }
  if (options.strategy.explicit_control) {
    if (options.strategy.target_workers < 1 ||
        options.strategy.target_plants < 0) {
      throw py::value_error(
          "explicit worker target must be positive and plant target non-negative");
    }
    if (!options.strategy.enforce_production_targets ||
        options.strategy.target_land_quadrants == 0 ||
        !options.strategy.has_crop_targets ||
        !options.strategy.has_animal_targets) {
      throw py::value_error(
          "explicit strategic control requires complete production targets");
    }
    const int crop_total = std::accumulate(
        options.strategy.target_crops.begin(),
        options.strategy.target_crops.end(), 0);
    if (crop_total != options.strategy.target_plants) {
      throw py::value_error(
          "explicit plant total differs from crop targets");
    }
    if (crop_total > 0 &&
        options.strategy.target_crops[options.strategy.preferred_crop] == 0) {
      throw py::value_error(
          "explicit preferred crop is absent from crop targets");
    }
    const int animal_total = std::accumulate(
        options.strategy.target_animals.begin(),
        options.strategy.target_animals.end(), 0);
    if ((animal_total > 0 && options.strategy.preferred_animal < 0) ||
        (animal_total == 0 && options.strategy.preferred_animal >= 0) ||
        (options.strategy.preferred_animal >= 0 &&
         options.strategy.target_animals[options.strategy.preferred_animal] ==
             0)) {
      throw py::value_error(
          "explicit animal targets and preferred animal differ");
    }
  }
  return options;
}

MarketState ParseMarket(const py::dict& observation) {
  MarketState state;
  const auto market = py::cast<py::dict>(observation["market"]);
  const auto inventory = py::cast<py::dict>(market["inventory"]);
  const auto prices = py::cast<py::dict>(market["prices"]);
  for (int item_index = 0; item_index < kNumProducts; ++item_index) {
    state.inventory[item_index] =
        py::cast<int64_t>(inventory[kItemNames[item_index]]);
    state.prices[item_index] =
        py::cast<int64_t>(prices[kItemNames[item_index]]);
  }
  return state;
}

const char* CommitmentName(planner::CommitmentKind kind) {
  switch (kind) {
    case planner::CommitmentKind::kTask:
      return "task";
    case planner::CommitmentKind::kSupply:
      return "supply";
    case planner::CommitmentKind::kReturn:
      return "return";
  }
  return "task";
}

py::object OptionalString(const std::string& value) {
  return value.empty() ? py::none() : py::cast(value);
}

py::dict UnitTraceToPy(const UnitActionTrace& trace) {
  py::dict out;
  out["unit_index"] = trace.unit_index;
  out["requested"] = pyconv::UnitActionToPy(trace.requested);
  out["actual"] = pyconv::UnitActionToPy(trace.actual);
  out["status"] = UnitActionStatusName(trace.status);
  return out;
}

py::object OptionalMarketOrderToPy(
    const std::optional<MarketOrder>& order) {
  if (!order) return py::none();
  return pyconv::MarketOrderToPy(*order);
}

py::dict MarketTraceToPy(const MarketSlotTrace& trace) {
  py::dict out;
  out["slot_index"] = trace.slot_index;
  out["requested"] = OptionalMarketOrderToPy(trace.requested);
  out["actual"] = OptionalMarketOrderToPy(trace.actual);
  out["status"] = MarketOrderStatusName(trace.status);
  out["committed"] = trace.committed;
  out["money_before"] = trace.money_before;
  out["money_after"] = trace.money_after;
  out["shed_total_before"] = trace.shed_total_before;
  out["shed_total_after"] = trace.shed_total_after;
  return out;
}

py::dict IntentToPy(const planner::Intent& intent) {
  py::dict out;
  out["key"] = intent.key;
  out["action"] = pyconv::UnitActionToPy(intent.action);
  py::list predecessors;
  for (const std::string& predecessor : intent.predecessors) {
    predecessors.append(predecessor);
  }
  out["predecessors"] = predecessors;
  out["required_item"] = intent.required_item < 0
                             ? py::none()
                             : py::cast(kItemNames[intent.required_item]);
  out["priority"] = intent.priority;
  out["hard"] = intent.hard;
  out["deadline_step"] = intent.deadline_step
                             ? py::cast(*intent.deadline_step)
                             : py::none();
  out["resource_group"] = OptionalString(intent.resource_group);
  out["resource_limit"] = intent.resource_group.empty()
                              ? py::none()
                              : py::cast(intent.resource_limit);
  out["exclusive_group"] = OptionalString(intent.exclusive_group);
  out["reserve_before_ready"] = intent.reserve_before_ready;
  out["allow_supply"] = intent.allow_supply;
  out["requires_command"] = intent.requires_command;
  out["proposal_only"] = intent.proposal_only;
  return out;
}

py::list TasksToPy(const std::vector<planner::Task>& tasks) {
  py::list out;
  for (const planner::Task& task : tasks) {
    py::dict entry;
    entry["key"] = task.key;
    entry["position"] = py::make_tuple(task.position.first, task.position.second);
    entry["priority"] = task.priority;
    entry["deadline_step"] = task.deadline_step
                                 ? py::cast(*task.deadline_step)
                                 : py::none();
    entry["reason"] = task.reason;
    entry["layout_cost"] = task.layout_cost;
    py::list intents;
    for (const planner::Intent& intent : task.intents) {
      intents.append(IntentToPy(intent));
    }
    entry["nodes"] = intents;
    out.append(entry);
  }
  return out;
}

py::dict ScheduleToPy(const planner::ScheduleResult& schedule) {
  py::dict out;
  out["farmer"] = pyconv::UnitActionToPy(schedule.requested.farmer);
  py::list hands;
  for (const UnitAction& action : schedule.requested.hands) {
    hands.append(pyconv::UnitActionToPy(action));
  }
  out["hands"] = hands;
  py::list assignments;
  for (const planner::Assignment& assignment : schedule.assignments) {
    py::dict entry;
    entry["unit_index"] = assignment.unit_index;
    entry["task"] = assignment.task;
    entry["target"] =
        py::make_tuple(assignment.target.first, assignment.target.second);
    entry["action"] = pyconv::UnitActionToPy(assignment.action);
    entry["reason"] = assignment.reason;
    entry["node"] = OptionalString(assignment.node);
    assignments.append(entry);
  }
  out["assignments"] = assignments;
  py::list deferred;
  for (const std::string& task : schedule.deferred_tasks) {
    py::dict entry;
    entry["task"] = task;
    entry["reason"] = "scheduled_route_or_missing_supply";
    entry["remaining_nodes"] = py::list();
    deferred.append(entry);
  }
  out["deferred_tasks"] = deferred;
  out["unassigned_units"] = schedule.unassigned_units;
  py::dict reservations;
  py::dict shortfalls;
  for (int item_index = 0; item_index < kNumItems; ++item_index) {
    if (schedule.supply_reservations[item_index] <= 0) continue;
    reservations[kItemNames[item_index]] =
        schedule.supply_reservations[item_index];
    shortfalls[kItemNames[item_index]] = schedule.supply_shortfalls[item_index];
  }
  out["supply_reservations"] = reservations;
  out["supply_shortfalls"] = shortfalls;
  py::list commitments;
  for (const auto& [unit_index, commitment] : schedule.commitments) {
    py::dict entry;
    entry["unit_index"] = unit_index;
    entry["kind"] = CommitmentName(commitment.kind);
    entry["target"] =
        py::make_tuple(commitment.target.first, commitment.target.second);
    entry["task"] = OptionalString(commitment.task_key);
    entry["item"] = commitment.item < 0
                        ? py::none()
                        : py::cast(kItemNames[commitment.item]);
    entry["route_tasks"] = commitment.route_tasks;
    commitments.append(entry);
  }
  out["commitments"] = commitments;
  return out;
}

py::list StrategyTraceToPy(
    const std::vector<planner::StrategyTrace>& traces) {
  py::list out;
  for (const planner::StrategyTrace& trace : traces) {
    py::dict entry;
    entry["kind"] = trace.kind;
    if (!trace.action.empty()) entry["action"] = trace.action;
    if (!trace.operation.empty()) entry["operation"] = trace.operation;
    if (trace.item >= 0) entry["item"] = kItemNames[trace.item];
    if (trace.count > 0) entry["count"] = trace.count;
    entry["selected"] = trace.selected;
    if (!trace.reason.empty()) entry["reason"] = trace.reason;
    if (!trace.retry_state.empty()) entry["retry_state"] = trace.retry_state;
    if (trace.normalized_count) {
      entry["normalized_count"] = *trace.normalized_count;
    }
    out.append(entry);
  }
  return out;
}

py::dict PlanToPy(const planner::PlanResult& plan, bool include_diagnostics) {
  py::list unit_trace;
  for (const UnitActionTrace& trace : plan.unit_trace) {
    unit_trace.append(UnitTraceToPy(trace));
  }
  py::list market_trace;
  for (const MarketSlotTrace& trace : plan.market_trace) {
    market_trace.append(MarketTraceToPy(trace));
  }
  py::dict compiler;
  compiler["unit"] = unit_trace;
  compiler["market"] = market_trace;
  compiler["opponent_scenario"] = "no_orders";
  compiler["truncated_orders"] = plan.truncated_orders;

  py::dict out;
  out["action"] = pyconv::PlayerActionToPy(plan.action);
  if (include_diagnostics) {
    out["tasks"] = TasksToPy(plan.tasks);
    out["schedule"] = ScheduleToPy(plan.schedule);
  }
  out["strategy"] = StrategyTraceToPy(plan.strategy_trace);
  out["compiler"] = compiler;
  return out;
}

class PyNativePlanner {
 public:
  PyNativePlanner(py::object configuration, py::object options)
      : config_(pyconv::ParseConfig(configuration)),
        planner_(config_, ParsePlannerOptions(options)) {}

  py::dict Plan(const py::dict& observation) {
    auto [farm, opponent, priv, market, player, step] = Parse(observation);
    planner::PlanResult result;
    {
      py::gil_scoped_release release;
      result = planner_.Plan(farm, opponent, priv, market, player, step);
    }
    return PlanToPy(result, true);
  }

  py::dict PlanCompact(const py::dict& observation) {
    auto [farm, opponent, priv, market, player, step] = Parse(observation);
    planner::PlanResult result;
    {
      py::gil_scoped_release release;
      result = planner_.Plan(farm, opponent, priv, market, player, step);
    }
    return PlanToPy(result, false);
  }

  py::dict Act(const py::dict& observation) {
    auto [farm, opponent, priv, market, player, step] = Parse(observation);
    planner::PlanResult result;
    {
      py::gil_scoped_release release;
      result = planner_.Plan(farm, opponent, priv, market, player, step);
    }
    return pyconv::PlayerActionToPy(result.action);
  }

  void Reset() { planner_.Reset(); }

 private:
  struct Parsed {
    Farm farm;
    Farm opponent;
    PrivateState priv;
    MarketState market;
    int player = 0;
    int step = 0;
  };

  Parsed Parse(const py::dict& observation) const {
    Parsed parsed;
    parsed.player = py::cast<int>(observation["player"]);
    if (parsed.player < 0 || parsed.player > 1) {
      throw py::value_error("observation player must be 0 or 1");
    }
    parsed.step = py::cast<int>(observation["step"]);
    const auto farms = py::cast<py::list>(observation["farms"]);
    parsed.farm = pyconv::ParseFarm(py::cast<py::dict>(farms[parsed.player]),
                                    config_.board_size);
    parsed.opponent = pyconv::ParseFarm(
        py::cast<py::dict>(farms[1 - parsed.player]), config_.board_size);
    parsed.priv = pyconv::ParsePrivate(py::cast<py::dict>(observation["private"]));
    parsed.market = ParseMarket(observation);
    return parsed;
  }

  Config config_;
  planner::NativePlanner planner_;
};


}  // namespace

void BindPlanner(py::module_& module) {
  py::class_<PyNativePlanner>(module, "NativePlanner")
      .def(py::init<py::object, py::object>(), py::arg("configuration") = py::none(),
           py::arg("options") = py::none())
      .def("plan", &PyNativePlanner::Plan, py::arg("observation"),
           "Compile one complete deterministic decision and diagnostic trace.")
      .def("plan_compact", &PyNativePlanner::PlanCompact, py::arg("observation"),
           "Compile one decision and return action plus compiler diagnostics.")
      .def("act", &PyNativePlanner::Act, py::arg("observation"),
           "Compile one complete deterministic decision and return only its action.")
      .def("reset", &PyNativePlanner::Reset)
      .def_property_readonly_static(
          "spec_version", [](py::object) { return planner::kPlannerSpecVersion; });
}

}  // namespace kagg
