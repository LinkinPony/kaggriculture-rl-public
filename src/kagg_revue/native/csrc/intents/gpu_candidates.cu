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
constexpr int kProducts = 9;
constexpr int kCrops = 5;
constexpr int kFertilizer = 8;
constexpr int kGoose = 9;
constexpr int kCandidateFields = 10;
constexpr int kCandidateFeatures = 12;
constexpr int kLedgerFields = 8;
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
constexpr int64_t kDirectivePickup = 3;
constexpr int64_t kDirectivePlace = 5;
constexpr int64_t kDirectivePlant = 6;
constexpr int64_t kDirectiveCare = 15;
constexpr int64_t kPlant = 3;
constexpr int64_t kStructure = 4;

struct Candidate {
  int64_t fields[kCandidateFields];
  bool valid;
};

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

__device__ __forceinline__ int MarketCount(const Buffers& buffers,
                                           const Dimensions& dimensions,
                                           int row) {
  int count = 0;
  const int offset = row * dimensions.market_capacity;
  for (int index = 0; index < dimensions.market_capacity; ++index) {
    count += buffers.market_mask[offset + index] ? 1 : 0;
  }
  return count;
}

__device__ __forceinline__ int64_t MarketSellUpper(
    const Buffers& buffers, const Dimensions& dimensions, int row, int item) {
  int64_t available = buffers.owned[row * kItems + item];
  const int offset = row * dimensions.market_capacity;
  for (int index = 0; index < dimensions.market_capacity; ++index) {
    if (!buffers.market_mask[offset + index]) continue;
    const int64_t* order =
        buffers.market_prefix + (offset + index) * kMarketFields;
    if (order[1] != item) continue;
    if (order[0] == 3) available -= order[2];
    if (order[0] == 1) available += order[2];
  }
  return available > 0 ? available : int64_t{0};
}

__device__ __forceinline__ bool ServiceCovers(
    const Buffers& buffers, const Dimensions& dimensions, int row, int target,
    int kind) {
  const int64_t* ledger =
      buffers.ledger + (row * dimensions.cells + target) * kLedgerFields;
  const int64_t* tile =
      buffers.tiles + (row * dimensions.cells + target) * dimensions.tile_fields;
  const bool plant = tile[0] == kPlant;
  const bool animal = tile[0] == kStructure && tile[7] != 0;
  const int64_t item = ledger[2] - 1;
  const bool crop_match = ledger[0] != 0 && ledger[1] == 1 && plant &&
                          item == tile[1];
  const bool animal_match = ledger[0] != 0 && ledger[1] == 2 && animal &&
                            item == kGoose + tile[8];
  if (kind == 2) return animal_match && ledger[3] == 3;
  if (kind == 4) return animal_match && ledger[5] == 1;
  if (kind == 6) return crop_match && ledger[3] == 2;
  if (kind == 7) return animal_match && ledger[3] == 3;
  return false;
}

__device__ __forceinline__ bool WorkAvailable(
    const Buffers& buffers, const Dimensions& dimensions, int row, int target,
    int kind) {
  const bool applies = buffers.work_applies[
      (row * dimensions.cells + target) * 8 + kind];
  const int64_t last = buffers.last_ledger_key[row];
  return applies && !ServiceCovers(buffers, dimensions, row, target, kind) &&
         target * 16 + 1 + kind > last;
}

__device__ __forceinline__ bool UnitPresent(const Buffers& buffers,
                                            const Dimensions& dimensions,
                                            int row, int unit) {
  const int32_t* economic = buffers.economic + row * dimensions.economic_width;
  const int count = Clamp(economic[1], 1, dimensions.unit_limit);
  return unit < count;
}

__device__ __forceinline__ bool FetchAvailable(
    const Buffers& buffers, const Dimensions& dimensions, int row, int unit,
    int item) {
  if (!UnitPresent(buffers, dimensions, row, unit)) return false;
  const int32_t* economic = buffers.economic + row * dimensions.economic_width;
  const int64_t key = dimensions.cells * 16 + 2 + kItems + unit;
  return key > buffers.last_ledger_key[row] &&
         buffers.shed[row * kItems + item] > 0 &&
         buffers.unit_inventories[(row * dimensions.unit_limit + unit) *
                                      kItems +
                                  item] < economic[5];
}

