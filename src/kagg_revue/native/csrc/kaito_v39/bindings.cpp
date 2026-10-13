#include "kaito_v39/runtime.hpp"

#include <pybind11/numpy.h>
#include <pybind11/pybind11.h>

#include <cstdint>
#include <memory>

namespace py = pybind11;

namespace kagg::kaito_v39 {
namespace {

using IntArray =
    py::array_t<int64_t, py::array::c_style | py::array::forcecast>;
using ByteArray =
    py::array_t<uint8_t, py::array::c_style | py::array::forcecast>;
using DoubleArray =
    py::array_t<double, py::array::c_style | py::array::forcecast>;

void RequireVector(const py::buffer_info& info, py::ssize_t count,
                   const char* name) {
  if (info.ndim != 1 || info.shape[0] != count) {
    throw py::value_error(std::string("Kaito v39 ") + name +
                          " must be a matching vector");
  }
}

void RequirePopulation(const py::buffer_info& index_info,
                       const py::buffer_info& margin_info,
                       const char* name) {
  if (index_info.ndim != 1 || index_info.shape[0] < 1 ||
      margin_info.ndim != 2 || margin_info.shape[0] != index_info.shape[0] ||
      margin_info.shape[1] != 2) {
    throw py::value_error(std::string("Kaito v39 ") + name +
                          " population arrays are invalid");
  }
}

std::shared_ptr<Portfolio> MakePortfolio(
    IntArray tokens, IntArray quantities, IntArray decision_counts,
    IntArray unit_counts, ByteArray parts_layout, DoubleArray parts_numeric,
    ByteArray parts_actor_lengths, ByteArray parts_unlocks,
    ByteArray parts_shop_counts, ByteArray parts_seats,
    IntArray nested_indices, DoubleArray nested_margins,
    IntArray fallback_indices, DoubleArray fallback_margins,
    IntArray stage1_indices, DoubleArray stage1_margins,
    IntArray stage2_indices, DoubleArray stage2_margins,
    int maximum_market_orders) {
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
        "Kaito v39 portfolio requires action arrays [4,719,D] and count "
        "arrays [4,719]");
  }

  const py::buffer_info layout_info = parts_layout.request();
  const py::buffer_info numeric_info = parts_numeric.request();
  if (layout_info.ndim != 2 || layout_info.shape[0] < 1 ||
      layout_info.shape[1] != kLayoutWidth || numeric_info.ndim != 2 ||
      numeric_info.shape[0] != layout_info.shape[0] ||
      numeric_info.shape[1] != kNumericWidth) {
    throw py::value_error("Kaito v39 public-state memory shape is invalid");
  }
  const py::ssize_t part_count = layout_info.shape[0];
  const py::buffer_info actor_info = parts_actor_lengths.request();
  const py::buffer_info unlock_info = parts_unlocks.request();
  const py::buffer_info shop_info = parts_shop_counts.request();
  const py::buffer_info seat_info = parts_seats.request();
  RequireVector(actor_info, part_count, "actor lengths");
  RequireVector(unlock_info, part_count, "unlock masks");
  RequireVector(seat_info, part_count, "seats");
  if (shop_info.ndim != 2 || shop_info.shape[0] != part_count ||
      shop_info.shape[1] != kNumShops) {
    throw py::value_error("Kaito v39 shop memory shape is invalid");
  }

  const py::buffer_info nested_index_info = nested_indices.request();
  const py::buffer_info nested_margin_info = nested_margins.request();
  const py::buffer_info fallback_index_info = fallback_indices.request();
  const py::buffer_info fallback_margin_info = fallback_margins.request();
  const py::buffer_info stage1_index_info = stage1_indices.request();
  const py::buffer_info stage1_margin_info = stage1_margins.request();
  const py::buffer_info stage2_index_info = stage2_indices.request();
  const py::buffer_info stage2_margin_info = stage2_margins.request();
  RequirePopulation(nested_index_info, nested_margin_info, "nested");
  RequirePopulation(fallback_index_info, fallback_margin_info, "fallback");
  RequirePopulation(stage1_index_info, stage1_margin_info, "stage1");
  if (stage2_index_info.ndim != 2 || stage2_index_info.shape[0] < 1 ||
      stage2_index_info.shape[1] != kHistoryCheckpoints ||
      stage2_margin_info.ndim != 2 ||
      stage2_margin_info.shape[0] != stage2_index_info.shape[0] ||
      stage2_margin_info.shape[1] != 2) {
    throw py::value_error("Kaito v39 stage2 history arrays are invalid");
  }
  return std::make_shared<Portfolio>(
      static_cast<const int64_t*>(token_info.ptr),
      static_cast<const int64_t*>(quantity_info.ptr),
      static_cast<const int64_t*>(decision_info.ptr),
      static_cast<const int64_t*>(unit_info.ptr),
      static_cast<int>(token_info.shape[2]), maximum_market_orders,
      static_cast<const uint8_t*>(layout_info.ptr),
      static_cast<const double*>(numeric_info.ptr),
      static_cast<const uint8_t*>(actor_info.ptr),
      static_cast<const uint8_t*>(unlock_info.ptr),
      static_cast<const uint8_t*>(shop_info.ptr),
      static_cast<const uint8_t*>(seat_info.ptr), static_cast<int>(part_count),
      static_cast<const int64_t*>(nested_index_info.ptr),
      static_cast<const double*>(nested_margin_info.ptr),
      static_cast<int>(nested_index_info.shape[0]),
      static_cast<const int64_t*>(fallback_index_info.ptr),
      static_cast<const double*>(fallback_margin_info.ptr),
      static_cast<int>(fallback_index_info.shape[0]),
      static_cast<const int64_t*>(stage1_index_info.ptr),
      static_cast<const double*>(stage1_margin_info.ptr),
      static_cast<int>(stage1_index_info.shape[0]),
      static_cast<const int64_t*>(stage2_index_info.ptr),
      static_cast<const double*>(stage2_margin_info.ptr),
      static_cast<int>(stage2_index_info.shape[0]));
}

}  // namespace

void Bind(py::module_& module) {
  py::class_<Portfolio, std::shared_ptr<Portfolio>>(module,
                                                    "KaitoV39Portfolio")
      .def(py::init(&MakePortfolio), py::arg("tokens"), py::arg("quantities"),
           py::arg("decision_counts"), py::arg("unit_counts"),
           py::arg("parts_layout"), py::arg("parts_numeric"),
           py::arg("parts_actor_lengths"), py::arg("parts_unlocks"),
           py::arg("parts_shop_counts"), py::arg("parts_seats"),
           py::arg("nested_indices"), py::arg("nested_margins"),
           py::arg("fallback_indices"), py::arg("fallback_margins"),
           py::arg("stage1_indices"), py::arg("stage1_margins"),
           py::arg("stage2_indices"), py::arg("stage2_margins"),
           py::arg("maximum_market_orders"));
  py::class_<Session>(module, "KaitoV39Session")
      .def(py::init([](std::shared_ptr<Portfolio> portfolio) {
             return std::make_unique<Session>(std::move(portfolio));
           }),
           py::arg("portfolio"));
}

}  // namespace kagg::kaito_v39
