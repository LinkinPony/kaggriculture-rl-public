// High-throughput numeric policy boundary for native rollouts.

#include <pybind11/numpy.h>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include <cstdint>
#include <initializer_list>
#include <stdexcept>
#include <vector>

#include "action_codec.hpp"
#include "actor_encoding.hpp"
#include "derived_facts.hpp"
#include "engine.hpp"
#include "py_convert.hpp"
#include "policy_session.hpp"

namespace py = pybind11;

namespace kagg {
namespace {

using IntArray =
    py::array_t<int64_t, py::array::c_style | py::array::forcecast>;

template <typename T>
py::array_t<T> MakeArray(std::initializer_list<py::ssize_t> shape) {
  return py::array_t<T>(std::vector<py::ssize_t>(shape));
}

void CheckActionBuffers(const py::buffer_info& tokens,
                        const py::buffer_info& quantities,
                        const py::buffer_info& decisions,
                        const py::buffer_info& units, int batch_size) {
  if (tokens.ndim != 3 || tokens.shape[0] != batch_size || tokens.shape[1] != 2 ||
      quantities.ndim != 3 || quantities.shape != tokens.shape ||
      decisions.ndim != 2 || decisions.shape[0] != batch_size ||
      decisions.shape[1] != 2 || units.ndim != 2 || units.shape != decisions.shape) {
    throw py::value_error(
        "batch actions require tokens/quantities [B,2,D] and counts [B,2]");
  }
}

py::dict ActionCodecSpec() {
  py::dict result;
  result["version"] = policy::kActionCodecVersion;
  result["unit_tokens"] = policy::kUnitActionTokens;
  result["market_tokens"] = policy::kMarketActionTokens;
  result["tokens"] = policy::kActionTokens;
  result["market_stop_token"] = policy::kMarketStopToken;
  result["keys"] = policy::ActionTokenKeys();
  py::array_t<uint8_t> quantity = MakeArray<uint8_t>({policy::kActionTokens});
  for (int token = 0; token < policy::kActionTokens; ++token) {
    quantity.mutable_at(token) = policy::TokenHasQuantity(token) ? 1 : 0;
  }
  result["has_quantity"] = std::move(quantity);
  return result;
}

py::dict DerivedFactSpec() {
  py::dict result;
  result["version"] = facts::kDerivedFactVersion;
  result["turn_features"] = facts::kTurnFactFeatures;
  result["prefix_features"] = facts::kPrefixFactFeatures;
  result["candidate_features"] = facts::kCandidateFactFeatures;
  result["products"] = kNumProducts;
  result["turn_feature_names"] = facts::TurnFactNames();
  result["prefix_feature_names"] = facts::PrefixFactNames();
  result["candidate_feature_names"] = facts::CandidateFactNames();
  result["semantics"] =
      "policy-neutral exact facts; market projections are explicitly conditional";
  result["matching_semantics"] =
      "one-task-per-unit reachability relaxation; shared resources are not "
      "reserved; not a schedule or policy";
  return result;
}

py::dict DecodeActionTokens(IntArray tokens, IntArray quantities, int decision_count,
                            int unit_count, int max_market_orders) {
  const py::buffer_info token_info = tokens.request();
  const py::buffer_info quantity_info = quantities.request();
  if (token_info.ndim != 1 || quantity_info.ndim != 1 ||
      quantity_info.shape != token_info.shape || decision_count < 0 ||
      decision_count > token_info.shape[0]) {
    throw py::value_error("action tokens and quantities must be matching vectors");
  }
  const PlayerAction action = policy::DecodePlayerAction(
      static_cast<const int64_t*>(token_info.ptr),
      static_cast<const int64_t*>(quantity_info.ptr), decision_count, unit_count,
      max_market_orders);
  return pyconv::PlayerActionToPy(action);
}

class NativeEngineBatch {
 public:
  NativeEngineBatch(IntArray seeds, py::object configuration)
      : config_(pyconv::ParseConfig(configuration)) {
    Reset(std::move(seeds));
  }

  void Reset(IntArray seeds) {
    const py::buffer_info info = seeds.request();
    if (info.ndim != 1 || info.shape[0] < 1) {
      throw py::value_error("seeds must be a nonempty vector");
    }
    const auto* values = static_cast<const int64_t*>(info.ptr);
    engines_.clear();
    engines_.reserve(static_cast<size_t>(info.shape[0]));
    for (py::ssize_t index = 0; index < info.shape[0]; ++index) {
      if (values[index] < 0) throw py::value_error("seeds must be non-negative");
      engines_.emplace_back(config_, values[index]);
    }
  }