__device__ Candidate BuildRootCandidate(const Buffers& buffers,
                                        const Dimensions& dimensions, int row,
                                        int slot, unsigned int available) {
  Candidate candidate{};
  candidate.fields[1] = -1;
  if (slot >= 34) return candidate;
  const int32_t* economic = buffers.economic + row * dimensions.economic_width;
  int64_t kind = kCommit;
  if (slot >= 1 && slot <= 7) kind = slot;
  if (slot == 8) kind = kBeginFetch;
  if (slot == 9) kind = kBeginCancelFetch;
  if (slot == 10) kind = kBeginDirective;
  if (slot == 11) kind = kBeginCancelDirective;
  if (slot >= 12 && slot < 21) kind = kMarketSell;
  if (slot >= 21 && slot < 26) kind = kMarketBuySeed;
  if (slot >= 26 && slot < 28) kind = kMarketBuyProduct;
  if (slot >= 28 && slot < 31) kind = kMarketBuyAnimal;
  if (slot == 31) kind = kMarketHire;
  if (slot == 32) kind = kMarketBuyLand;
  if (slot == 33) kind = kMarketSkipSlot;
  candidate.fields[0] = kind;
  if (slot >= 12 && slot < 21) {
    const int item = slot - 12;
    candidate.fields[2] = item + 1;
    candidate.fields[7] = MarketSellUpper(buffers, dimensions, row, item);
  } else if (slot >= 21 && slot < 26) {
    candidate.fields[2] = slot - 20;
    candidate.fields[7] = dimensions.cells;
  } else if (slot >= 26 && slot < 28) {
    candidate.fields[2] = slot == 26 ? 1 : kFertilizer + 1;
    candidate.fields[7] = economic[5] > 1 ? economic[5] : 1;
  } else if (slot >= 28 && slot < 31) {
    candidate.fields[2] = slot - 27;
    candidate.fields[7] = dimensions.cells;
  }

  const bool ledger_allowed = !buffers.market_phase[row];
  const int market_count = MarketCount(buffers, dimensions, row);
  const bool market_room = market_count < dimensions.market_capacity;
  if (slot == 0) {
    candidate.valid = true;
  } else if (slot < 12) {
    candidate.valid = ledger_allowed && ((available & (1U << slot)) != 0);
  } else if (slot < 21) {
    candidate.valid = market_room && candidate.fields[7] > 0;
  } else if (slot < 32) {
    candidate.valid = market_room;
  } else if (slot == 32) {
    int land = 0;
    const int offset = row * dimensions.market_capacity;
    for (int index = 0; index < dimensions.market_capacity; ++index) {
      land += buffers.market_mask[offset + index] &&
              buffers.market_prefix[(offset + index) * kMarketFields] == 5;
    }
    candidate.valid = market_room && economic[11] + land < 3;
  } else {
    candidate.valid = market_room;
  }
  return candidate;
}

