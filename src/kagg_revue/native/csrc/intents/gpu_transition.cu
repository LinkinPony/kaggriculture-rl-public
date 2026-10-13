#include "intents/gpu_kernels.hpp"

#include <cub/block/block_scan.cuh>
#include <cuda_runtime.h>

#include <algorithm>
#include <cstdint>
#include <stdexcept>
#include <string>

namespace kagg::intents::gpu {
namespace {

constexpr int kItems = 12;
constexpr int kCrops = 5;
constexpr int kFertilizer = 8;
constexpr int kCandidateFields = 10;
constexpr int kLedgerFields = 8;
constexpr int kStatusFields = 4;
constexpr int kWorkFields = 9;
constexpr int kPositionFields = 4;
constexpr int kMarketFields = 3;

enum Phase : int64_t {
  kRoot = 0,
  kAssetTarget = 1,
  kAssetProfile = 2,
  kCancelAsset = 3,
  kWorkTarget = 4,
  kWorkProfile = 5,
  kCancelWork = 6,
  kPositionRole = 7,
  kPositionTarget = 8,
  kCancelPosition = 9,
  kStoreItem = 10,
  kStoreQuantity = 11,
  kStorePriority = 12,
  kMarketQuantity = 13,
  kFetchUnit = 14,
  kFetchItem = 15,
  kFetchQuantity = 16,
  kCancelFetch = 17,
  kDirectiveUnit = 18,
  kDirectiveOperation = 19,
  kDirectiveTarget = 20,
  kDirectiveItem = 21,
  kDirectiveQuantity = 22,
  kCancelDirective = 23,
  kDone = 24,
};

enum Choice : int64_t {
  kCommit = 0,
  kBeginAsset = 1,
  kBeginCancelAsset = 2,
  kBeginWork = 3,
  kBeginCancelWork = 4,
  kBeginPosition = 5,
  kBeginCancelPosition = 6,
  kBeginStore = 7,
  kSelectTarget = 8,
  kSetAsset = 9,
  kCancelAssetChoice = 10,
  kAddWork = 11,
  kCancelWorkChoice = 12,
  kSelectRole = 13,
  kSetPosition = 14,
  kCancelPositionChoice = 15,
  kSelectStoreItem = 16,
  kSelectStoreQuantity = 17,
  kAddStore = 18,
  kMarketSell = 19,
  kMarketBuySeed = 20,
  kMarketBuyProduct = 21,
  kMarketBuyAnimal = 22,
  kMarketHire = 23,
  kMarketBuyLand = 24,
  kSelectMarketQuantity = 25,
  kBeginFetch = 26,
  kBeginCancelFetch = 27,
  kSelectFetchUnit = 28,
  kSelectFetchItem = 29,
  kSetFetch = 30,
  kCancelFetchChoice = 31,
  kBeginDirective = 32,
  kBeginCancelDirective = 33,
  kSelectDirectiveUnit = 34,
  kSelectDirectiveOperation = 35,
  kSelectDirectiveTarget = 36,
  kSelectDirectiveItem = 37,
  kSetDirective = 38,
  kCancelDirectiveChoice = 39,
  kMarketSkipSlot = 40,
};

constexpr int64_t kDirectiveWait = 2;
constexpr int64_t kDoneMarketKind = 6;
constexpr int64_t kEmpty = 0;
constexpr int64_t kLocked = 1;
constexpr int64_t kWeed = 2;
constexpr int64_t kPlant = 3;
constexpr int64_t kStructure = 4;
constexpr int64_t kStatusPending = 1;
constexpr int64_t kStatusRunning = 2;
constexpr int64_t kStatusBlocked = 3;
constexpr int64_t kStatusAtRisk = 4;
constexpr int64_t kStatusSatisfied = 5;
constexpr int64_t kReasonLandLocked = 1;
constexpr int64_t kReasonConflictingAsset = 2;
constexpr int64_t kReasonSeedShortfall = 3;
constexpr int64_t kReasonAnimalShortfall = 4;
constexpr int64_t kReasonWheatShortfall = 5;
constexpr int64_t kReasonFertilizerShortfall = 6;
constexpr int64_t kReasonShedCapacity = 8;
constexpr int64_t kReasonShedItemShortfall = 10;

__device__ __forceinline__ int Clamp(int value, int low, int high) {
  return max(low, min(value, high));
}

__device__ __forceinline__ int64_t WorkKey(const Dimensions& dimensions,
                                           const int64_t* fields) {
  const int64_t kind = fields[0];
  if (kind == 8) {
    return dimensions.cells * 16 + 2 + fields[2] - 1;
  }
  if (kind == 9) {
    return dimensions.cells * 16 + 2 + kItems + fields[8] - 1;
  }
  if (kind >= 10) {
    return dimensions.cells * 16 + 2 + kItems + 256 + fields[8] - 1;
  }
  return fields[1] * 16 + 1 + kind;
}

__device__ void UpdateStatus(const Buffers& buffers,
                             const Dimensions& dimensions, int row,
                             int target) {
  int64_t* output =
      buffers.status +
      (row * dimensions.cells + target) * kStatusFields;
  const int64_t* ledger =
      buffers.ledger +
      (row * dimensions.cells + target) * kLedgerFields;
  const int64_t* tile =
      buffers.tiles +
      (row * dimensions.cells + target) * dimensions.tile_fields;
  const int item = Clamp(static_cast<int>(ledger[2] - 1), 0, kItems - 1);
  const int tile_kind = static_cast<int>(tile[0]);
  const bool plant = tile_kind == kPlant;
  const bool animal = tile_kind == kStructure && tile[7] != 0;
  const bool crop_contract = ledger[1] == 1;
  const bool animal_contract = ledger[1] == 2;
  const int64_t owned = buffers.owned[row * kItems + item];
  const int crop_item = Clamp(item, 0, kCrops - 1);
  const int32_t* economic = buffers.economic + row * dimensions.economic_width;
  const int64_t seeds = economic[dimensions.seeds_offset + crop_item];
  const bool matches =
      (crop_contract && plant && item == tile[1]) ||
      (animal_contract && animal && item == 9 + tile[8]);
  const bool active = ledger[0] != 0;
  const bool risk = matches && buffers.asset_risk[row * dimensions.cells + target];
  const int inactive_offset = (row * dimensions.cells + target) * 2;
  int64_t status = buffers.inactive_status[inactive_offset];
  int64_t reason = buffers.inactive_status[inactive_offset + 1];
  int64_t shortfall = 0;
  if (matches) status = risk ? kStatusAtRisk : kStatusSatisfied;
  const bool wheat_shortfall =
      risk && animal_contract && buffers.owned[row * kItems] <= 0;
  if (wheat_shortfall) {
    reason = kReasonWheatShortfall;
    shortfall = 1;
  }
  const bool land_locked = active && !matches && tile_kind == kLocked;
  const bool seed_shortfall = active && !matches && crop_contract &&
                              tile_kind == kEmpty && seeds <= 0;
  const bool animal_shortfall =
      active && !matches && animal_contract && tile_kind == kStructure &&
      !animal && owned <= 0;
  const bool runnable =
      active && !matches &&
      (tile_kind == kEmpty || tile_kind == kWeed ||
       (tile_kind == kStructure && !animal));
  const bool conflict = active && !matches && !land_locked &&
                        !seed_shortfall && !animal_shortfall && !runnable;
  if (land_locked) {
    status = kStatusBlocked;
    reason = kReasonLandLocked;
  }
  if (seed_shortfall) {
    status = kStatusBlocked;
    reason = kReasonSeedShortfall;
    shortfall = item + 1;
  }
  if (animal_shortfall) {
    status = kStatusBlocked;
    reason = kReasonAnimalShortfall;
    shortfall = item + 1;
  }
  if (runnable) status = kStatusRunning;
  if (conflict) {
    status = kStatusBlocked;
    reason = kReasonConflictingAsset;
  }
  output[0] = status;
  output[1] = reason;
  output[2] = shortfall;
  output[3] = buffers.status_deadline[row * dimensions.cells + target];
}

__device__ void UpdatePriorities(const Buffers& buffers,
                                 const Dimensions& dimensions, int row,
                                 int target) {
  int64_t* output =
      buffers.work_priorities + (row * dimensions.cells + target) * 8;
  for (int kind = 0; kind < 8; ++kind) output[kind] = -1;
  for (int work = 0; work < dimensions.work_capacity; ++work) {
    if (!buffers.work_mask[row * dimensions.work_capacity + work]) continue;
    const int64_t* fields =
        buffers.work_orders +
        (row * dimensions.work_capacity + work) * kWorkFields;
    if (fields[0] >= 0 && fields[0] < 8 && fields[1] == target) {
      output[fields[0]] = max(output[fields[0]], fields[4]);
    }
  }
}

__device__ void NewWorkStatus(const Buffers& buffers,
                              const Dimensions& dimensions, int row,
                              const int64_t* choice, int64_t* status) {
  const int kind = static_cast<int>(choice[2] - 1);
  const int target = Clamp(static_cast<int>(choice[1]), 0,
                           dimensions.cells - 1);
  const int64_t* tile =
      buffers.tiles +
      (row * dimensions.cells + target) * dimensions.tile_fields;
  const int tile_kind = static_cast<int>(tile[0]);
  const bool animal = tile_kind == kStructure && tile[7] != 0;
  const int crop = Clamp(static_cast<int>(tile[1]), 0, kCrops - 1);
  constexpr int64_t first_yield[kCrops] = {2, 2, 8, 10, 10};
  const int32_t* economic = buffers.economic + row * dimensions.economic_width;
  const int64_t day = economic[0];
  bool ready = false;
  ready |= kind == 0 && tile_kind == kPlant && tile[5] > 0 &&
           day - tile[2] >= first_yield[crop];
  ready |= kind == 1 && tile_kind == kPlant;
  ready |= kind == 2 && animal && tile[10] == 0;
  ready |= kind == 3 && animal && tile[5] > 0;
  ready |= kind == 4 && animal && tile[11] != 0;
  ready |= kind == 5 && tile_kind != kEmpty && tile_kind != kLocked &&
           !animal;
  ready |= kind == 6 && tile_kind == kPlant && tile[3] == 0;
  ready |= kind == 7 && animal && tile[9] == 0;
  ready |= kind == 8;
  status[0] = ready ? kStatusRunning : kStatusPending;
  status[1] = 0;
  const bool store_blocked = kind == 8 && economic[8] >= economic[5];
  const bool feed_blocked =
      kind == 7 && buffers.owned[row * kItems] <= 0;
  const bool fertilizer_blocked =
      kind == 1 && buffers.owned[row * kItems + kFertilizer] <= 0;
  if (store_blocked || feed_blocked || fertilizer_blocked) {
    status[0] = kStatusBlocked;
  }
  if (store_blocked) status[1] = kReasonShedCapacity;
  if (feed_blocked) status[1] = kReasonWheatShortfall;
  if (fertilizer_blocked) status[1] = kReasonFertilizerShortfall;
}

enum class WorkMutation {
  kNone,
  kAddWork,
  kCancelWork,
  kAddStore,
  kSetFetch,
  kCancelFetch,
  kSetDirective,
  kCancelDirective,
};

__device__ bool RemoveWork(WorkMutation mutation, const int64_t* existing,
                           const int64_t* choice, const int64_t* appended) {
  switch (mutation) {
    case WorkMutation::kAddWork:
      return existing[0] == appended[0] && existing[1] == appended[1];
    case WorkMutation::kCancelWork: {
      const int64_t kind = choice[2] - 1;
      return existing[0] == kind &&
             (kind == 8 ? existing[2] == choice[3]
                        : existing[1] == choice[1]);
    }
    case WorkMutation::kAddStore:
      return existing[0] == 8 && existing[2] == appended[2];
    case WorkMutation::kSetFetch:
    case WorkMutation::kCancelFetch:
      return existing[0] == 9 && existing[8] == choice[8];
    case WorkMutation::kSetDirective:
    case WorkMutation::kCancelDirective:
      return existing[0] >= 10 && existing[8] == choice[8];
    case WorkMutation::kNone:
      return false;
  }
  return false;
}

__device__ void CopyWork(int64_t* destination, const int64_t* source) {
  for (int field = 0; field < kWorkFields; ++field) {
    destination[field] = source[field];
  }
}

__device__ void ScheduleWorkMutation(const Buffers& buffers, int row,
                                     WorkMutation mutation,
                                     const int64_t* appended, bool append,
                                     int priority_target = -1) {
  buffers.work_mutation[row] = static_cast<int64_t>(mutation);
  buffers.work_added_mask[row] = append;
  buffers.work_priority_target[row] = priority_target;
  if (append) {
    CopyWork(buffers.work_added_fields + row * kWorkFields, appended);
  }
}

__device__ void ModifyWork(const Buffers& buffers,
                           const Dimensions& dimensions, int row,
                           WorkMutation mutation, const int64_t* choice,
                           const int64_t* appended, bool append) {
  int64_t* scratch =
      buffers.work_scratch + row * dimensions.work_capacity * kWorkFields;
  bool* scratch_mask =
      buffers.work_mask_scratch + row * dimensions.work_capacity;
  int output_count = 0;
  bool removed = false;
  for (int work = 0; work < dimensions.work_capacity; ++work) {
    const bool valid = buffers.work_mask[row * dimensions.work_capacity + work];
    const int64_t* fields =
        buffers.work_orders +
        (row * dimensions.work_capacity + work) * kWorkFields;
    if (!valid) continue;
    if (RemoveWork(mutation, fields, choice, appended)) {
      if (!removed) {
        CopyWork(buffers.work_removed_fields + row * kWorkFields, fields);
      }
      removed = true;
      continue;
    }
    CopyWork(scratch + output_count * kWorkFields, fields);
    scratch_mask[output_count] = true;
    ++output_count;
  }
  buffers.work_removed_mask[row] = removed;
  if (append && output_count < dimensions.work_capacity) {
    int insertion = output_count;
    const int64_t appended_key = WorkKey(dimensions, appended);
    while (insertion > 0 &&
           WorkKey(dimensions,
                   scratch + (insertion - 1) * kWorkFields) > appended_key) {
      CopyWork(scratch + insertion * kWorkFields,
               scratch + (insertion - 1) * kWorkFields);
      scratch_mask[insertion] = true;
      --insertion;
    }
    CopyWork(scratch + insertion * kWorkFields, appended);
    scratch_mask[insertion] = true;
    ++output_count;
    CopyWork(buffers.work_added_fields + row * kWorkFields, appended);
    buffers.work_added_mask[row] = true;
  }
  for (int work = output_count; work < dimensions.work_capacity; ++work) {
    int64_t* fields = scratch + work * kWorkFields;
    for (int field = 0; field < kWorkFields; ++field) fields[field] = 0;
    scratch_mask[work] = false;
  }
  for (int work = 0; work < dimensions.work_capacity; ++work) {
    CopyWork(buffers.work_orders +
                 (row * dimensions.work_capacity + work) * kWorkFields,
             scratch + work * kWorkFields);
    buffers.work_mask[row * dimensions.work_capacity + work] =
        scratch_mask[work];
  }
}

__device__ int MarketCount(const Buffers& buffers,
                           const Dimensions& dimensions, int row) {
  int count = 0;
  for (int slot = 0; slot < dimensions.market_capacity; ++slot) {
    count += buffers.market_mask[row * dimensions.market_capacity + slot] ? 1
                                                                          : 0;
  }
  return min(count, dimensions.market_capacity - 1);
}

__global__ void ResetTransitionScalars(int64_t* decision_variant,
                                       int64_t* live_batch_count) {
  if (threadIdx.x == 0) {
    *decision_variant = 0;
    *live_batch_count = 0;
  }
}

__global__ void ApplyTransition(Buffers buffers, Dimensions dimensions,
                                const int64_t* candidate_fields,
                                const int64_t* selected,
                                const float* log_probability,
                                const float* value) {
  const int row = blockIdx.x * blockDim.x + threadIdx.x;
  if (row >= dimensions.batch) return;
  buffers.work_removed_mask[row] = false;
  buffers.work_added_mask[row] = false;
  buffers.work_mutation[row] = static_cast<int64_t>(WorkMutation::kNone);
  buffers.work_priority_target[row] = -1;
  buffers.ledger_dirty_target[row] = -1;
  buffers.position_dirty_role[row] = -1;
  buffers.market_dirty_slot[row] = -1;
  for (int field = 0; field < kWorkFields; ++field) {
    buffers.work_removed_fields[row * kWorkFields + field] = 0;
    buffers.work_added_fields[row * kWorkFields + field] = 0;
  }

  const bool live = buffers.active[row];
  const int64_t choice_index = selected[row];
  const int64_t* choice =
      candidate_fields +
      (row * dimensions.candidate_capacity + choice_index) *
          kCandidateFields;
  if (live) {
    const int trace_index = Clamp(
        static_cast<int>(buffers.trace_counts[row]), 0,
        dimensions.trace_capacity - 1);
    buffers.trace_selected[row * dimensions.trace_capacity + trace_index] =
        choice_index;
    int64_t* trace_fields =
        buffers.trace_fields +
        (row * dimensions.trace_capacity + trace_index) * kCandidateFields;
    for (int field = 0; field < kCandidateFields; ++field) {
      trace_fields[field] = choice[field];
    }
    buffers.trace_log_probability[trace_index * dimensions.batch + row] =
        log_probability[row];
    buffers.trace_value[trace_index * dimensions.batch + row] = value[row];
    ++buffers.trace_counts[row];

    const int64_t action = choice[0];
    if (action == kCommit) {
      buffers.phase[row] = kDone;
      buffers.active[row] = false;
    } else if (action == kBeginAsset) {
      buffers.pending_kind[row] = kBeginAsset;
      buffers.phase[row] = kAssetTarget;
    } else if (action == kBeginCancelAsset) {
      buffers.phase[row] = kCancelAsset;
    } else if (action == kBeginWork) {
      buffers.pending_kind[row] = kBeginWork;
      buffers.phase[row] = kWorkTarget;
    } else if (action == kBeginCancelWork) {
      buffers.phase[row] = kCancelWork;
    } else if (action == kBeginPosition) {
      buffers.phase[row] = kPositionRole;
    } else if (action == kBeginCancelPosition) {
      buffers.phase[row] = kCancelPosition;
    } else if (action == kBeginStore) {
      buffers.phase[row] = kStoreItem;
    } else if (action == kBeginFetch) {
      buffers.phase[row] = kFetchUnit;
    } else if (action == kBeginCancelFetch) {
      buffers.phase[row] = kCancelFetch;
    } else if (action == kBeginDirective) {
      buffers.phase[row] = kDirectiveUnit;
    } else if (action == kBeginCancelDirective) {
      buffers.phase[row] = kCancelDirective;
    } else if (action == kSelectTarget) {
      buffers.pending_target[row] = choice[1];
      buffers.phase[row] = buffers.pending_kind[row] == kBeginAsset
                               ? kAssetProfile
                               : kWorkProfile;
    } else if (action == kSetAsset) {
      const int target = Clamp(static_cast<int>(buffers.pending_target[row]), 0,
                               dimensions.cells - 1);
      int64_t* ledger =
          buffers.ledger +
          (row * dimensions.cells + target) * kLedgerFields;
      ledger[0] = 1;
      ledger[1] = choice[2] - 1 < kCrops ? 1 : 2;
      for (int field = 2; field < 7; ++field) ledger[field] = choice[field];
      ledger[7] = 0;
      buffers.last_ledger_key[row] = target * 16;
      buffers.phase[row] = kRoot;
      UpdateStatus(buffers, dimensions, row, target);
      buffers.ledger_dirty_target[row] = target;
    } else if (action == kCancelAssetChoice) {
      const int target = Clamp(static_cast<int>(choice[1]), 0,
                               dimensions.cells - 1);
      int64_t* ledger =
          buffers.ledger +
          (row * dimensions.cells + target) * kLedgerFields;
      for (int field = 0; field < kLedgerFields; ++field) ledger[field] = 0;
      ledger[6] = 1;
      buffers.last_ledger_key[row] = target * 16;
      buffers.phase[row] = kRoot;
      UpdateStatus(buffers, dimensions, row, target);
      buffers.ledger_dirty_target[row] = target;
    } else if (action == kAddWork) {
      int64_t work[kWorkFields]{};
      work[0] = choice[2] - 1;
      work[1] = choice[1];
      work[4] = choice[6];
      NewWorkStatus(buffers, dimensions, row, choice, work + 5);
      const int32_t* economic =
          buffers.economic + row * dimensions.economic_width;
      const int64_t step =
          (static_cast<int64_t>(economic[0]) + 1) * dimensions.turns_per_day -
          1 - buffers.status_deadline[row * dimensions.cells];
      work[7] = dimensions.episode_steps - step;
      const int target = Clamp(static_cast<int>(work[1]), 0,
                               dimensions.cells - 1);
      ScheduleWorkMutation(buffers, row, WorkMutation::kAddWork, work, true,
                           target);
      buffers.last_ledger_key[row] = work[1] * 16 + 1 + work[0];
      buffers.phase[row] = kRoot;
      buffers.ledger_dirty_target[row] = target;
    } else if (action == kCancelWorkChoice) {
      const int64_t kind = choice[2] - 1;
      const int target =
          kind < 8 ? Clamp(static_cast<int>(choice[1]), 0,
                           dimensions.cells - 1)
                   : -1;
      ScheduleWorkMutation(buffers, row, WorkMutation::kCancelWork, nullptr,
                           false, target);
      buffers.last_ledger_key[row] =
          kind == 8 ? dimensions.cells * 16 + 2 + choice[3] - 1
                    : choice[1] * 16 + 1 + kind;
      buffers.phase[row] = kRoot;
      if (kind < 8) {
        buffers.ledger_dirty_target[row] = target;
      }
    } else if (action == kSelectRole) {
      buffers.pending_role[row] = choice[2] - 1;
      buffers.phase[row] = kPositionTarget;
    } else if (action == kSetPosition) {
      const int role = Clamp(static_cast<int>(choice[2] - 1), 0, 1);
      int64_t* position =
          buffers.positions + (row * 2 + role) * kPositionFields;
      position[0] = 1;
      position[1] = choice[1];
      position[2] = choice[6];
      position[3] = role;
      buffers.last_ledger_key[row] = dimensions.cells * 16 + role;
      buffers.phase[row] = kRoot;
      buffers.position_dirty_role[row] = role;
    } else if (action == kCancelPositionChoice) {
      const int role = Clamp(static_cast<int>(choice[2] - 1), 0, 1);
      int64_t* position =
          buffers.positions + (row * 2 + role) * kPositionFields;
      for (int field = 0; field < kPositionFields; ++field) position[field] = 0;
      buffers.last_ledger_key[row] = dimensions.cells * 16 + role;
      buffers.phase[row] = kRoot;
      buffers.position_dirty_role[row] = role;
    } else if (action == kSelectStoreItem) {
      buffers.pending_item[row] = choice[2] - 1;
      buffers.phase[row] = kStoreQuantity;
    } else if (action == kSelectStoreQuantity) {
      buffers.pending_quantity[row] = choice[7];
      buffers.phase[row] = kStorePriority;
    } else if (action == kAddStore) {
      int64_t work[kWorkFields]{};
      work[0] = 8;
      work[1] = -1;
      work[2] = choice[2];
      work[3] = choice[7];
      work[4] = choice[6];
      int64_t synthetic[kCandidateFields]{};
      for (int field = 0; field < kCandidateFields; ++field) {
        synthetic[field] = choice[field];
      }
      synthetic[2] = 9;
      NewWorkStatus(buffers, dimensions, row, synthetic, work + 5);
      const int32_t* economic =
          buffers.economic + row * dimensions.economic_width;
      const int64_t step =
          (static_cast<int64_t>(economic[0]) + 1) * dimensions.turns_per_day -
          1 - buffers.status_deadline[row * dimensions.cells];
      work[7] = dimensions.episode_steps - step;
      ScheduleWorkMutation(buffers, row, WorkMutation::kAddStore, work, true);
      buffers.last_ledger_key[row] =
          dimensions.cells * 16 + 2 + choice[2] - 1;
      buffers.phase[row] = kRoot;
    } else if (action == kSelectFetchUnit) {
      buffers.pending_unit[row] = choice[8] - 1;
      buffers.phase[row] = kFetchItem;
    } else if (action == kSelectFetchItem) {
      buffers.pending_item[row] = choice[2] - 1;
      buffers.phase[row] = kFetchQuantity;
    } else if (action == kSetFetch) {
      int64_t work[kWorkFields]{};
      const int item = Clamp(static_cast<int>(choice[2] - 1), 0, kItems - 1);
      work[0] = 9;
      work[1] = -1;
      work[2] = choice[2];
      work[3] = choice[7];
      work[4] = 2;
      work[5] = buffers.shed[row * kItems + item] > 0 ? kStatusRunning
                                                       : kStatusBlocked;
      work[6] = buffers.shed[row * kItems + item] > 0
                    ? 0
                    : kReasonShedItemShortfall;
      const int32_t* economic =
          buffers.economic + row * dimensions.economic_width;
      const int64_t step =
          (static_cast<int64_t>(economic[0]) + 1) * dimensions.turns_per_day -
          1 - buffers.status_deadline[row * dimensions.cells];
      work[7] = dimensions.episode_steps - step;
      work[8] = choice[8];
      ScheduleWorkMutation(buffers, row, WorkMutation::kSetFetch, work, true);
      buffers.last_ledger_key[row] = dimensions.cells * 16 + 2 + kItems +
                                     choice[8] - 1;
      buffers.phase[row] = kRoot;
    } else if (action == kCancelFetchChoice) {
      ScheduleWorkMutation(buffers, row, WorkMutation::kCancelFetch, nullptr,
                           false);
      buffers.last_ledger_key[row] = dimensions.cells * 16 + 2 + kItems +
                                     choice[8] - 1;
      buffers.phase[row] = kRoot;
    } else if (action == kSelectDirectiveUnit) {
      buffers.pending_unit[row] = choice[8] - 1;
      buffers.phase[row] = kDirectiveOperation;
    } else if (action == kSelectDirectiveOperation) {
      buffers.pending_directive_operation[row] = choice[9];
      buffers.pending_target[row] = -1;
      buffers.pending_item[row] = -1;
      buffers.pending_quantity[row] = 0;
      buffers.phase[row] =
          choice[9] == kDirectiveWait ? kDirectiveQuantity : kDirectiveTarget;
    } else if (action == kSelectDirectiveTarget) {
      buffers.pending_target[row] = choice[1];
      buffers.phase[row] = kDirectiveItem;
    } else if (action == kSelectDirectiveItem) {
      buffers.pending_item[row] = choice[2] - 1;
      buffers.phase[row] = kDirectiveQuantity;
    } else if (action == kSetDirective) {
      int64_t work[kWorkFields]{};
      const int32_t* economic =
          buffers.economic + row * dimensions.economic_width;
      const int64_t step =
          (static_cast<int64_t>(economic[0]) + 1) * dimensions.turns_per_day -
          1 - buffers.status_deadline[row * dimensions.cells];
      work[0] = 9 + choice[9];
      work[1] = choice[1];
      work[2] = choice[2];
      work[3] = choice[7];
      work[4] = 2;
      work[5] = kStatusRunning;
      work[6] = 0;
      work[7] = dimensions.turns_per_day -
                step % dimensions.turns_per_day;
      work[8] = choice[8];
      ScheduleWorkMutation(buffers, row, WorkMutation::kSetDirective, work,
                           true);
      buffers.last_ledger_key[row] = dimensions.cells * 16 + 2 + kItems +
                                     256 + choice[8] - 1;
      buffers.phase[row] = kRoot;
    } else if (action == kCancelDirectiveChoice) {
      ScheduleWorkMutation(buffers, row, WorkMutation::kCancelDirective,
                           nullptr, false);
      buffers.last_ledger_key[row] = dimensions.cells * 16 + 2 + kItems +
                                     256 + choice[8] - 1;
      buffers.phase[row] = kRoot;
    } else if (action == kMarketHire || action == kMarketBuyLand ||
               action == kMarketSkipSlot) {
      const int slot = MarketCount(buffers, dimensions, row);
      int64_t* market =
          buffers.market_prefix +
          (row * dimensions.market_capacity + slot) * kMarketFields;
      market[0] = action == kMarketHire
                      ? 4
                      : (action == kMarketBuyLand ? 5 : kDoneMarketKind);
      market[1] = action == kMarketSkipSlot ? -1 : 0;
      market[2] = 0;
      buffers.market_mask[row * dimensions.market_capacity + slot] = true;
      buffers.market_phase[row] = true;
      buffers.phase[row] = kRoot;
      buffers.market_dirty_slot[row] = slot;
    } else if (action >= kMarketSell && action <= kMarketBuyAnimal) {
      buffers.pending_market_kind[row] =
          action == kMarketSell
              ? 3
              : (action == kMarketBuySeed
                     ? 0
                     : (action == kMarketBuyProduct ? 1 : 2));
      buffers.pending_market_item[row] = choice[2] - 1;
      buffers.pending_market_upper[row] = choice[7];
      buffers.market_phase[row] = true;
      buffers.phase[row] = kMarketQuantity;
    } else if (action == kSelectMarketQuantity) {
      const int slot = MarketCount(buffers, dimensions, row);
      int64_t* market =
          buffers.market_prefix +
          (row * dimensions.market_capacity + slot) * kMarketFields;
      market[0] = buffers.pending_market_kind[row];
      market[1] = buffers.pending_market_item[row];
      market[2] = choice[7];
      buffers.market_mask[row * dimensions.market_capacity + slot] = true;
      buffers.phase[row] = kRoot;
      buffers.market_dirty_slot[row] = slot;
    }
  }

}

template <int kThreads>
__global__ void ApplyWorkMutations(Buffers buffers, Dimensions dimensions,
                                   const int64_t* candidate_fields,
                                   const int64_t* selected) {
  const int row = blockIdx.x;
  const auto mutation =
      static_cast<WorkMutation>(buffers.work_mutation[row]);
  if (mutation == WorkMutation::kNone) return;

  const int slot = threadIdx.x;
  const int64_t choice_index = selected[row];
  const int64_t* choice =
      candidate_fields +
      (row * dimensions.candidate_capacity + choice_index) *
          kCandidateFields;
  const int64_t* appended =
      buffers.work_added_fields + row * kWorkFields;
  const bool append_requested = buffers.work_added_mask[row];
  const bool valid =
      slot < dimensions.work_capacity &&
      buffers.work_mask[row * dimensions.work_capacity + slot];
  const int64_t* existing =
      buffers.work_orders +
      (row * dimensions.work_capacity +
       min(slot, dimensions.work_capacity - 1)) *
          kWorkFields;
  const bool remove =
      valid && RemoveWork(mutation, existing, choice, appended);
  const int keep = valid && !remove ? 1 : 0;

  using Scan = cub::BlockScan<int, kThreads>;
  __shared__ typename Scan::TempStorage scan_storage;
  __shared__ int kept_total;
  __shared__ int first_removed;
  __shared__ int insertion;
  if (slot == 0) {
    first_removed = dimensions.work_capacity;
    insertion = 0;
  }
  __syncthreads();
  int keep_prefix = 0;
  Scan(scan_storage).ExclusiveSum(keep, keep_prefix);
  if (slot == kThreads - 1) kept_total = keep_prefix + keep;
  if (remove) atomicMin(&first_removed, slot);
  if (append_requested && keep &&
      WorkKey(dimensions, existing) <= WorkKey(dimensions, appended)) {
    atomicAdd(&insertion, 1);
  }
  __syncthreads();

  const bool append = append_requested && kept_total < dimensions.work_capacity;
  int64_t* scratch =
      buffers.work_scratch + row * dimensions.work_capacity * kWorkFields;
  bool* scratch_mask =
      buffers.work_mask_scratch + row * dimensions.work_capacity;
  if (keep) {
    const int destination =
        keep_prefix +
        static_cast<int>(append && WorkKey(dimensions, existing) >
                                      WorkKey(dimensions, appended));
    CopyWork(scratch + destination * kWorkFields, existing);
    scratch_mask[destination] = true;
  }
  if (slot == 0) {
    buffers.work_removed_mask[row] =
        first_removed < dimensions.work_capacity;
    if (first_removed < dimensions.work_capacity) {
      CopyWork(
          buffers.work_removed_fields + row * kWorkFields,
          buffers.work_orders +
              (row * dimensions.work_capacity + first_removed) * kWorkFields);
    }
    buffers.work_added_mask[row] = append;
    if (append) {
      CopyWork(scratch + insertion * kWorkFields, appended);
      scratch_mask[insertion] = true;
    }
  }
  const int output_count = kept_total + static_cast<int>(append);
  if (slot < dimensions.work_capacity && slot >= output_count) {
    int64_t* fields = scratch + slot * kWorkFields;
    for (int field = 0; field < kWorkFields; ++field) fields[field] = 0;
    scratch_mask[slot] = false;
  }
  __syncthreads();
  if (slot < dimensions.work_capacity) {
    CopyWork(buffers.work_orders +
                 (row * dimensions.work_capacity + slot) * kWorkFields,
             scratch + slot * kWorkFields);
    buffers.work_mask[row * dimensions.work_capacity + slot] =
        scratch_mask[slot];
  }
  __syncthreads();

  const int target = static_cast<int>(buffers.work_priority_target[row]);
  if (target >= 0 && slot < 8) {
    int64_t priority = -1;
    for (int work = 0; work < dimensions.work_capacity; ++work) {
      if (!buffers.work_mask[row * dimensions.work_capacity + work]) continue;
      const int64_t* fields =
          buffers.work_orders +
          (row * dimensions.work_capacity + work) * kWorkFields;
      if (fields[0] == slot && fields[1] == target) {
        priority = max(priority, fields[4]);
      }
    }
    buffers.work_priorities[(row * dimensions.cells + target) * 8 + slot] =
        priority;
  }
}

__global__ void FinishTransitions(Buffers buffers, Dimensions dimensions) {
  const int row = blockIdx.x * blockDim.x + threadIdx.x;
  if (row >= dimensions.batch) return;
  if (buffers.active[row]) {
    atomicAdd(reinterpret_cast<unsigned long long*>(buffers.live_batch_count),
              1ULL);
  }
  const int phase = Clamp(static_cast<int>(buffers.phase[row]), 0, kDone);
  atomicMax(reinterpret_cast<unsigned long long*>(buffers.decision_variant),
            static_cast<unsigned long long>(buffers.phase_variants[phase]));
}

void CheckLaunch(const char* operation) {
  const cudaError_t status = cudaGetLastError();
  if (status != cudaSuccess) {
    throw std::runtime_error(std::string(operation) + ": " +
                             cudaGetErrorString(status));
  }
}

}  // namespace

void LaunchTransition(const Buffers& buffers, const Dimensions& dimensions,
                      const int64_t* candidate_fields,
                      const int64_t* selected,
                      const float* log_probability, const float* value,
                      cudaStream_t stream) {
  ResetTransitionScalars<<<1, 1, 0, stream>>>(buffers.decision_variant,
                                              buffers.live_batch_count);
  constexpr int kRowThreads = 128;
  const int row_blocks =
      (dimensions.batch + kRowThreads - 1) / kRowThreads;
  ApplyTransition<<<row_blocks, kRowThreads, 0, stream>>>(
      buffers, dimensions, candidate_fields, selected, log_probability, value);
  ApplyWorkMutations<1024><<<dimensions.batch, 1024, 0, stream>>>(
      buffers, dimensions, candidate_fields, selected);
  FinishTransitions<<<row_blocks, kRowThreads, 0, stream>>>(buffers,
                                                            dimensions);
  CheckLaunch("intent transition kernel");
}

}  // namespace kagg::intents::gpu
