#include "kaito_v48.hpp"

#include <pybind11/numpy.h>
#include <pybind11/pybind11.h>

#include <cstdint>
#include <memory>
#include <stdexcept>

namespace py = pybind11;

namespace kagg::kaito {
namespace {

using IntArray =
    py::array_t<int64_t, py::array::c_style | py::array::forcecast>;

std::shared_ptr<Portfolio> MakePortfolio(
    IntArray tokens, IntArray quantities, IntArray decision_counts,
    IntArray unit_counts, int maximum_market_orders) {
  const py::buffer_info token_info = tokens.request();
  const py::buffer_info quantity_info = quantities.request();
  const py::buffer_info decision_info = decision_counts.request();
  const py::buffer_info unit_info = unit_counts.request();
  if (token_info.ndim != 3 || token_info.shape[0] != kRouteCount ||
      token_info.shape[1] != kRouteTurns || quantity_info.ndim != 3 ||
      quantity_info.shape != token_info.shape || decision_info.ndim != 2 ||
      decision_info.shape[0] != kRouteCount ||
      decision_info.shape[1] != kRouteTurns || unit_info.ndim != 2 ||
      unit_info.shape != decision_info.shape) {
    throw py::value_error(
        "Kaito v48 portfolio requires action arrays [6,719,D] and count "
        "arrays [6,719]");
  }
  return std::make_shared<Portfolio>(
      static_cast<const int64_t*>(token_info.ptr),
      static_cast<const int64_t*>(quantity_info.ptr),
      static_cast<const int64_t*>(decision_info.ptr),
      static_cast<const int64_t*>(unit_info.ptr),
      static_cast<int>(token_info.shape[2]), maximum_market_orders);
}

}  // namespace

void Bind(py::module_& module) {
  py::class_<Portfolio, std::shared_ptr<Portfolio>>(module,
                                                    "KaitoV48Portfolio")
      .def(py::init(&MakePortfolio), py::arg("tokens"), py::arg("quantities"),
           py::arg("decision_counts"), py::arg("unit_counts"),
           py::arg("maximum_market_orders"));
  py::class_<Session>(module, "KaitoV48Session")
      .def(py::init([](std::shared_ptr<Portfolio> portfolio) {
             return std::make_unique<Session>(std::move(portfolio));
           }),
           py::arg("portfolio"));
}

}  // namespace kagg::kaito