__device__ Candidate BuildCandidate(const Buffers& buffers,
                                    const Dimensions& dimensions, int row,
                                    int slot) {
  Candidate candidate{};
  candidate.fields[1] = -1;
  const int64_t phase = buffers.phase[row];
  const int64_t last = buffers.last_ledger_key[row];
  const int32_t* economic = buffers.economic + row * dimensions.economic_width;

  switch (phase) {
    case kRoot: {
      if (slot >= 34) break;
      int64_t kind = kCommit;
      if (slot >= 1 && slot <= 7) kind = slot;
      if (slot == 8) kind = kBeginFetch;
      if (slot == 9) kind = kBeginCancelFetch;
      if (slot == 10) kind = kBeginDirective;
      if (slot == 11) kind = kBeginCancelDirective;
      if (slot >= 12 && slot < 21) kind = kMarketSell;
      if (slot >= 21 && slot < 26) kind = kMarketBuySeed;
      if (slot >= 26 && slot < 28) kind = kMarketBuyProduct;
      if (slot >= 28 && slot < 31) kind = kMarketBuyAnimal;
      if (slot == 31) kind = kMarketHire;
      if (slot == 32) kind = kMarketBuyLand;
      if (slot == 33) kind = kMarketSkipSlot;
      candidate.fields[0] = kind;
      if (slot >= 12 && slot < 21) {
        const int item = slot - 12;
        candidate.fields[2] = item + 1;
        candidate.fields[7] =
            MarketSellUpper(buffers, dimensions, row, item);
      } else if (slot >= 21 && slot < 26) {
        candidate.fields[2] = slot - 20;
        candidate.fields[7] = dimensions.cells;
      } else if (slot >= 26 && slot < 28) {
        candidate.fields[2] = slot == 26 ? 1 : kFertilizer + 1;
        candidate.fields[7] = economic[5] > 1 ? economic[5] : 1;
      } else if (slot >= 28 && slot < 31) {
        candidate.fields[2] = slot - 27;
        candidate.fields[7] = dimensions.cells;
      }
      const bool ledger_allowed = !buffers.market_phase[row];
      const int market_count = MarketCount(buffers, dimensions, row);
      const bool market_room = market_count < dimensions.market_capacity;
      if (slot == 0) {
        candidate.valid = true;
      } else if (slot == 1) {
        candidate.valid = ledger_allowed &&
                          (dimensions.cells - 1) * 16 > last;
      } else if (slot == 2) {
        bool any = false;
        for (int target = 0; target < dimensions.cells; ++target) {
          any |= buffers.ledger[(row * dimensions.cells + target) *
                                    kLedgerFields] != 0 &&
                 target * 16 > last;
        }
        candidate.valid = ledger_allowed && any;
      } else if (slot == 3) {
        bool any = false;
        for (int target = 0; target < dimensions.cells && !any; ++target) {
          for (int work = 0; work < 8; ++work) {
            any |= WorkAvailable(buffers, dimensions, row, target, work);
          }
        }
        candidate.valid = ledger_allowed && any;
      } else if (slot == 4) {
        bool any = false;
        for (int work = 0; work < dimensions.work_capacity; ++work) {
          if (!buffers.work_mask[row * dimensions.work_capacity + work]) continue;
          const int64_t* fields =
              buffers.work_orders +
              (row * dimensions.work_capacity + work) * kWorkFields;
          any |= fields[0] <= 8 && WorkKey(dimensions, fields) > last;
        }
        candidate.valid = ledger_allowed && any;
      } else if (slot == 5) {
        candidate.valid = ledger_allowed && dimensions.cells * 16 + 1 > last;
      } else if (slot == 6) {
        bool any = false;
        for (int role = 0; role < 2; ++role) {
          const int64_t* position =
              buffers.positions + (row * 2 + role) * kPositionFields;
          any |= position[0] != 0 &&
                 dimensions.cells * 16 + position[3] > last;
        }
        candidate.valid = ledger_allowed && any;
      } else if (slot == 7) {
        bool any = false;
        for (int item = 0; item < kItems; ++item) {
          any |= buffers.carried[row * kItems + item] > 0 &&
                 dimensions.cells * 16 + 2 + item > last;
        }
        candidate.valid = ledger_allowed && any;
      } else if (slot == 8) {
        bool any = false;
        for (int unit = 0; unit < dimensions.unit_limit && !any; ++unit) {
          for (int item = 0; item < kItems; ++item) {
            any |= FetchAvailable(buffers, dimensions, row, unit, item);
          }
        }
        candidate.valid = ledger_allowed && any;
      } else if (slot == 9) {
        bool any = false;
        for (int work = 0; work < dimensions.work_capacity; ++work) {
          if (!buffers.work_mask[row * dimensions.work_capacity + work]) continue;
          const int64_t* fields =
              buffers.work_orders +
              (row * dimensions.work_capacity + work) * kWorkFields;
          any |= fields[0] == 9 && WorkKey(dimensions, fields) > last;
        }
        candidate.valid = ledger_allowed && any;
      } else if (slot == 10) {
        bool any = false;
        for (int unit = 0; unit < dimensions.unit_limit; ++unit) {
          const int64_t key =
              dimensions.cells * 16 + 2 + kItems + 256 + unit;
          any |= UnitPresent(buffers, dimensions, row, unit) && key > last;
        }
        candidate.valid = ledger_allowed && any;
      } else if (slot == 11) {
        bool any = false;
        for (int work = 0; work < dimensions.work_capacity; ++work) {
          if (!buffers.work_mask[row * dimensions.work_capacity + work]) continue;
          const int64_t* fields =
              buffers.work_orders +
              (row * dimensions.work_capacity + work) * kWorkFields;
          any |= fields[0] >= 10 && WorkKey(dimensions, fields) > last;
        }
        candidate.valid = ledger_allowed && any;
      } else if (slot >= 12 && slot < 21) {
        candidate.valid = market_room && candidate.fields[7] > 0;
      } else if (slot >= 21 && slot < 32) {
        candidate.valid = market_room;
      } else if (slot == 32) {
        int land = 0;
        const int offset = row * dimensions.market_capacity;
        for (int index = 0; index < dimensions.market_capacity; ++index) {
          land += buffers.market_mask[offset + index] &&
                  buffers.market_prefix[(offset + index) * kMarketFields] == 5;
        }
        candidate.valid = market_room && economic[11] + land < 3;
      } else {
        candidate.valid = market_room;
      }
      break;
    }
    case kAssetTarget:
      candidate.fields[0] = kSelectTarget;
      candidate.fields[1] = min(slot, dimensions.cells - 1);
      candidate.valid = slot < dimensions.cells && slot * 16 > last;
      break;
    case kAssetProfile: {
      const bool crop_profile = slot < 45;
      const int crop_slot = min(slot, 44);
      const int crop = crop_slot / 9;
      const int crop_remainder = crop_slot % 9;
      const int animal_slot = Clamp(slot - 45, 0, 107);
      const int animal = animal_slot / 36;
      const int animal_remainder = animal_slot % 36;
      int maintenance = animal_remainder / 12;
      if (maintenance == 2) maintenance = 3;
      candidate.fields[0] = kSetAsset;
      candidate.fields[1] = buffers.pending_target[row];
      candidate.fields[2] = crop_profile ? crop + 1 : kGoose + animal + 1;
      candidate.fields[3] = crop_profile ? crop_remainder / 3 : maintenance;
      candidate.fields[4] = crop_profile ? 0 : (animal_remainder % 12) / 6;
      candidate.fields[5] = crop_profile ? 0 : (animal_remainder % 6) / 3;
      candidate.fields[6] = crop_profile ? crop_remainder % 3
                                         : animal_remainder % 3;
      const int target = Clamp(buffers.pending_target[row], 0,
                               dimensions.cells - 1);
      const int64_t* current =
          buffers.ledger + (row * dimensions.cells + target) * kLedgerFields;
      const int64_t kind = crop_profile ? 1 : 2;
      const bool same = current[0] != 0 && current[1] == kind &&
                        current[2] == candidate.fields[2] &&
                        current[3] == candidate.fields[3] &&
                        current[4] == candidate.fields[4] &&
                        current[5] == candidate.fields[5] &&
                        current[6] == candidate.fields[6];
      candidate.valid = slot < 153 && !same;
      break;
    }
    case kCancelAsset: {
      const int target = min(slot, dimensions.cells - 1);
      candidate.fields[0] = kCancelAssetChoice;
      candidate.fields[1] = target;
      candidate.valid = slot < dimensions.cells &&
                        buffers.ledger[(row * dimensions.cells + target) *
                                           kLedgerFields] != 0 &&
                        target * 16 > last;
      break;
    }
    case kWorkTarget: {
      const int target = min(slot, dimensions.cells - 1);
      candidate.fields[0] = kSelectTarget;
      candidate.fields[1] = target;
      bool available = false;
      for (int kind = 0; kind < 8; ++kind) {
        available |= WorkAvailable(buffers, dimensions, row, target, kind);
      }
      candidate.valid = slot < dimensions.cells && available;
      break;
    }
    case kWorkProfile: {
      const int kind = min(slot / 3, 7);
      const int priority = slot % 3;
      candidate.fields[0] = kAddWork;
      candidate.fields[1] = buffers.pending_target[row];
      candidate.fields[2] = kind + 1;
      candidate.fields[6] = priority;
      bool same = false;
      for (int work = 0; work < dimensions.work_capacity; ++work) {
        if (!buffers.work_mask[row * dimensions.work_capacity + work]) continue;
        const int64_t* fields =
            buffers.work_orders +
            (row * dimensions.work_capacity + work) * kWorkFields;
        same |= fields[1] == buffers.pending_target[row] &&
                fields[0] == kind && fields[4] == priority;
      }
      const int target = Clamp(buffers.pending_target[row], 0,
                               dimensions.cells - 1);
      candidate.valid = slot < 24 &&
                        WorkAvailable(buffers, dimensions, row, target, kind) &&
                        !same;
      break;
    }
    case kCancelWork: {
      const int work = min(slot, dimensions.work_capacity - 1);
      const int64_t* fields =
          buffers.work_orders +
          (row * dimensions.work_capacity + work) * kWorkFields;
      candidate.fields[0] = kCancelWorkChoice;
      candidate.fields[1] = fields[1];
      candidate.fields[2] = fields[0] + 1;
      candidate.fields[3] = fields[2];
      candidate.valid = slot < dimensions.work_capacity &&
                        buffers.work_mask[row * dimensions.work_capacity + work] &&
                        WorkKey(dimensions, fields) > last;
      break;
    }
    case kPositionRole: {
      const int role = min(slot, 1);
      candidate.fields[0] = kSelectRole;
      candidate.fields[2] = role + 1;
      candidate.valid = slot < 2 && dimensions.cells * 16 + role > last;
      break;
    }
    case kPositionTarget: {
      const int target = min(slot / 3, dimensions.cells - 1);
      const int priority = slot % 3;
      candidate.fields[0] = kSetPosition;
      candidate.fields[1] = target;
      candidate.fields[2] = buffers.pending_role[row] + 1;
      candidate.fields[6] = priority;
      const int role = Clamp(buffers.pending_role[row], 0, 1);
      const int64_t* current =
          buffers.positions + (row * 2 + role) * kPositionFields;
      const bool same = current[0] != 0 && current[1] == target &&
                        current[2] == priority;
      candidate.valid = slot < dimensions.cells * 3 && !same;
      break;
    }
    case kCancelPosition: {
      const int role = min(slot, 1);
      const int64_t* current =
          buffers.positions + (row * 2 + role) * kPositionFields;
      candidate.fields[0] = kCancelPositionChoice;
      candidate.fields[2] = role + 1;
      candidate.valid = slot < 2 && current[0] != 0 &&
                        dimensions.cells * 16 + current[3] > last;
      break;
    }
    case kStoreItem: {
      const int item = min(slot, kItems - 1);
      candidate.fields[0] = kSelectStoreItem;
      candidate.fields[2] = item + 1;
      candidate.valid = slot < kItems &&
                        buffers.carried[row * kItems + item] > 0 &&
                        dimensions.cells * 16 + 2 + item > last;
      break;
    }
    case kStoreQuantity: {
      const int item = Clamp(buffers.pending_item[row], 0, kItems - 1);
      candidate.fields[0] = kSelectStoreQuantity;
      candidate.fields[2] = buffers.pending_item[row] + 1;
      candidate.fields[7] = slot + 1;
      candidate.valid = slot + 1 <= buffers.carried[row * kItems + item];
      break;
    }
    case kStorePriority: {
      candidate.fields[0] = kAddStore;
      candidate.fields[2] = buffers.pending_item[row] + 1;
      candidate.fields[6] = slot;
      candidate.fields[7] = buffers.pending_quantity[row];
      bool same = false;
      for (int work = 0; work < dimensions.work_capacity; ++work) {
        if (!buffers.work_mask[row * dimensions.work_capacity + work]) continue;
        const int64_t* fields =
            buffers.work_orders +
            (row * dimensions.work_capacity + work) * kWorkFields;
        same |= fields[0] == 8 &&
                fields[2] == buffers.pending_item[row] + 1 &&
                fields[3] == buffers.pending_quantity[row] &&
                fields[4] == slot;
      }
      candidate.valid = slot < 3 && !same;
      break;
    }
    case kMarketQuantity:
      candidate.fields[0] = kSelectMarketQuantity;
      candidate.fields[2] = buffers.pending_market_item[row] + 1;
      candidate.fields[7] = slot + 1;
      candidate.valid = slot + 1 <= buffers.pending_market_upper[row];
      break;
    case kFetchUnit: {
      const int unit = min(slot, dimensions.unit_limit - 1);
      candidate.fields[0] = kSelectFetchUnit;
      candidate.fields[8] = unit + 1;
      bool available = false;
      for (int item = 0; item < kItems; ++item) {
        available |= FetchAvailable(buffers, dimensions, row, unit, item);
      }
      const int64_t key = dimensions.cells * 16 + 2 + kItems + unit;
      candidate.valid = slot < dimensions.unit_limit &&
                        UnitPresent(buffers, dimensions, row, unit) &&
                        key > last && available;
      break;
    }
    case kFetchItem: {
      const int item = min(slot, kItems - 1);
      const int unit = Clamp(buffers.pending_unit[row], 0,
                             dimensions.unit_limit - 1);
      candidate.fields[0] = kSelectFetchItem;
      candidate.fields[2] = item + 1;
      candidate.fields[8] = buffers.pending_unit[row] + 1;
      candidate.valid = slot < kItems &&
                        buffers.shed[row * kItems + item] > 0 &&
                        buffers.unit_inventories[
                            (row * dimensions.unit_limit + unit) * kItems +
                            item] < economic[5];
      break;
    }
    case kFetchQuantity: {
      const int item = Clamp(buffers.pending_item[row], 0, kItems - 1);
      const int unit = Clamp(buffers.pending_unit[row], 0,
                             dimensions.unit_limit - 1);
      const int64_t carried = buffers.unit_inventories[
          (row * dimensions.unit_limit + unit) * kItems + item];
      const int64_t available =
          carried + buffers.shed[row * kItems + item];
      const int64_t upper =
          static_cast<int64_t>(economic[5]) < available
              ? static_cast<int64_t>(economic[5])
              : available;
      candidate.fields[0] = kSetFetch;
      candidate.fields[2] = buffers.pending_item[row] + 1;
      candidate.fields[6] = 2;
      candidate.fields[7] = slot + 1;
      candidate.fields[8] = buffers.pending_unit[row] + 1;
      candidate.valid = slot + 1 > carried && slot + 1 <= upper;
      break;
    }
    case kCancelFetch: {
      const int unit = min(slot, dimensions.unit_limit - 1);
      const int64_t key = dimensions.cells * 16 + 2 + kItems + unit;
      const int64_t* matched = nullptr;
      for (int work = 0; work < dimensions.work_capacity; ++work) {
        if (!buffers.work_mask[row * dimensions.work_capacity + work]) continue;
        const int64_t* fields =
            buffers.work_orders +
            (row * dimensions.work_capacity + work) * kWorkFields;
        if (fields[0] == 9 && fields[8] == unit + 1 && matched == nullptr) {
          matched = fields;
        }
      }
      candidate.fields[0] = kCancelFetchChoice;
      candidate.fields[2] = matched == nullptr ? 0 : matched[2];
      candidate.fields[6] = 2;
      candidate.fields[7] = matched == nullptr ? 0 : matched[3];
      candidate.fields[8] = unit + 1;
      candidate.valid = slot < dimensions.unit_limit && matched != nullptr &&
                        key > last;
      break;
    }
    case kDirectiveUnit: {
      const int unit = min(slot, dimensions.unit_limit - 1);
      const int64_t key =
          dimensions.cells * 16 + 2 + kItems + 256 + unit;
      candidate.fields[0] = kSelectDirectiveUnit;
      candidate.fields[8] = unit + 1;
      candidate.valid = slot < dimensions.unit_limit &&
                        UnitPresent(buffers, dimensions, row, unit) &&
                        key > last;
      break;
    }
    case kDirectiveOperation:
      candidate.fields[0] = kSelectDirectiveOperation;
      candidate.fields[8] = buffers.pending_unit[row] + 1;
      candidate.fields[9] = slot + 1;
      candidate.valid = slot < kDirectiveCare;
      break;
    case kDirectiveTarget: {
      const int target = min(slot, dimensions.cells - 1);
      const int64_t operation = buffers.pending_directive_operation[row];
      const bool needs_item = operation == kDirectivePickup ||
                              operation == kDirectivePlace ||
                              operation == kDirectivePlant;
      candidate.fields[0] = needs_item ? kSelectDirectiveTarget : kSetDirective;
      candidate.fields[1] = target;
      candidate.fields[6] = 2;
      candidate.fields[8] = buffers.pending_unit[row] + 1;
      candidate.fields[9] = operation;
      candidate.valid = slot < dimensions.cells;
      break;
    }
    case kDirectiveItem: {
      const int item = min(slot, kItems - 1);
      const int64_t operation = buffers.pending_directive_operation[row];
      const bool quantity =
          operation == kDirectivePickup || operation == kDirectivePlace;
      candidate.fields[0] = quantity ? kSelectDirectiveItem : kSetDirective;
      candidate.fields[1] = buffers.pending_target[row];
      candidate.fields[2] = item + 1;
      candidate.fields[6] = 2;
      candidate.fields[8] = buffers.pending_unit[row] + 1;
      candidate.fields[9] = operation;
      const int upper = operation == kDirectivePlant ? kCrops : kItems;
      candidate.valid = slot < upper;
      break;
    }
    case kDirectiveQuantity: {
      const int64_t operation = buffers.pending_directive_operation[row];
      const int64_t step =
          (static_cast<int64_t>(economic[0]) + 1) * dimensions.turns_per_day -
          1 - buffers.status_deadline[row * dimensions.cells];
      const int64_t hour = step % dimensions.turns_per_day;
      const int64_t upper =
          operation == kDirectiveWait ? dimensions.turns_per_day : economic[5];
      candidate.fields[0] = kSetDirective;
      candidate.fields[1] = buffers.pending_target[row];
      candidate.fields[2] = buffers.pending_item[row] + 1;
      candidate.fields[6] = 2;
      candidate.fields[7] = slot + 1;
      candidate.fields[8] = buffers.pending_unit[row] + 1;
      candidate.fields[9] = operation;
      candidate.valid = slot + 1 <= upper &&
                        (operation != kDirectiveWait || slot + 1 > hour);
      break;
    }
    case kCancelDirective: {
      const int unit = min(slot, dimensions.unit_limit - 1);
      const int64_t key =
          dimensions.cells * 16 + 2 + kItems + 256 + unit;
      const int64_t* matched = nullptr;
      for (int work = 0; work < dimensions.work_capacity; ++work) {
        if (!buffers.work_mask[row * dimensions.work_capacity + work]) continue;
        const int64_t* fields =
            buffers.work_orders +
            (row * dimensions.work_capacity + work) * kWorkFields;
        if (fields[0] >= 10 && fields[8] == unit + 1 && matched == nullptr) {
          matched = fields;
        }
      }
      candidate.fields[0] = kCancelDirectiveChoice;
      candidate.fields[1] = matched == nullptr ? -1 : matched[1];
      candidate.fields[2] = matched == nullptr ? 0 : matched[2];
      candidate.fields[6] = 2;
      candidate.fields[7] = matched == nullptr ? 0 : matched[3];
      candidate.fields[8] = unit + 1;
      candidate.fields[9] = matched == nullptr ? -9 : matched[0] - 9;
      candidate.valid = slot < dimensions.unit_limit && matched != nullptr &&
                        key > last;
      break;
    }
    case kDone:
      break;
  }
  return candidate;
}

