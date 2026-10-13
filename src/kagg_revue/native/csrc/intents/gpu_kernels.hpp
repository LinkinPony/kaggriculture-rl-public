#pragma once

#include <cuda_runtime.h>

#include <cstdint>

namespace kagg::intents::gpu {

struct Buffers {
  int64_t* candidate_fields;
  float* candidate_features;
  bool* candidate_mask;
  int64_t* candidate_counts;

  int64_t* ledger;
  int64_t* status;
  int64_t* work_priorities;
  int64_t* status_deadline;
  int64_t* inactive_status;
  bool* asset_risk;
  int64_t* work_orders;
  bool* work_mask;
  int64_t* work_scratch;
  bool* work_mask_scratch;
  int64_t* work_removed_fields;
  bool* work_removed_mask;
  int64_t* work_added_fields;
  bool* work_added_mask;
  int64_t* work_mutation;
  int64_t* work_priority_target;
  int64_t* positions;
  int64_t* market_prefix;
  bool* market_mask;

  int32_t* economic;
  int64_t* carried;
  int64_t* unit_inventories;
  int64_t* shed;
  int64_t* unit_positions;
  int64_t* owned;
  int64_t* tiles;
  bool* work_applies;
  double* market_product_ratio;

  int64_t* phase;
  bool* active;
  int64_t* pending_kind;
  int64_t* pending_target;
  int64_t* pending_role;
  int64_t* pending_unit;
  int64_t* pending_directive_operation;
  int64_t* pending_item;
  int64_t* pending_quantity;
  int64_t* pending_market_kind;
  int64_t* pending_market_item;
  int64_t* pending_market_upper;
  int64_t* last_ledger_key;
  bool* market_phase;

  int64_t* trace_counts;
  int64_t* trace_selected;
  int64_t* trace_fields;
  float* trace_log_probability;
  float* trace_value;
  int64_t* live_candidate_count;
  int64_t* live_batch_count;
  int64_t* decision_variant;
  int64_t* phase_variants;

  int64_t* ledger_dirty_target;
  int64_t* position_dirty_role;
  int64_t* market_dirty_slot;
};

struct Dimensions {
  int batch;
  int board_size;
  int cells;
  int unit_limit;
  int work_capacity;
  int market_capacity;
  int economic_width;
  int seeds_offset;
  int tile_fields;
  int candidate_capacity;
  int trace_capacity;
  int maximum_steps;
  int episode_steps;
  int turns_per_day;
};

void LaunchCandidates(const Buffers& buffers, const Dimensions& dimensions,
                      int capacity, cudaStream_t stream);

void LaunchTransition(const Buffers& buffers, const Dimensions& dimensions,
                      const int64_t* candidate_fields,
                      const int64_t* selected,
                      const float* log_probability, const float* value,
                      cudaStream_t stream);

}  // namespace kagg::intents::gpu
