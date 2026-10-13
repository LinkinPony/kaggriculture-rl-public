// Shared official-engine wrapper; no strategy or teacher session dependencies.
#pragma once

#include <pybind11/numpy.h>
#include <pybind11/pybind11.h>

#include <algorithm>
#include <array>
#include <cstdint>
#include <string>
#include <vector>

#include "action_codec.hpp"
#include "actor_encoding.hpp"
#include "../engine.hpp"
#include "py_convert.hpp"

namespace kagg {
namespace py = pybind11;

using pyconv::ConfigToPy;
using pyconv::ObservationToPy;
using pyconv::ParseConfig;
using pyconv::ParsePlayerAction;

class PyEngine {
 public:
  PyEngine(int64_t seed, py::object configuration)
      : engine_(ParseConfig(configuration), CheckSeed(seed)) {}

  explicit PyEngine(const Engine& engine) : engine_(engine) {}

  PyEngine Clone() const { return PyEngine(engine_); }

  void Reset(int64_t seed) { engine_.Reset(CheckSeed(seed)); }

  bool Step(py::handle action0, py::handle action1) {
    const int max_orders = engine_.config().max_market_orders;
    const PlayerAction a0 = ParsePlayerAction(action0, max_orders);
    const PlayerAction a1 = ParsePlayerAction(action1, max_orders);
    engine_.Step(a0, a1);
    return engine_.done();
  }

  bool StepNumeric(
      py::array_t<int64_t, py::array::c_style | py::array::forcecast> tokens,
      py::array_t<int64_t, py::array::c_style | py::array::forcecast> quantities,
      py::array_t<int64_t, py::array::c_style | py::array::forcecast> decision_counts,
      py::array_t<int64_t, py::array::c_style | py::array::forcecast> unit_counts) {
    const py::buffer_info token_info = tokens.request();
    const py::buffer_info quantity_info = quantities.request();
    const py::buffer_info decision_info = decision_counts.request();
    const py::buffer_info unit_info = unit_counts.request();
    if (token_info.ndim != 2 || token_info.shape[0] != 2 ||
        quantity_info.ndim != 2 || quantity_info.shape != token_info.shape ||
        decision_info.ndim != 1 || decision_info.shape[0] != 2 ||
        unit_info.ndim != 1 || unit_info.shape[0] != 2) {
      throw py::value_error(
          "numeric actions require tokens/quantities [2,D] and counts [2]");
    }
    const auto* token_data = static_cast<const int64_t*>(token_info.ptr);
    const auto* quantity_data = static_cast<const int64_t*>(quantity_info.ptr);
    const auto* decisions = static_cast<const int64_t*>(decision_info.ptr);
    const auto* units = static_cast<const int64_t*>(unit_info.ptr);
    const int width = static_cast<int>(token_info.shape[1]);
    std::array<PlayerAction, 2> actions;
    for (int player = 0; player < 2; ++player) {
      if (decisions[player] < 0 || decisions[player] > width || units[player] < 1 ||
          units[player] > decisions[player]) {
        throw py::value_error("numeric action counts are outside their buffers");
      }
      actions[player] = policy::DecodePlayerAction(
          token_data + player * width, quantity_data + player * width,
          static_cast<int>(decisions[player]), static_cast<int>(units[player]),
          engine_.config().max_market_orders);
    }
    {
      py::gil_scoped_release release;
      engine_.Step(actions[0], actions[1]);
    }
    return engine_.done();
  }

  bool StepMixedNumeric(
      int numeric_player,
      py::array_t<int64_t, py::array::c_style | py::array::forcecast> tokens,
      py::array_t<int64_t, py::array::c_style | py::array::forcecast> quantities,
      int decision_count, int unit_count, py::handle other_action) {
    CheckPlayer(numeric_player);
    const py::buffer_info token_info = tokens.request();
    const py::buffer_info quantity_info = quantities.request();
    if (token_info.ndim != 1 || quantity_info.ndim != 1 ||
        quantity_info.shape != token_info.shape || decision_count < 0 ||
        decision_count > token_info.shape[0]) {
      throw py::value_error("mixed numeric action buffers must be matching vectors");
    }
    std::array<PlayerAction, 2> actions;
    actions[numeric_player] = policy::DecodePlayerAction(
        static_cast<const int64_t*>(token_info.ptr),
        static_cast<const int64_t*>(quantity_info.ptr), decision_count, unit_count,
        engine_.config().max_market_orders);
    actions[1 - numeric_player] =
        ParsePlayerAction(other_action, engine_.config().max_market_orders);
    {
      py::gil_scoped_release release;
      engine_.Step(actions[0], actions[1]);
    }
    return engine_.done();
  }