__device__ void WriteFeatures(const Buffers& buffers,
                              const Dimensions& dimensions, int row, int slot,
                              const Candidate& candidate) {
  float* features =
      buffers.candidate_features +
      (row * dimensions.candidate_capacity + slot) * kCandidateFeatures;
  for (int field = 0; field < kCandidateFeatures; ++field) {
    features[field] = 0.0F;
  }
  const int64_t choice = candidate.fields[0];
  const int64_t target = candidate.fields[1];
  const int item = static_cast<int>(candidate.fields[2] - 1);
  features[0] = static_cast<float>(choice) / 40.0F;
  features[1] = static_cast<float>(buffers.phase[row]) / 24.0F;
  const bool market = (choice >= kMarketSell &&
                       choice <= kSelectMarketQuantity) ||
                      choice == kMarketSkipSlot;
  features[2] = choice != kCommit && !market ? 1.0F : 0.0F;
  features[3] = market ? 1.0F : 0.0F;
  if (target >= 0 && target < dimensions.cells) {
    features[4] = static_cast<float>(target % dimensions.board_size) /
                  max(1, dimensions.board_size - 1);
    features[5] = static_cast<float>(target / dimensions.board_size) /
                  max(1, dimensions.board_size - 1);
    features[10] = static_cast<float>(
        buffers.ledger[(row * dimensions.cells + target) * kLedgerFields]);
  }
  const int unit = static_cast<int>(candidate.fields[8] - 1);
  if (unit >= 0 && unit < dimensions.unit_limit) {
    const int64_t* position =
        buffers.unit_positions +
        (row * dimensions.unit_limit + unit) * 2;
    features[4] = static_cast<float>(position[0]) /
                  max(1, dimensions.board_size - 1);
    features[5] = static_cast<float>(position[1]) /
                  max(1, dimensions.board_size - 1);
  }
  const float shed_capacity = max(1, buffers.economic[
      row * dimensions.economic_width + 5]);
  features[6] = static_cast<float>(candidate.fields[7]) / shed_capacity;
  if (item >= 0 && item < kItems) {
    features[7] = static_cast<float>(item + 1) / kItems;
    features[9] = static_cast<float>(buffers.owned[row * kItems + item]) /
                  shed_capacity;
    if (item < kProducts) {
      features[8] = static_cast<float>(
          buffers.market_product_ratio[row * kProducts + item]);
    }
  }
  features[11] = static_cast<float>(MarketCount(buffers, dimensions, row)) /
                 max(1, dimensions.market_capacity);
}

