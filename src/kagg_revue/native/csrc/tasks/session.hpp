// Actor-owned unit task tapes and deterministic official-action compilation.
#pragma once

#include <array>
#include <cstdint>
#include <deque>
#include <string>
#include <vector>

#include "action_codec.hpp"
#include "engine.hpp"
#include "unit_phase.hpp"

namespace kagg::tasks {

inline constexpr const char* kAbiVersion = "unit-task-tape-v1";
inline constexpr int kCandidateFeatureCount = 18;
inline constexpr int kRootFeatureCount = 24;
inline constexpr int kTaskFieldCount = 9;
inline constexpr int kModeCount = 2;
inline constexpr int kCompactResourceCount =
    kNumCrops + kNumItems + kNumItems;

enum class Operation : int64_t {
  kEnd = 0,
  kPosition = 1,
  kWait = 2,
  kPickup = 3,
  kDrop = 4,
  kPlace = 5,
  kPlant = 6,
  kWater = 7,
  kHarvest = 8,
  kFertilize = 9,
  kDig = 10,
  kBuildCoop = 11,
  kBuildPasture = 12,
  kFeed = 13,
  kCollectFertilizer = 14,
  kCare = 15,
};

enum class FeasibilityReason : int64_t {
  kFeasible = 0,
  kEnd = 1,
  kOutOfTime = 2,
  kNoProgress = 3,
  kInvalidGeometry = 4,
  kInvalidParameter = 5,
};

enum class ResultStatus : int64_t {
  kCompleted = 0,
  kTargetInvalid = 1,
  kResourceConflict = 2,
  kNoOp = 3,
  kMissedDeadline = 4,
  kDayEnded = 5,
  kUnitRemoved = 6,
  kReplaced = 7,
};

enum class ReplanReason : int64_t {
  kDayStart = 0,
  kNewUnit = 1,
  kQueueEmpty = 2,
  kTaskCompleted = 3,
  kTargetInvalid = 4,
  kOperationFailed = 5,
  kDeadlineMissed = 6,
};

enum class SuffixMode : int64_t {
  kContinue = 0,
  kRewrite = 1,
};

struct Candidate {
  Operation operation = Operation::kEnd;
  int argument = -1;
  int x = -1;
  int y = -1;
};

struct Task {
  Operation operation = Operation::kWait;
  int argument = -1;
  int x = -1;
  int y = -1;
  int64_t quantity = 0;
  int earliest = 0;
  int deadline = 0;
  int completion = 0;
  uint64_t record_id = 0;
};

struct TaskRecord {
  int unit_index = 0;
  Task task;
  int status_token = 0;  // 0 is active; 1 + ResultStatus is final.
  int step = 0;
};

struct Decision {
  int unit_index = 0;
  int current_x = 0;
  int current_y = 0;
  int available_at = 0;
  int day_end = 0;
  int replan_reason = 0;
  std::array<uint8_t, kModeCount> mode_mask{};
  std::vector<uint8_t> candidate_mask;
  std::vector<int64_t> candidate_arrivals;
  std::vector<int64_t> candidate_reasons;
  std::vector<float> candidate_features;
  std::vector<int16_t> target_conflicts;
  std::vector<int16_t> resource_conflicts;
  std::vector<int64_t> prefix_fields;
  std::vector<uint8_t> prefix_mask;
  std::array<float, kRootFeatureCount> root_features{};
};

struct NumericUnitAction {
  std::vector<int64_t> tokens;
  std::vector<int64_t> quantities;
  std::vector<int64_t> task_results;
  int64_t unit_count = 1;
  bool requires_decision = false;
};

struct VisibleState {
  Farm farm;
  PrivateState priv;
  int step = 0;
  int player = 0;
};

struct Selection {
  SuffixMode mode = SuffixMode::kRewrite;
  int candidate_index = 0;
  int64_t quantity = 0;
  int earliest = 0;
  int deadline = 0;
};

// Compact turn-boundary state used by the GPU-resident autoregressive planner.
// Visible farm/private state remains in the existing policy GPU state ABI.
struct PlanningSnapshot {
  bool requires_decision = false;
  int hour = 0;
  int day = 0;
  int days = 1;
  int unit_count = 0;
  int history_count = 0;
  int successful_tasks = 0;
  int failed_tasks = 0;
  int forced_ends = 0;
  std::vector<int16_t> prefix_fields;
  std::vector<uint8_t> replan_mask;
  std::vector<uint8_t> optional_mask;
  std::vector<int16_t> replan_reasons;
  std::vector<int16_t> tape_sizes;
};

class Session {
 public:
  Session(Config config, int unit_limit, int maximum_quantity);

