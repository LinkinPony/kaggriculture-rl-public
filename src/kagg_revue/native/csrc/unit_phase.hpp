// Reusable farmer/hand prefix execution for the engine and turn compiler.
#pragma once

#include <vector>

#include "types.hpp"

namespace kagg {

inline constexpr int kUnitCompilerSpecVersion = 1;

enum class UnitActionStatus {
  kApplied,
  kPass,
  kMalformed,
  kGhostUnit,
  kIllegal,
  kAtomicPlantConflict,
};

struct UnitActionTrace {
  int unit_index = 0;
  UnitAction requested;
  UnitAction actual;
  UnitActionStatus status = UnitActionStatus::kPass;
};

struct UnitPhaseResult {
  Farm farm;
  PrivateState priv;
  PlayerAction actual;
  std::vector<UnitActionTrace> trace;
};

// Applies one action against the current prefix state. The returned action is
// normalized to its actual quantity, or PASS when it had no effect.
UnitActionTrace ApplyUnitAction(const Config& config, Farm* farm, PrivateState* priv,
                                int unit_index, const UnitAction& action, int day);

// Read-only legality predicate for an already applied prefix state. This is
// equivalent to checking whether ApplyUnitAction would return kApplied or
// kPass, without copying and mutating the farm for every candidate token.
bool WouldApplyUnitAction(const Config& config, const Farm& farm,
                          const PrivateState& priv, int unit_index,
                          const UnitAction& action, int day);

// Official raw phase semantics, including all-or-nothing per-crop PLANT
// validation and ghost-hand demand.
void ApplyPlayerUnitPhase(const Config& config, Farm* farm, PrivateState* priv,
                          const PlayerAction& action, int day);

// Planner/compiler seam: executes farmer then real hands on a private shadow
// copy and returns the protocol action that has the same state effect.
UnitPhaseResult CompileUnitPhase(const Config& config, const Farm& farm,
                                 const PrivateState& priv, const PlayerAction& requested,
                                 int day);

const char* UnitActionStatusName(UnitActionStatus status);

}  // namespace kagg