__global__ void ResetCandidateCount(int64_t* count) {
  if (threadIdx.x == 0) *count = 0;
}

__device__ void WriteCandidate(const Buffers& buffers,
                               const Dimensions& dimensions, int row,
                               int destination, const Candidate& candidate) {
  int64_t* fields =
      buffers.candidate_fields +
      (row * dimensions.candidate_capacity + destination) *
          kCandidateFields;
  for (int field = 0; field < kCandidateFields; ++field) {
    fields[field] = candidate.fields[field];
  }
  bool mask = true;
  const bool force =
      buffers.trace_counts[row] >= dimensions.maximum_steps - 1 &&
      buffers.phase[row] == kRoot;
  if (force) mask = candidate.fields[0] == kCommit;
  buffers.candidate_mask[row * dimensions.candidate_capacity + destination] =
      mask;
  WriteFeatures(buffers, dimensions, row, destination, candidate);
}

__device__ void FinishCandidateRow(const Buffers& buffers,
                                   const Dimensions& dimensions, int row,
                                   int valid_total) {
  const bool live = buffers.active[row];
  buffers.candidate_counts[row] = live ? valid_total : 0;
  if (!live) {
    const int offset = row * dimensions.candidate_capacity;
    buffers.candidate_mask[offset] = true;
    buffers.candidate_fields[offset * kCandidateFields] = kCommit;
  } else {
    atomicMax(
        reinterpret_cast<unsigned long long*>(buffers.live_candidate_count),
        static_cast<unsigned long long>(valid_total));
  }
}

