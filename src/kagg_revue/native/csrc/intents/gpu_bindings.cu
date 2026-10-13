#include "intents/gpu_kernels.hpp"

#include <cuda_runtime.h>

#include <cstdint>
#include <stdexcept>
#include <string>

#include <pybind11/pybind11.h>

namespace py = pybind11;

namespace kagg::intents::gpu {
namespace {

template <typename T>
T* Pointer(const py::dict& values, const char* name) {
  const uintptr_t address = py::cast<uintptr_t>(values[py::str(name)]);
  if (address == 0) {
    throw std::invalid_argument(std::string("intent CUDA pointer is null: ") +
                                name);
  }
  return reinterpret_cast<T*>(address);
}

int Integer(const py::dict& values, const char* name) {
  const int value = py::cast<int>(values[py::str(name)]);
  if (value < 1) {
    throw std::invalid_argument(std::string("intent CUDA dimension is invalid: ") +
                                name);
  }
  return value;
}

Buffers ParseBuffers(const py::dict& values) {
  return Buffers{
      .candidate_fields = Pointer<int64_t>(values, "candidate_fields"),
      .candidate_features = Pointer<float>(values, "candidate_features"),
      .candidate_mask = Pointer<bool>(values, "candidate_mask"),
      .candidate_counts = Pointer<int64_t>(values, "candidate_counts"),
      .ledger = Pointer<int64_t>(values, "ledger"),
      .status = Pointer<int64_t>(values, "status"),
      .work_priorities = Pointer<int64_t>(values, "work_priorities"),
      .status_deadline = Pointer<int64_t>(values, "status_deadline"),
      .inactive_status = Pointer<int64_t>(values, "inactive_status"),
      .asset_risk = Pointer<bool>(values, "asset_risk"),
      .work_orders = Pointer<int64_t>(values, "work_orders"),
      .work_mask = Pointer<bool>(values, "work_mask"),
      .work_scratch = Pointer<int64_t>(values, "work_scratch"),
      .work_mask_scratch = Pointer<bool>(values, "work_mask_scratch"),
      .work_removed_fields =
          Pointer<int64_t>(values, "work_removed_fields"),
      .work_removed_mask = Pointer<bool>(values, "work_removed_mask"),
      .work_added_fields = Pointer<int64_t>(values, "work_added_fields"),
      .work_added_mask = Pointer<bool>(values, "work_added_mask"),
      .work_mutation = Pointer<int64_t>(values, "work_mutation"),
      .work_priority_target =
          Pointer<int64_t>(values, "work_priority_target"),
      .positions = Pointer<int64_t>(values, "positions"),
      .market_prefix = Pointer<int64_t>(values, "market_prefix"),
      .market_mask = Pointer<bool>(values, "market_mask"),
      .economic = Pointer<int32_t>(values, "economic"),
      .carried = Pointer<int64_t>(values, "carried"),
      .unit_inventories = Pointer<int64_t>(values, "unit_inventories"),
      .shed = Pointer<int64_t>(values, "shed"),
      .unit_positions = Pointer<int64_t>(values, "unit_positions"),
      .owned = Pointer<int64_t>(values, "owned"),
      .tiles = Pointer<int64_t>(values, "tiles"),
      .work_applies = Pointer<bool>(values, "work_applies"),
      .market_product_ratio =
          Pointer<double>(values, "market_product_ratio"),
      .phase = Pointer<int64_t>(values, "phase"),
      .active = Pointer<bool>(values, "active"),
      .pending_kind = Pointer<int64_t>(values, "pending_kind"),
      .pending_target = Pointer<int64_t>(values, "pending_target"),
      .pending_role = Pointer<int64_t>(values, "pending_role"),
      .pending_unit = Pointer<int64_t>(values, "pending_unit"),
      .pending_directive_operation =
          Pointer<int64_t>(values, "pending_directive_operation"),
      .pending_item = Pointer<int64_t>(values, "pending_item"),
      .pending_quantity = Pointer<int64_t>(values, "pending_quantity"),
      .pending_market_kind =
          Pointer<int64_t>(values, "pending_market_kind"),
      .pending_market_item =
          Pointer<int64_t>(values, "pending_market_item"),
      .pending_market_upper =
          Pointer<int64_t>(values, "pending_market_upper"),
      .last_ledger_key = Pointer<int64_t>(values, "last_ledger_key"),
      .market_phase = Pointer<bool>(values, "market_phase"),
      .trace_counts = Pointer<int64_t>(values, "trace_counts"),
      .trace_selected = Pointer<int64_t>(values, "trace_selected"),
      .trace_fields = Pointer<int64_t>(values, "trace_fields"),
      .trace_log_probability =
          Pointer<float>(values, "trace_log_probability"),
      .trace_value = Pointer<float>(values, "trace_value"),
      .live_candidate_count =
          Pointer<int64_t>(values, "live_candidate_count"),
      .live_batch_count = Pointer<int64_t>(values, "live_batch_count"),
      .decision_variant = Pointer<int64_t>(values, "decision_variant"),
      .phase_variants = Pointer<int64_t>(values, "phase_variants"),
      .ledger_dirty_target =
          Pointer<int64_t>(values, "ledger_dirty_target"),
      .position_dirty_role =
          Pointer<int64_t>(values, "position_dirty_role"),
      .market_dirty_slot = Pointer<int64_t>(values, "market_dirty_slot"),
  };
}

Dimensions ParseDimensions(const py::dict& values) {
  return Dimensions{
      .batch = Integer(values, "batch"),
      .board_size = Integer(values, "board_size"),
      .cells = Integer(values, "cells"),
      .unit_limit = Integer(values, "unit_limit"),
      .work_capacity = Integer(values, "work_capacity"),
      .market_capacity = Integer(values, "market_capacity"),
      .economic_width = Integer(values, "economic_width"),
      .seeds_offset = Integer(values, "seeds_offset"),
      .tile_fields = Integer(values, "tile_fields"),
      .candidate_capacity = Integer(values, "candidate_capacity"),
      .trace_capacity = Integer(values, "trace_capacity"),
      .maximum_steps = Integer(values, "maximum_steps"),
      .episode_steps = Integer(values, "episode_steps"),
      .turns_per_day = Integer(values, "turns_per_day"),
  };
}

class IntentTransactionKernels {
 public:
  IntentTransactionKernels(const py::dict& pointers,
                           const py::dict& dimensions)
      : buffers_(ParseBuffers(pointers)),
        dimensions_(ParseDimensions(dimensions)) {}

