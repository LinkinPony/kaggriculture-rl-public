// Neural self-play exposes no teacher or built-in script construction.
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include <stdexcept>

#include "core/engine.hpp"
#include "parallel/batch.hpp"
#include "parallel/encoding.hpp"

namespace py = pybind11;

PYBIND11_MODULE(_revue_core, module) {
  module.doc() = "Official rules and neural self-play without script strategies";
  module.attr("runtime_kind") = "neural-selfplay-only-v1";
  kagg::BindEngine(module);
  kagg::parallel::BindObservation(module);
  using kagg::parallel::Batch;
  py::class_<Batch>(module, "SelfPlayBatch", py::module_local())
      .def(py::init<py::dict, std::vector<int64_t>, std::vector<int>, int, int,
                    std::vector<int64_t>>())
      .def("observe_into", &Batch::Observe)
      .def("observe_selfplay_into", &Batch::ObserveSelfPlay)
      .def("advance_programs",
           [](Batch& batch, py::array plans, int turns, int capacity, bool selfplay) {
             if (!selfplay) throw std::invalid_argument("core batches require neural self-play");
             batch.AdvancePrograms(plans, turns, capacity, true);
           }, py::arg("plans"), py::arg("turns"), py::arg("capacity"),
           py::arg("selfplay") = true)
      .def("advance_selfplay", &Batch::AdvanceSelfPlay)
      .def("fork", &Batch::Fork)
      .def("replay_prefixes", &Batch::ReplayPrefixes)
      .def("cash", &Batch::Cash)
      .def("observation", &Batch::Observation, py::arg("lane"), py::arg("player") = -1)
      .def("action", &Batch::Action)
      .def("contract_action", &Batch::ContractAction,
           py::arg("lane"), py::arg("contracts"), py::arg("player") = -1)
      .def_property_readonly("completed_games", &Batch::completed)
      .def_property_readonly("transitions", &Batch::transitions)
      .def_property_readonly("features", &Batch::features)
      .def_property_readonly("entity_features", &Batch::entity_features)
      .def_property_readonly("slots", &Batch::slots)
      .def_property_readonly("step_index", &Batch::step);
}