template <int kThreads>
__global__ void GenerateCandidates(Buffers buffers, Dimensions dimensions,
                                   int capacity) {
  const int row = blockIdx.x;
  const int source_slot = threadIdx.x;
  __shared__ unsigned int root_available;
  if (source_slot == 0) root_available = 0;
  __syncthreads();
  if (buffers.phase[row] == kRoot) {
    unsigned int local = 0;
    const int64_t last = buffers.last_ledger_key[row];
    if (source_slot == 0) {
      if ((dimensions.cells - 1) * 16 > last) local |= 1U << 1;
      if (dimensions.cells * 16 + 1 > last) local |= 1U << 5;
    }
    for (int target = source_slot; target < dimensions.cells;
         target += kThreads) {
      const int64_t* ledger =
          buffers.ledger +
          (row * dimensions.cells + target) * kLedgerFields;
      if (ledger[0] != 0 && target * 16 > last) local |= 1U << 2;
    }
    for (int work_index = source_slot;
         work_index < dimensions.cells * 8; work_index += kThreads) {
      const int target = work_index / 8;
      const int kind = work_index % 8;
      if (WorkAvailable(buffers, dimensions, row, target, kind)) {
        local |= 1U << 3;
      }
    }
    for (int work = source_slot; work < dimensions.work_capacity;
         work += kThreads) {
      if (!buffers.work_mask[row * dimensions.work_capacity + work]) continue;
      const int64_t* fields =
          buffers.work_orders +
          (row * dimensions.work_capacity + work) * kWorkFields;
      if (WorkKey(dimensions, fields) <= last) continue;
      if (fields[0] <= 8) local |= 1U << 4;
      if (fields[0] == 9) local |= 1U << 9;
      if (fields[0] >= 10) local |= 1U << 11;
    }
    for (int role = source_slot; role < 2; role += kThreads) {
      const int64_t* position =
          buffers.positions + (row * 2 + role) * kPositionFields;
      if (position[0] != 0 &&
          dimensions.cells * 16 + position[3] > last) {
        local |= 1U << 6;
      }
    }
    for (int item = source_slot; item < kItems; item += kThreads) {
      if (buffers.carried[row * kItems + item] > 0 &&
          dimensions.cells * 16 + 2 + item > last) {
        local |= 1U << 7;
      }
    }
    for (int unit_item = source_slot;
         unit_item < dimensions.unit_limit * kItems;
         unit_item += kThreads) {
      const int unit = unit_item / kItems;
      const int item = unit_item % kItems;
      if (FetchAvailable(buffers, dimensions, row, unit, item)) {
        local |= 1U << 8;
      }
    }
    for (int unit = source_slot; unit < dimensions.unit_limit;
         unit += kThreads) {
      const int64_t key =
          dimensions.cells * 16 + 2 + kItems + 256 + unit;
      if (UnitPresent(buffers, dimensions, row, unit) && key > last) {
        local |= 1U << 10;
      }
    }
    if (local != 0) atomicOr(&root_available, local);
  }
  __syncthreads();
  Candidate candidate{};
  if (source_slot < capacity) {
    candidate = buffers.phase[row] == kRoot
                    ? BuildRootCandidate(buffers, dimensions, row,
                                         source_slot, root_available)
                    : BuildCandidate(buffers, dimensions, row, source_slot);
  }
  const int flag = source_slot < capacity && candidate.valid ? 1 : 0;
  using Scan = cub::BlockScan<int, kThreads>;
  __shared__ typename Scan::TempStorage scan_storage;
  __shared__ int valid_total;
  int valid_prefix = 0;
  Scan(scan_storage).ExclusiveSum(flag, valid_prefix);
  if (source_slot == kThreads - 1) {
    valid_total = valid_prefix + flag;
  }
  __syncthreads();
  if (source_slot < capacity) {
    const int invalid_prefix = source_slot - valid_prefix;
    const int destination = candidate.valid
                                ? valid_prefix
                                : valid_total + invalid_prefix;
    if (candidate.valid) {
      WriteCandidate(buffers, dimensions, row, destination, candidate);
    } else {
      buffers.candidate_mask[row * dimensions.candidate_capacity +
                             destination] = false;
    }
  }
  __syncthreads();
  if (source_slot == 0) {
    FinishCandidateRow(buffers, dimensions, row, valid_total);
  }
}

