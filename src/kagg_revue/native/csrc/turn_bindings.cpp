// Python binding for the prefix shadow-state turn compiler.

#include <pybind11/pybind11.h>

#include <algorithm>
#include <array>

#include "market_phase.hpp"
#include "py_convert.hpp"
#include "unit_phase.hpp"

namespace py = pybind11;

namespace kagg {
namespace {

py::dict TraceToPy(const UnitActionTrace& trace) {
  py::dict out;
  out["unit_index"] = trace.unit_index;
  out["requested"] = pyconv::UnitActionToPy(trace.requested);
  out["actual"] = pyconv::UnitActionToPy(trace.actual);
  out["status"] = UnitActionStatusName(trace.status);
  return out;
}

py::object OptionalMarketOrderToPy(const std::optional<MarketOrder>& order) {
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

MarketState ParseMarketState(const py::dict& observation) {
  MarketState state;
  const auto market = py::reinterpret_borrow<py::dict>(observation["market"]);
  const auto inventory = py::reinterpret_borrow<py::dict>(market["inventory"]);
  const auto prices = py::reinterpret_borrow<py::dict>(market["prices"]);
  for (int item_index = 0; item_index < kNumProducts; ++item_index) {
    const char* name = kItemNames[item_index];
    state.inventory[item_index] = py::cast<int64_t>(inventory[name]);
    state.prices[item_index] = py::cast<int64_t>(prices[name]);
  }
  return state;
}

py::dict MarketStateToPy(const MarketState& state) {
  py::dict inventory;
  py::dict prices;
  for (int item_index = 0; item_index < kNumProducts; ++item_index) {
    inventory[kItemNames[item_index]] = state.inventory[item_index];
    prices[kItemNames[item_index]] = state.prices[item_index];
  }
  py::dict out;
  out["inventory"] = inventory;
  out["prices"] = prices;
  return out;
}

py::dict CompileUnitPrefixFromObservation(const py::dict& observation,
                                          py::object configuration,
                                          py::handle requested_action) {
  const Config config = pyconv::ParseConfig(configuration);
  const int player = py::cast<int>(observation["player"]);
  if (player < 0 || player > 1) throw py::value_error("observation player must be 0 or 1");

  const int step = py::cast<int>(observation["step"]);
  const int day = step / config.turns_per_day;
  const auto farms = py::reinterpret_borrow<py::list>(observation["farms"]);
  const Farm farm = pyconv::ParseFarm(py::reinterpret_borrow<py::dict>(farms[player]),
                                      config.board_size);
  const PrivateState priv =
      pyconv::ParsePrivate(py::reinterpret_borrow<py::dict>(observation["private"]));
  const PlayerAction requested =
      pyconv::ParsePlayerAction(requested_action, config.max_market_orders);
  const UnitPhaseResult result = CompileUnitPhase(config, farm, priv, requested, day);

  py::dict post_unit;
  post_unit["farm"] = pyconv::FarmToPy(result.farm, config.board_size);
  post_unit["private"] = pyconv::PrivateToPy(result.priv);

  py::list trace;
  for (const UnitActionTrace& entry : result.trace) trace.append(TraceToPy(entry));

  py::dict out;
  out["spec_version"] = kUnitCompilerSpecVersion;
  out["action"] = pyconv::PlayerActionToPy(result.actual);
  out["post_unit"] = post_unit;
  out["trace"] = trace;
  return out;
}

py::dict CompileMarketFromPostUnit(const py::dict& observation,
                                   py::object configuration,
                                   const py::dict& post_unit,
                                   py::handle requested_market) {
  const Config config = pyconv::ParseConfig(configuration);
  const int player = py::cast<int>(observation["player"]);
  if (player < 0 || player > 1) throw py::value_error("observation player must be 0 or 1");

  const auto observed_farms = py::reinterpret_borrow<py::list>(observation["farms"]);
  std::array<Farm, 2> farms;
  farms[player] = pyconv::ParseFarm(
      py::reinterpret_borrow<py::dict>(post_unit["farm"]), config.board_size);
  farms[1 - player] = pyconv::ParseFarm(
      py::reinterpret_borrow<py::dict>(observed_farms[1 - player]), config.board_size);
  std::array<PrivateState, 2> privates;
  privates[player] =
      pyconv::ParsePrivate(py::reinterpret_borrow<py::dict>(post_unit["private"]));

  py::dict requested_action;
  requested_action["market"] = requested_market;
  std::array<PlayerAction, 2> actions;
  const int max_orders = std::max(1, config.max_market_orders);
  actions[player] = pyconv::ParsePlayerAction(requested_action, max_orders);
  const int requested_slots = py::isinstance<py::list>(requested_market)
                                  ? static_cast<int>(py::len(requested_market))
                                  : 0;

  MarketState market = ParseMarketState(observation);
  const std::array<Farm*, 2> farm_ptrs = {&farms[0], &farms[1]};
  const std::array<PrivateState*, 2> private_ptrs = {&privates[0], &privates[1]};
  std::vector<MarketSlotTrace> trace;
  ApplyMarketPhase(config, farm_ptrs, private_ptrs, &market, actions[0], actions[1],
                   &trace);

  PlayerAction actual;
  actual.market.resize(actions[player].market.size());
  py::list trace_out;
  for (const MarketSlotTrace& entry : trace) {
    if (entry.player != player) continue;
    actual.market[entry.slot_index] = entry.actual;
    trace_out.append(MarketTraceToPy(entry));
  }

  py::dict post_market;
  post_market["farm"] = pyconv::FarmToPy(farms[player], config.board_size);
  post_market["private"] = pyconv::PrivateToPy(privates[player]);
  post_market["market"] = MarketStateToPy(market);

  py::dict out;
  out["spec_version"] = kMarketCompilerSpecVersion;
  out["market"] = pyconv::PlayerActionToPy(actual)["market"];
  out["post_market"] = post_market;
  out["trace"] = trace_out;
  out["opponent_scenario"] = "no_orders";
  out["truncated_orders"] =
      std::max(0, requested_slots - static_cast<int>(actions[player].market.size()));
  return out;
}

}  // namespace

void BindTurn(py::module_& module) {
  module.def(
      "compile_unit_prefix_from_obs", &CompileUnitPrefixFromObservation,
      py::arg("obs"), py::arg("configuration"), py::arg("requested_action"),
      "Compile farmer/hands sequentially on a shadow copy of an official observation. "
      "Returns the actual protocol action, post-unit state and per-unit trace.");
  module.def(
      "compile_market_from_post_unit", &CompileMarketFromPostUnit,
      py::arg("obs"), py::arg("configuration"), py::arg("post_unit"),
      py::arg("requested_market"),
      "Compile an ordered market queue from post-unit state under an explicit "
      "no-opponent-orders scenario.");
}

}  // namespace kagg