  py::tuple Encode(int unit_limit) const {
    if (unit_limit < 1) throw py::value_error("unit_limit must be positive");
    const py::ssize_t batch = static_cast<py::ssize_t>(engines_.size());
    const int board_size = config_.board_size;
    py::array_t<float> board = MakeArray<float>(
        {batch, 2, 2, actor::kBoardChannels, board_size, board_size});
    py::array_t<float> units =
        MakeArray<float>({batch, 2, 2, unit_limit, actor::kUnitFeat});
    py::array_t<float> global =
        MakeArray<float>({batch, 2, actor::kGlobalFeat});
    const size_t board_stride = static_cast<size_t>(2) * actor::kBoardChannels *
                                board_size * board_size;
    const size_t unit_stride =
        static_cast<size_t>(2) * unit_limit * actor::kUnitFeat;
    const size_t global_stride = actor::kGlobalFeat;
    {
      py::gil_scoped_release release;
      for (size_t environment = 0; environment < engines_.size(); ++environment) {
        for (int player = 0; player < 2; ++player) {
          const size_t seat = environment * 2 + player;
          actor::EncodeEngineSeat(
              engines_[environment], player, unit_limit,
              board.mutable_data() + seat * board_stride,
              units.mutable_data() + seat * unit_stride,
              global.mutable_data() + seat * global_stride);
        }
      }
    }
    return py::make_tuple(std::move(board), std::move(units), std::move(global));
  }

  py::array_t<uint8_t> Step(IntArray tokens, IntArray quantities,
                            IntArray decision_counts, IntArray unit_counts) {
    const py::buffer_info token_info = tokens.request();
    const py::buffer_info quantity_info = quantities.request();
    const py::buffer_info decision_info = decision_counts.request();
    const py::buffer_info unit_info = unit_counts.request();
    const int batch = static_cast<int>(engines_.size());
    CheckActionBuffers(token_info, quantity_info, decision_info, unit_info, batch);
    const auto* token_data = static_cast<const int64_t*>(token_info.ptr);
    const auto* quantity_data = static_cast<const int64_t*>(quantity_info.ptr);
    const auto* decisions = static_cast<const int64_t*>(decision_info.ptr);
    const auto* units = static_cast<const int64_t*>(unit_info.ptr);
    const int width = static_cast<int>(token_info.shape[2]);
    py::array_t<uint8_t> done = MakeArray<uint8_t>({batch});
    auto* done_data = done.mutable_data();
    {
      py::gil_scoped_release release;
      for (int environment = 0; environment < batch; ++environment) {
        Engine& engine = engines_[environment];
        if (!engine.done()) {
          std::array<PlayerAction, 2> actions;
          for (int player = 0; player < 2; ++player) {
            const int seat = environment * 2 + player;
            const int64_t decisions_value = decisions[seat];
            const int64_t units_value = units[seat];
            if (decisions_value < 0 || decisions_value > width || units_value < 1 ||
                units_value > decisions_value) {
              throw std::invalid_argument("numeric action counts are invalid");
            }
            const size_t offset = static_cast<size_t>(seat) * width;
            actions[player] = policy::DecodePlayerAction(
                token_data + offset, quantity_data + offset,
                static_cast<int>(decisions_value), static_cast<int>(units_value),
                config_.max_market_orders);
          }
          engine.Step(actions[0], actions[1]);
        }
        done_data[environment] = engine.done() ? 1 : 0;
      }
    }
    return done;
  }

  py::array_t<double> Money() const {
    const py::ssize_t batch = static_cast<py::ssize_t>(engines_.size());
    py::array_t<double> result = MakeArray<double>({batch, 2});
    for (py::ssize_t environment = 0; environment < batch; ++environment) {
      result.mutable_at(environment, 0) = engines_[environment].farm(0).money;
      result.mutable_at(environment, 1) = engines_[environment].farm(1).money;
    }
    return result;
  }

  int size() const { return static_cast<int>(engines_.size()); }

 private:
  Config config_;
  std::vector<Engine> engines_;
};

}  // namespace

void BindPolicyIo(py::module_& module) {
  module.def("action_codec_spec", &ActionCodecSpec,
             "Return the fixed numeric action vocabulary and quantity mask.");
  module.def("derived_fact_spec", &DerivedFactSpec,
             "Return the DerivedFact-v1 tensor contract.");
  module.def("decode_action_tokens", &DecodeActionTokens, py::arg("tokens"),
             py::arg("quantities"), py::arg("decision_count"),
             py::arg("unit_count"), py::arg("max_market_orders"),
             "Convert one numeric action to the official boundary format.");
  py::class_<NativeEngineBatch>(module, "EngineBatch")
      .def(py::init<IntArray, py::object>(), py::arg("seeds"),
           py::arg("configuration") = py::none())
      .def("reset", &NativeEngineBatch::Reset, py::arg("seeds"))
      .def("encode", &NativeEngineBatch::Encode, py::arg("unit_limit"))
      .def("step", &NativeEngineBatch::Step, py::arg("tokens"),
           py::arg("quantities"), py::arg("decision_counts"),
           py::arg("unit_counts"))
      .def("money", &NativeEngineBatch::Money)
      .def_property_readonly("size", &NativeEngineBatch::size);
  BindPolicySession(module);
}

}  // namespace kagg
