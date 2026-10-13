// Episode-local controller state for the native Boatlee v21 runtime.
#pragma once

#include <array>
#include <cstdint>
#include <map>
#include <optional>
#include <utility>
#include <vector>

#include "boatlee/runtime.hpp"

namespace kagg::boatlee::detail {

inline constexpr int kMaximumOrders = 10;
inline constexpr int64_t kFixedShedCapacity = 100;

struct RepairTransaction {
  bool active = false;
  int start = 0;
  UnitAction intended{UnitOp::kPass, -1, 1};
};

struct RepairState {
  std::vector<RepairTransaction> active;
};

struct FrontRunState {
  int last_step = -1;
  int due_step = -1;
  std::array<int64_t, kNumProducts> due{};
};

struct ReplayState {
  int last_step = -1;
  RepairState repair;
  FrontRunState front_run;
};

struct RaceState {
  bool initialized = false;
  int last_step = -1;
  std::array<int64_t, kNumProducts> inventory{};
  std::array<int64_t, kNumProducts> prices{};
  std::array<int64_t, kNumProducts> own_sells{};
  std::vector<int> shops;
  std::array<std::array<double, 6>, 4> scores{};
  std::array<double, 4> evidence{};
  std::array<int, 4> horizon{1, 1, 1, 1};
  std::array<double, 6> policy_scores{};
  double policy_evidence = 0.0;
  int policy_horizon = 1;
};

struct ShiftState {
  std::map<int, std::array<int64_t, kNumProducts>> debts;
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

struct TomatoState {
  bool active = false;
  int scheduled_plants = 0;
  int seed_debt = 0;
};

struct EggState {
  bool active = false;
};

struct MoonState {
  int last_step = -1;
  std::optional<bool> legacy_layout;
  RepairState repair;
  RaceState race;
  ShiftState shift;
  TargetState r5;
  TargetState md;
  RoomState room;
  TomatoState tomato;
  EggState egg;
};

enum class Route : uint8_t { kNone, kMoon, kMutoy, kMunib };

struct OuterState {
  int last_step = -1;
  Route route = Route::kNone;
  bool market_overlay = false;
  bool has_previous_opponent_money = false;
  double previous_opponent_money = 0.0;
};

UnitAction Pass();
void AlignHands(const Engine& engine, int player, PlayerAction* action);
std::pair<int, int> Position(const Farm& farm, int actor);
const Tile* TileAt(const Engine& engine, const Farm& farm,
                   std::pair<int, int> position);
UnitAction* MutableUnit(PlayerAction* action, int actor);
const UnitAction& Unit(const PlayerAction& action, int actor);
bool IsSell(const std::optional<MarketOrder>& slot, int product = -1);
std::optional<MarketOrder>* FirstSell(PlayerAction* action, int product);
void AddSell(PlayerAction* action, int product, int64_t quantity);
int64_t InventoryTotal(const Inventory& inventory);
UnitAction MoveToward(std::pair<int, int> position,
                      std::pair<int, int> target);
std::array<std::pair<int, int>, 4> PythonAccessOrder(int board_size);
std::array<int64_t, kNumItems> ProjectedShed(
    const Engine& engine, int player, const PlayerAction& action);
std::array<int64_t, kNumProducts> SellTotals(const PlayerAction& action);
bool ActionsEqual(const PlayerAction& left, const PlayerAction& right);
int CloneDistance(const Engine& engine);

Tape SelectMoonTape(const Engine& engine, int player, MoonState* state);
PlayerAction ApplyWeedRepair(const Portfolio& portfolio, const Engine& engine,
                             int player, Tape tape, PlayerAction action,
                             RepairState* state);
PlayerAction ReplayAct(const Portfolio& portfolio, const Engine& engine,
                       int player, Tape tape, bool front_run,
                       ReplayState* state);

PlayerAction MoonAct(const Portfolio& portfolio, const Engine& engine,
                     int player, MoonState* state);
PlayerAction RankSellSlots(const Engine& engine, PlayerAction action);
PlayerAction RepayShift(const Engine& engine, PlayerAction action,
                        ShiftState* state);
PlayerAction ApplyPreemptShift(const Portfolio& portfolio,
                               const Engine& engine, int player, Tape tape,
                               PlayerAction action, MoonState* state);
PlayerAction ApplyR5Counter(const Portfolio& portfolio, const Engine& engine,
                            int player, PlayerAction action,
                            TargetState* state);
PlayerAction ApplyMdCounter(const Portfolio& portfolio, const Engine& engine,
                            int player, PlayerAction action,
                            TargetState* state);
void ObserveOpponentMarket(const Portfolio& portfolio, const Engine& engine,
                           int player, MoonState* state);
void RecordOwnSells(const Engine& engine, int player,
                    const PlayerAction& action, RaceState* state);

PlayerAction ApplyRoomEvac(const Engine& engine, int player,
                           PlayerAction action, RoomState* state);
PlayerAction ApplyRoomGuard(const Engine& engine, int player,
                            PlayerAction action);
PlayerAction ApplyTomatoPair(const Engine& engine, int player,
                             PlayerAction action, TomatoState* state);
PlayerAction ApplyEggPair(const Engine& engine, int player,
                          PlayerAction action, EggState* state);
PlayerAction TerminalAction(const Engine& engine, int player);

PlayerAction ApplyMarketDelta(PlayerAction action,
                              const PlayerAction& base_action,
                              const PlayerAction& shifted_action);

}  // namespace kagg::boatlee::detail
