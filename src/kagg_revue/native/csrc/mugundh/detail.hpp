// Internal state and guard boundaries for the native Mugundh v21 runtime.
#pragma once

#include <array>
#include <cstdint>
#include <optional>
#include <utility>
#include <vector>

#include "mugundh/runtime.hpp"

namespace kagg::mugundh::detail {

struct RepairTransaction {
  bool active = false;
  int start = 0;
  UnitAction intended{UnitOp::kPass, -1, 1};
};

struct RepairState {
  std::vector<RepairTransaction> active;
};

struct ShiftState {
  int due_step = -1;
  std::array<int64_t, kNumProducts> due{};
};

struct TargetState {
  bool target = false;
};

struct RoomState {
  int day = -1;
  bool active = false;
  int actor = -1;
  std::pair<int, int> target{};
};

struct SeatState {
  int last_step = -1;
  std::optional<bool> legacy_layout;
  RepairState repair;
  ShiftState shift;
  TargetState r5;
  TargetState md;
  RoomState room;
};

UnitAction Pass();
void AlignHands(const Engine& engine, int player, PlayerAction* action);
std::array<int64_t, kNumItems> ProjectedShed(
    const Engine& engine, int player, const PlayerAction& action);

Tape SelectTape(const Engine& engine, int player, SeatState* state);
PlayerAction ApplyWeedRepair(const Portfolio& portfolio, const Engine& engine,
                             int player, Tape tape, PlayerAction action,
                             RepairState* state);
PlayerAction ApplyRoomEvac(const Engine& engine, int player,
                           PlayerAction action, RoomState* state);
PlayerAction ApplyRoomGuard(const Engine& engine, int player,
                            PlayerAction action);

PlayerAction RepayShift(const Engine& engine, PlayerAction action,
                        ShiftState* state);
PlayerAction RankSellSlots(const Engine& engine, PlayerAction action);
PlayerAction ApplyPreemptShift(const Portfolio& portfolio,
                               const Engine& engine, int player, Tape tape,
                               PlayerAction action, ShiftState* state);
PlayerAction ApplyR5Counter(const Portfolio& portfolio, const Engine& engine,
                            int player, PlayerAction action,
                            TargetState* state);
PlayerAction ApplyMdCounter(const Portfolio& portfolio, const Engine& engine,
                            int player, PlayerAction action,
                            TargetState* state);
PlayerAction ApplyTerminalLiquidation(const Engine& engine, int player,
                                      PlayerAction action);
PlayerAction ApplySellDivergenceGuard(const Engine& engine, int player,
                                      PlayerAction action);

}  // namespace kagg::mugundh::detail
