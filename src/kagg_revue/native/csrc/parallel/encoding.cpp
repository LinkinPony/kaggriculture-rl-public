#include "parallel/encoding.hpp"

#include <pybind11/stl.h>

#include "action_codec.hpp"
#include "actor_encoding.hpp"
#include "parallel/deployment.hpp"
#include "parallel/context.hpp"
#include "production/features.hpp"
#include "derived/features.hpp"

namespace kagg::parallel {
namespace py = pybind11;

void BindObservation(py::module_& module) {
  py::class_<ContractSession>(module, "ContractSession", py::module_local())
      .def(py::init<py::dict, int>())
      .def("update", &ContractSession::Update)
      .def("observe_into", &ContractSession::Observe)
      .def("encode_replay_into", &ContractSession::EncodeReplay)
      .def("action", &ContractSession::Action)
      .def("set_program", &ContractSession::SetProgram)
      .def("program_action", &ContractSession::ProgramAction);
  module.def("parallel_spec", [] {
    py::dict result;
    result["version"] = "parallel-official-turn-v1";
    result["entity_version"] = kEntityObservationVersion;
    result["grounded_version"] = kGroundedObservationVersion;
    result["agronomy_version"] = production::kVersion;
    result["agronomy_board_features"] = production::kBoardFeatures;
    result["agronomy_product_features"] = production::kProductFeatures;
    result["agronomy_global_features"] = production::kGlobalFeatures;
    result["agronomy_unit_features"] = production::kUnitFeatures;
    result["derived_version"] = derived::kVersion;
    result["derived_global_features"] = derived::kGlobalFeatures;
    result["derived_board_features"] = derived::kBoardFeatures;
    result["derived_unit_features"] = derived::kUnitFeatures;
    result["derived_product_features"] = derived::kProductFeatures;
    result["context_version"] = kContextObservationVersion;
    result["context_board_channels"] = kContextBoardChannels;
    result["context_product_features"] = kContextProductFeatures;
    result["context_global_features"] = kContextGlobalFeatures;
    result["context_history_tokens"] = kContextHistoryTokens;
    result["context_history_features"] = kContextHistoryFeatures;
    result["unit_support_features"] = kUnitSupportFeatures;
    result["product_features"] = kProductFeatures;
    result["history_features"] = kHistoryFeatures;
    result["board_channels"] = actor::kBoardChannels;
    result["unit_features"] = actor::kUnitFeat;
    result["global_features"] = actor::kGlobalFeat + kMaxShopInstances * kNumShops;
    result["unit_actions"] = policy::kUnitActionTokens;
    result["market_actions"] = policy::kMarketActionTokens;
    return result;
  });
}

}  // namespace kagg::parallel