// Hopper cannot launch the phase kernel at 1024 threads with Candidate's
// register footprint. Two stable 512-wide scans retain canonical order while
// covering the production work-order capacity without a second global pass.
template <int kThreads>
__global__ void GenerateWideCandidates(Buffers buffers,
                                       Dimensions dimensions, int capacity) {
  const int row = blockIdx.x;
  const int first_slot = threadIdx.x;
  const int second_slot = first_slot + kThreads;
  const int row_offset = row * dimensions.candidate_capacity;
  if (first_slot < capacity) {
    buffers.candidate_mask[row_offset + first_slot] = false;
  }
  if (second_slot < capacity) {
    buffers.candidate_mask[row_offset + second_slot] = false;
  }

  using Scan = cub::BlockScan<int, kThreads>;
  __shared__ typename Scan::TempStorage scan_storage;
  __shared__ int first_total;
  __shared__ int valid_total;

  Candidate first{};
  if (first_slot < capacity) {
    first = BuildCandidate(buffers, dimensions, row, first_slot);
  }
  const int first_flag = first_slot < capacity && first.valid ? 1 : 0;
  int first_prefix = 0;
  Scan(scan_storage).ExclusiveSum(first_flag, first_prefix);
  if (first_slot == kThreads - 1) {
    first_total = first_prefix + first_flag;
  }
  __syncthreads();
  if (first.valid) {
    WriteCandidate(buffers, dimensions, row, first_prefix, first);
  }
  __syncthreads();

  Candidate second{};
  if (second_slot < capacity) {
    second = BuildCandidate(buffers, dimensions, row, second_slot);
  }
  const int second_flag = second_slot < capacity && second.valid ? 1 : 0;
  int second_prefix = 0;
  Scan(scan_storage).ExclusiveSum(second_flag, second_prefix);
  if (first_slot == kThreads - 1) {
    valid_total = first_total + second_prefix + second_flag;
  }
  __syncthreads();
  if (second.valid) {
    WriteCandidate(buffers, dimensions, row, first_total + second_prefix,
                   second);
  }
  __syncthreads();
  if (first_slot == 0) {
    FinishCandidateRow(buffers, dimensions, row, valid_total);
  }
}

