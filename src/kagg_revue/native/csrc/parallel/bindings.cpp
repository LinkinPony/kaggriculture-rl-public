#include "parallel/batch.hpp"

#include <pybind11/stl.h>

#include "action_codec.hpp"
#include "actor_encoding.hpp"
#include "parallel/encoding.hpp"

namespace kagg::parallel {

void Bind(py::module_& module) {
  BindObservation(module);
  py::class_<Batch>(module, "ParallelBatch")
      .def(py::init<py::dict, std::vector<int64_t>, std::vector<int>,
                    std::vector<std::string>, py::list, py::list, int, int,
                    std::vector<int64_t>>())
      .def("observe_into", &Batch::Observe)
      .def("observe_selfplay_into", &Batch::ObserveSelfPlay)
      .def("teacher_into", &Batch::Teacher)
      .def("step", &Batch::Step)
      .def("advance", &Batch::Advance)
      .def("advance_programs", &Batch::AdvancePrograms, py::arg("plans"), py::arg("turns"),
           py::arg("capacity"), py::arg("selfplay") = false)
      .def("advance_selfplay", &Batch::AdvanceSelfPlay)
      .def("prepare_opponents", &Batch::PrepareOpponents)
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

}  // namespace kagg::parallel
