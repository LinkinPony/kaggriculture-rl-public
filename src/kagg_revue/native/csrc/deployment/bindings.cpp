// Bind only the official-observation session required by the deployed actor.
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include "derived/features.hpp"
#include "parallel/deployment.hpp"
#include "parallel/context.hpp"
#include "production/features.hpp"

namespace py = pybind11;

PYBIND11_MODULE(_revue_observation, module) {
  module.doc() = "CPU official-observation execution without training or script opponents";
  module.attr("feature_version") = kagg::parallel::kGroundedObservationVersion;
  module.attr("feature_versions") = py::make_tuple(
      kagg::parallel::kGroundedObservationVersion, kagg::parallel::kContextObservationVersion,
      kagg::production::kVersion, kagg::derived::kVersion);
  // Module-local permits side-by-side qualification against the training binary.
  py::class_<kagg::parallel::ContractSession>(module, "ContractSession", py::module_local())
      .def(py::init<py::dict, int>())
      .def("update", &kagg::parallel::ContractSession::Update)
      .def("observe_into", &kagg::parallel::ContractSession::Observe)
      .def("set_program", &kagg::parallel::ContractSession::SetProgram)
      .def("program_action", &kagg::parallel::ContractSession::ProgramAction);
}