void CheckLaunch(const char* operation) {
  const cudaError_t status = cudaGetLastError();
  if (status != cudaSuccess) {
    throw std::runtime_error(std::string(operation) + ": " +
                             cudaGetErrorString(status));
  }
}

}  // namespace

void LaunchCandidates(const Buffers& buffers, const Dimensions& dimensions,
                      int capacity, cudaStream_t stream) {
  ResetCandidateCount<<<1, 1, 0, stream>>>(buffers.live_candidate_count);
  if (capacity <= 64) {
    GenerateCandidates<64><<<dimensions.batch, 64, 0, stream>>>(
        buffers, dimensions, capacity);
  } else if (capacity <= 128) {
    GenerateCandidates<128><<<dimensions.batch, 128, 0, stream>>>(
        buffers, dimensions, capacity);
  } else if (capacity <= 256) {
    GenerateCandidates<256><<<dimensions.batch, 256, 0, stream>>>(
        buffers, dimensions, capacity);
  } else if (capacity <= 512) {
    GenerateCandidates<512><<<dimensions.batch, 512, 0, stream>>>(
        buffers, dimensions, capacity);
  } else {
    GenerateWideCandidates<512><<<dimensions.batch, 512, 0, stream>>>(
        buffers, dimensions, capacity);
  }
  CheckLaunch("intent candidate kernel");
}

}  // namespace kagg::intents::gpu