  py::tuple EncodeNumeric(int player, int unit_limit) const {
    CheckPlayer(player);
    if (unit_limit < 1) throw py::value_error("unit_limit must be positive");
    const int board_size = engine_.config().board_size;
    py::array_t<float> board(
        {2, actor::kBoardChannels, board_size, board_size});
    py::array_t<float> units({2, unit_limit, actor::kUnitFeat});
    py::array_t<float> global({actor::kGlobalFeat});
    {
      py::gil_scoped_release release;
      actor::EncodeEngineSeat(engine_, player, unit_limit, board.mutable_data(),
                              units.mutable_data(), global.mutable_data());
    }
    return py::make_tuple(std::move(board), std::move(units), std::move(global));
  }

  py::dict StepWithTrace(py::handle action0, py::handle action1) {
    const int max_orders = engine_.config().max_market_orders;
    const int step = engine_.step_index();
    const PlayerAction a0 = ParsePlayerAction(action0, max_orders);
    const PlayerAction a1 = ParsePlayerAction(action1, max_orders);
    std::vector<MarketSlotTrace> trace;
    engine_.Step(a0, a1, &trace);

    py::list market_trace;
    for (const MarketSlotTrace& entry : trace) {
      py::dict value;
      value["player"] = entry.player;
      value["slot_index"] = entry.slot_index;
      value["requested"] = entry.requested
                               ? py::object(pyconv::MarketOrderToPy(*entry.requested))
                               : py::object(py::none());
      value["actual"] = entry.actual
                            ? py::object(pyconv::MarketOrderToPy(*entry.actual))
                            : py::object(py::none());
      value["status"] = MarketOrderStatusName(entry.status);
      value["committed"] = entry.committed;
      value["money_before"] = entry.money_before;
      value["money_after"] = entry.money_after;
      value["shed_total_before"] = entry.shed_total_before;
      value["shed_total_after"] = entry.shed_total_after;
      market_trace.append(std::move(value));
    }

    const auto truncated = [max_orders](py::handle action) {
      if (!py::isinstance<py::dict>(action)) return 0;
      const auto payload = py::reinterpret_borrow<py::dict>(action);
      if (!payload.contains("market") || !py::isinstance<py::list>(payload["market"])) {
        return 0;
      }
      return std::max(0, static_cast<int>(py::len(payload["market"])) - max_orders);
    };
    py::list truncated_orders;
    truncated_orders.append(truncated(action0));
    truncated_orders.append(truncated(action1));

    py::dict result;
    result["step"] = step;
    result["done"] = engine_.done();
    result["market_trace"] = std::move(market_trace);
    result["truncated_orders"] = std::move(truncated_orders);
    return result;
  }

  py::dict Observation(int player) const {
    CheckPlayer(player);
    return ObservationToPy(engine_, player);
  }

  double Money(int player) const {
    CheckPlayer(player);
    return engine_.farm(player).money;
  }

  int64_t MarketPriceByName(const std::string& item_name, int64_t inventory) const {
    const int itm = pyconv::LookupItem(item_name, kNumProducts);
    if (itm < 0) throw py::value_error("unknown product: " + item_name);
    return engine_.MarketPrice(itm, inventory);
  }

  bool done() const { return engine_.done(); }
  int step_index() const { return engine_.step_index(); }
  py::dict Configuration() const { return ConfigToPy(engine_.config()); }

  const Engine& raw_engine() const { return engine_; }
  Engine& mutable_engine() { return engine_; }

 private:
  static int64_t CheckSeed(int64_t seed) {
    if (seed < 0) throw py::value_error("seed must be non-negative");
    return seed;
  }
  static void CheckPlayer(int player) {
    if (player < 0 || player > 1) throw py::value_error("player must be 0 or 1");
  }

  Engine engine_;
};

py::class_<PyEngine> BindEngine(py::module_& module);

}  // namespace kagg
