#include "core/engine.hpp"

namespace kagg {

py::class_<PyEngine> BindEngine(py::module_& module) {
  return py::class_<PyEngine>(module, "Engine", py::module_local())
      .def(py::init<int64_t, py::object>(), py::arg("seed"),
           py::arg("configuration") = py::none(),
           "Create one episode. `seed` is the resolved episode seed "
           "(env.info['seed']); `configuration` accepts the official "
           "kaggle configuration dict.")
      .def("reset", &PyEngine::Reset, py::arg("seed"))
      .def("clone", &PyEngine::Clone,
           "Return an independent, step-exact copy of the current engine state.")
      .def("step", &PyEngine::Step, py::arg("action0"), py::arg("action1"),
           "Process one turn with both players' official-format action dicts; "
           "returns True when the episode is done.")
      .def("step_numeric", &PyEngine::StepNumeric, py::arg("tokens"),
           py::arg("quantities"), py::arg("decision_counts"),
           py::arg("unit_counts"),
           "Advance from fixed-width numeric action buffers without Python actions.")
      .def("step_mixed_numeric", &PyEngine::StepMixedNumeric,
           py::arg("numeric_player"), py::arg("tokens"), py::arg("quantities"),
           py::arg("decision_count"), py::arg("unit_count"),
           py::arg("other_action"),
           "Advance one numeric seat and one official Python-boundary seat.")
      .def("step_with_trace", &PyEngine::StepWithTrace, py::arg("action0"),
           py::arg("action1"),
           "Process one turn and return the exact realized market cash trace.")
      .def("observation", &PyEngine::Observation, py::arg("player"),
           "Full observation dict for `player` in the official format.")
      .def("encode_numeric", &PyEngine::EncodeNumeric, py::arg("player"),
           py::arg("unit_limit"),
           "Encode a seat directly from native state as contiguous numeric arrays.")
      .def("money", &PyEngine::Money, py::arg("player"))
      .def("market_price", &PyEngine::MarketPriceByName, py::arg("item"),
           py::arg("inventory"))
      .def_property_readonly("done", &PyEngine::done)
      .def_property_readonly("step_index", &PyEngine::step_index)
      .def_property_readonly(
          "configuration", &PyEngine::Configuration,
          "Fully resolved configuration actually used by the native engine.");
}

}  // namespace kagg
