// Incremental production-portfolio ABI and deterministic native executor.
#pragma once

#include <array>
#include <cstdint>
#include <string>
#include <vector>

#include "action_codec.hpp"
#include "engine.hpp"

namespace kagg::plans {

inline constexpr int kSpecVersion = 3;
inline constexpr int kProductionLineCount = kNumCrops + kNumAnimals;
inline constexpr int kLineFieldCount = 6;
inline constexpr int kGlobalFieldCount = 10;
inline constexpr int kModeTokenCount = 2;
inline constexpr int kLineOperationTokenCount = 3;
inline constexpr int kLineValueTokenCount = 16;
inline constexpr int kGlobalOperationTokenCount = 2;
inline constexpr int kGlobalValueTokenCount = 16;
inline constexpr int kObservationFeatureCount = 90;
inline constexpr int kEventCount = 32;
inline constexpr int kJournalFeatureCount = 32;

inline constexpr std::array<int64_t, 16> kCountBuckets = {
    0, 1, 2, 3, 4, 6, 8, 12, 16, 24, 32, 48, 64, 80, 96, 128};
inline constexpr std::array<double, 16> kMoneyFractions = {
    0.0, 0.02, 0.05, 0.10, 0.15, 0.20, 0.30, 0.40,
    0.50, 0.75, 1.00, 1.50, 2.00, 3.00, 4.00, 8.00};

enum class Mode : int64_t {
  kContinue = 0,
  kStop = 1,
};

enum class LineOperation : int64_t {
  kKeep = 0,
  kUpsert = 1,
  kRetire = 2,
};

enum class GlobalOperation : int64_t {
  kKeep = 0,
  kSet = 1,
};

enum LineField : int {
  kTarget = 0,
  kScaleMode = 1,
  kLinePriority = 2,
  kOutputReserve = 3,
  kPricePolicy = 4,
  kOptionalYield = 5,
};

enum GlobalField : int {
  kWorkerCeiling = 0,
  kLandCeiling = 1,
  kCashReserve = 2,
  kSpendCap = 3,
  kTaskPriorityFirst = 4,
};

enum class Event : int {
  kInitial = 0,
  kDayStart = 1,
  kPlanComplete = 2,
  kPlanExpired = 3,
  kExecutionFailure = 4,
  kLifecycleChanged = 5,
  kTownShopUnlocked = 6,
  kMarketTargetMissed = 7,
  kMarketSlotsTruncated = 8,
  kCropReadyFirst = 9,     // Five consecutive crop events.
  kAnimalReadyFirst = 14,  // Three consecutive animal events.
  kShedBandCrossed = 17,
  kPriceBandCrossed = 18,
  kOpponentLandBandCrossed = 19,
  kOpponentCropBandCrossed = 20,
  kOpponentAnimalBandCrossed = 21,
  kBudgetTruncated = 22,
};

struct ProductionLine {
  std::array<int64_t, kLineFieldCount> values{};
  int64_t price_anchor = 0;
  bool active = false;
};

struct Observation {
  std::array<float, kObservationFeatureCount> features{};
  std::array<float, kJournalFeatureCount> journal{};
  uint64_t event_mask = 0;
  std::array<std::array<int64_t, kLineFieldCount>, kProductionLineCount>
      active_lines{};
  std::array<uint8_t, kProductionLineCount> active_line_mask{};
  std::array<int64_t, kGlobalFieldCount> global_plan{};
};

struct NumericAction {
  std::vector<int64_t> tokens;
  std::vector<int64_t> quantities;
  std::vector<int64_t> unit_sources;
  std::vector<int64_t> unit_reasons;
  std::vector<int64_t> market_sources;
  int64_t decision_count = 0;
  int64_t unit_count = 1;
  bool requires_decision = false;
};

class Session {
 public:
  explicit Session(Config config);

  bool DecisionRequired(const Engine& engine, int player);
  Observation Observe(const Engine& engine, int player);
  void Apply(const Engine& engine, int player, Mode mode,
             const int64_t* line_operations, const int64_t* line_values,
             GlobalOperation global_operation, const int64_t* global_values);
  NumericAction Action(const Engine& engine, int player);
  void Reset();

  bool active() const { return active_line_count_ > 0; }
  bool paused() const { return paused_; }
  int active_line_count() const { return active_line_count_; }
  uint64_t pending_events() const { return pending_events_; }
  Mode selected_mode() const { return selected_mode_; }

 private:
  struct VisibleSnapshot {
    int step = -1;
    int day = -1;
    int town_shops = 0;
    int own_workers = 0;
    int own_land = 0;
    int opponent_land = 0;
    int own_crops = 0;
    int opponent_crops = 0;
    int own_animals = 0;
    int opponent_animals = 0;
    int64_t shed_total = 0;
    std::array<int64_t, kNumItems> owned_items{};
    std::array<int64_t, kNumProducts> prices{};
    std::array<int64_t, kNumProducts> market_inventory{};
    std::array<bool, kNumCrops> crops_ready{};
    std::array<bool, kNumAnimals> animals_ready{};
  };

  VisibleSnapshot Snapshot(const Engine& engine, int player) const;
  void Refresh(const Engine& engine, int player);
  void EvaluateSubscriptions(const VisibleSnapshot& previous,
                             const VisibleSnapshot& current);
  void ResetJournal(const VisibleSnapshot& current);
  bool PlanComplete(const Engine& engine, int player) const;
  Observation BuildObservation(const Engine& engine, int player) const;

  Config config_;
  std::array<ProductionLine, kProductionLineCount> lines_{};
  std::array<int64_t, kGlobalFieldCount> global_plan_{};
  std::vector<uint64_t> commitments_;
  std::vector<int64_t> submitted_market_sources_;
  int active_line_count_ = 0;
  bool global_initialized_ = false;
  bool paused_ = false;
  bool initialized_ = false;
  bool compiler_failed_ = false;
  bool was_complete_ = false;
  bool market_slots_truncated_ = false;
  bool budget_truncated_ = false;
  Mode selected_mode_ = Mode::kStop;
  int player_ = -1;
  int last_seen_step_ = -1;
  int last_decision_step_ = -1;
  int last_decision_day_ = -1;
  int task_successes_ = 0;
  int task_failures_ = 0;
  double phase_spend_ = 0.0;
  uint64_t pending_events_ = 0;
  VisibleSnapshot previous_;
  VisibleSnapshot journal_start_;
  std::array<int64_t, kNumProducts> journal_price_min_{};
  std::array<int64_t, kNumProducts> journal_price_max_{};
};

const char* ModeName(Mode mode);
const char* LineOperationName(LineOperation operation);
const char* GlobalOperationName(GlobalOperation operation);
std::vector<std::string> ObservationFeatureNames();
std::vector<std::string> JournalFeatureNames();
std::vector<std::string> EventNames();

}  // namespace kagg::plans