  void Candidates(uintptr_t stream, int capacity) {
    if (capacity < 1 || capacity > dimensions_.candidate_capacity) {
      throw std::invalid_argument("intent candidate launch is invalid");
    }
    LaunchCandidates(buffers_, dimensions_, capacity,
                     reinterpret_cast<cudaStream_t>(stream));
  }

  void Transition(uintptr_t stream, uintptr_t candidate_fields,
                  uintptr_t selected, uintptr_t log_probability,
                  uintptr_t value) {
    if (candidate_fields == 0 || selected == 0 ||
        log_probability == 0 || value == 0) {
      throw std::invalid_argument("intent transition launch is invalid");
    }
    LaunchTransition(
        buffers_, dimensions_, reinterpret_cast<const int64_t*>(candidate_fields),
        reinterpret_cast<const int64_t*>(selected),
        reinterpret_cast<const float*>(log_probability),
        reinterpret_cast<const float*>(value),
        reinterpret_cast<cudaStream_t>(stream));
  }

 private:
  Buffers buffers_;
  Dimensions dimensions_;
};

}  // namespace
}  // namespace kagg::intents::gpu

PYBIND11_MODULE(_intent_cuda, module) {
  py::class_<kagg::intents::gpu::IntentTransactionKernels>(
      module, "IntentTransactionKernels")
      .def(py::init<const py::dict&, const py::dict&>(), py::arg("pointers"),
           py::arg("dimensions"))
      .def("candidates",
           &kagg::intents::gpu::IntentTransactionKernels::Candidates,
           py::arg("stream"), py::arg("capacity"))
      .def("transition",
           &kagg::intents::gpu::IntentTransactionKernels::Transition,
           py::arg("stream"), py::arg("candidate_fields"),
           py::arg("selected"), py::arg("log_probability"),
           py::arg("value"));
}
