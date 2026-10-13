// Native deterministic fallback planner.
//
// The planner owns every stateful hot-path component.  Python passes one
// official observation at the boundary and receives either the compiled
// action or an optional diagnostic trace.
#pragma once

#include <array>
#include <cstdint>
#include <optional>
#include <string>
#include <unordered_map>
#include <utility>
#include <vector>

#include "market_phase.hpp"
#include "types.hpp"
#include "unit_phase.hpp"

namespace kagg::planner {

inline constexpr int kPlannerSpecVersion = 16;

enum class SchedulerKind {
  kGreedy,
  kDeadlineAware,
  kMinCost,
  kRouteAware,
  kTerritoryAware,
};

enum class ProjectLayoutKind {
  kAdaptive,
  kServiceZones,
  kCropCore,
};

enum class SupplyRouteMode {
  kUnbound,
  kTaskBound,
};

enum class TaskContinuationMode {
  kRelease,
  kSticky,
  kRegret,
};

enum class SoftServiceMode {
  kEager,
  kSurvivalFirst,
};

enum class SaleMode {
  kHold,
  kCapacity,
  kValue,
  kImpact,
  kAggressive,
};

struct StrategyOptions {
  int target_workers = 4;
  int target_plants = 8;
  int preferred_crop = item::kWheat;
  bool explicit_control = false;
  bool enforce_production_targets = false;
  bool allow_land = true;
  bool allow_crop_investment = true;
  bool allow_animal_investment = true;
  int preferred_animal = -1;
  bool liquidation_only = false;
  int target_land_quadrants = 0;
  bool has_crop_targets = false;
  std::array<int, kNumCrops> target_crops{};
  bool has_animal_targets = false;
  std::array<int, kNumAnimals> target_animals{};
  double cash_reserve_fraction = 0.0;
  double cash_reserve_amount = 0.0;
  SaleMode sale_mode = SaleMode::kAggressive;
  bool defer_one_time_harvest = false;
  SoftServiceMode soft_service_mode = SoftServiceMode::kEager;
  std::array<int64_t, kNumProducts> product_reserves{};
  // Capability ledgers use reserves as closed-loop inventory targets.  The
  // legacy planner keeps its protect-only behavior unless explicitly enabled.
  bool replenish_product_reserves = false;
  std::array<double, kNumProducts> minimum_sale_prices{};
};

struct PlannerOptions {
  StrategyOptions strategy;
  SchedulerKind scheduler = SchedulerKind::kRouteAware;
  int supply_route_capacity = 0;
  SupplyRouteMode supply_route_mode = SupplyRouteMode::kUnbound;
  TaskContinuationMode task_continuation_mode =
      TaskContinuationMode::kRelease;
  int continuation_travel_value = 75;
  ProjectLayoutKind project_layout = ProjectLayoutKind::kAdaptive;
  int animal_zone_cells = 0;
  int crop_zone_cells = 0;
  int project_layout_start_day = 0;
};

struct Intent {
  UnitAction action;
  int required_item = -1;
  std::string key;
  std::vector<std::string> predecessors;
  int priority = 0;
  bool hard = false;
  std::optional<int> deadline_step;
  std::string resource_group;
  int resource_limit = 0;
  std::string exclusive_group;
  bool reserve_before_ready = false;
  bool allow_supply = true;
  bool requires_command = false;
  bool proposal_only = false;
};

struct Task {
  std::string key;
  std::pair<int, int> position;
  std::vector<Intent> intents;
  int priority = 0;
  std::optional<int> deadline_step;
  std::string reason;
  int layout_cost = 0;
};

enum class CommitmentKind { kTask, kSupply, kReturn };

struct Commitment {
  CommitmentKind kind = CommitmentKind::kTask;
  std::pair<int, int> target;
  std::string task_key;
  int item = -1;
  std::vector<std::string> route_tasks;
};

struct Assignment {
  int unit_index = 0;
  std::string task;
  std::pair<int, int> target;
  UnitAction action;
  std::string reason;
  std::string node;
};

struct ScheduleResult {
  PlayerAction requested;
  std::vector<Assignment> assignments;
  std::vector<std::string> deferred_tasks;
  std::vector<int> unassigned_units;
  std::array<int64_t, kNumItems> supply_reservations{};
  std::array<int64_t, kNumItems> supply_shortfalls{};
  std::vector<std::pair<int, Commitment>> commitments;
};

struct StrategyTrace {
  std::string kind;
  std::string action;
  std::string operation;
  int item = -1;
  int64_t count = 0;
  bool selected = true;
  std::string reason;
  std::string retry_state;
  std::optional<int64_t> normalized_count;
};

struct PlanResult {
  PlayerAction action;
  std::vector<Task> tasks;
  ScheduleResult schedule;
  std::vector<StrategyTrace> strategy_trace;
  std::vector<UnitActionTrace> unit_trace;
  std::vector<MarketSlotTrace> market_trace;
  int truncated_orders = 0;
};

struct PlannerStateView {
  const Config& config;
  const Farm& farm;
  const Farm& opponent_farm;
  const PrivateState& priv;
  const MarketState& market;
  int player = 0;
  int step = 0;
};

class NativePlanner {
 public:
  NativePlanner(Config config, PlannerOptions options);

  PlanResult Plan(const Farm& farm, const Farm& opponent_farm,
                  const PrivateState& priv, const MarketState& market,
                  int player, int step);
  void Reset();

 private:
  Config config_;
  PlannerOptions options_;
  std::unordered_map<int, Commitment> commitments_;
  std::unordered_map<std::string, std::string> rejected_market_states_;
  int last_step_ = -1;
  int day_ = -1;
  int player_ = -1;
  double cash_reserve_anchor_ = 0.0;

  friend ScheduleResult Schedule(const PlannerStateView&, const std::vector<Task>&,
                                 SchedulerKind, int, SupplyRouteMode,
                                 TaskContinuationMode, int,
                                 std::unordered_map<int, Commitment>*);
  friend std::pair<std::vector<std::optional<MarketOrder>>, std::vector<StrategyTrace>>
  ChooseMarketOrders(const PlannerStateView&, const Farm&, const PrivateState&,
                     const StrategyOptions&, double,
                     const std::array<int64_t, kNumItems>&,
                     std::unordered_map<std::string, std::string>*);
};

std::vector<Task> GenerateTasks(const PlannerStateView& state,
                                const StrategyOptions& options,
                                ProjectLayoutKind project_layout,
                                int animal_zone_cells,
                                int crop_zone_cells,
                                int project_layout_start_day);

ScheduleResult Schedule(const PlannerStateView& state,
                        const std::vector<Task>& tasks,
                        SchedulerKind scheduler,
                        int supply_route_capacity,
                        SupplyRouteMode supply_route_mode,
                        TaskContinuationMode task_continuation_mode,
                        int continuation_travel_value,
                        std::unordered_map<int, Commitment>* commitments);

std::pair<std::vector<std::optional<MarketOrder>>, std::vector<StrategyTrace>>
ChooseMarketOrders(const PlannerStateView& state, const Farm& post_farm,
                   const PrivateState& post_priv,
                   const StrategyOptions& options, double cash_reserve_anchor,
                   const std::array<int64_t, kNumItems>& supply_reservations,
                   std::unordered_map<std::string, std::string>* rejected_states);

}  // namespace kagg::planner