  bool DecisionRequired(const Engine& engine, int player);
  Decision Observe(const Engine& engine, int player);
  Decision ObserveCompact(const Engine& engine, int player);
  void Select(const Engine& engine, int player, SuffixMode mode,
              int candidate_index, int64_t quantity, int earliest,
              int deadline);
  NumericUnitAction Action(const Engine& engine, int player);
  bool DecisionRequired(const Farm& farm, const PrivateState& priv, int step,
                        int player);
  Decision Observe(const Farm& farm, const PrivateState& priv, int step,
                   int player);
  Decision ObserveCompact(const Farm& farm, const PrivateState& priv, int step,
                          int player);
  void Select(const Farm& farm, const PrivateState& priv, int step, int player,
              SuffixMode mode, int candidate_index, int64_t quantity,
              int earliest, int deadline);
  NumericUnitAction Action(const Farm& farm, const PrivateState& priv,
                           int step, int player);
  PlanningSnapshot Snapshot(const Engine& engine, int player);
  PlanningSnapshot Snapshot(const Farm& farm, const PrivateState& priv,
                            int step, int player);
  void ApplySelections(const Engine& engine, int player,
                       const Selection* selections, int count);
  void ApplySelections(const Farm& farm, const PrivateState& priv, int step,
                       int player, const Selection* selections, int count);
  void Reset();

  const Config& config() const { return config_; }
  int unit_limit() const { return unit_limit_; }
  int maximum_quantity() const { return maximum_quantity_; }
  int candidate_count() const {
    return static_cast<int>(catalog_.size());
  }
  int prefix_capacity() const { return prefix_capacity_; }
  const std::vector<Candidate>& catalog() const { return catalog_; }
  const std::vector<TaskRecord>& history() const { return history_; }

 private:
  struct UnitState {
    std::deque<Task> tape;
    bool replan = false;
    bool optional = false;
    ReplanReason reason = ReplanReason::kQueueEmpty;
    int ended_step = -1;
  };

  struct PendingOperation {
    bool active = false;
    int step = -1;
    uint64_t record_id = 0;
    ResultStatus result = ResultStatus::kNoOp;
  };

  struct PlanningState {
    bool active = false;
    bool first = true;
    int unit_index = -1;
    int x = 0;
    int y = 0;
    int available_at = 0;
    std::vector<Task> tasks;
  };

  void Refresh(const Farm& farm, const PrivateState& priv, int step,
               int player);
  void StartPlanning(const Farm& farm, int step);
  void FinishPlanningUnit(const Farm& farm, int step);
  void MarkReplan(int unit_index, ReplanReason reason, bool optional);
  void CompleteHead(int unit_index, ResultStatus result, int step,
                    ReplanReason reason);
  void ClearTape(int unit_index, ResultStatus result, int step);
  void UpdateRecord(uint64_t record_id, ResultStatus result, int step);
  void AppendRecord(int unit_index, const Task& task, int step);
  void TrimHistory();
  Decision BuildDecision(const Farm& farm, const PrivateState& priv, int step,
                         bool include_candidate_surface) const;
  NumericUnitAction CompileAction(const Farm& farm, const PrivateState& priv,
                                  int step);
  void ApplySelection(const Farm& farm, int step, SuffixMode mode,
                      int candidate_index, int64_t quantity, int earliest,
                      int deadline);
  std::vector<Candidate> BuildCatalog() const;

  Config config_;
  int unit_limit_ = 1;
  int maximum_quantity_ = 1;
  int prefix_capacity_ = 1;
  std::vector<Candidate> catalog_;
  std::vector<UnitState> units_;
  std::vector<PendingOperation> pending_;
  std::vector<TaskRecord> history_;
  PlanningState planning_;
  uint64_t next_record_id_ = 1;
  int player_ = -1;
  int last_seen_step_ = -1;
  int last_seen_day_ = -1;
  int last_unit_count_ = 0;
  int successful_tasks_ = 0;
  int failed_tasks_ = 0;
  int forced_ends_ = 0;
  int last_action_step_ = -1;
  NumericUnitAction last_action_;
};

bool IsOfficial(Operation operation);
bool NeedsQuantity(Operation operation);
int ManhattanDistance(int left_x, int left_y, int right_x, int right_y);
std::vector<std::string> CandidateFeatureNames();
std::vector<std::string> RootFeatureNames();
std::vector<std::string> TaskFieldNames();

}  // namespace kagg::tasks
