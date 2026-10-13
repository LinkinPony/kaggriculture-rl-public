// Atomic-effect action space and policy-neutral deterministic compiler.
#pragma once

#include <array>
#include <cstdint>
#include <optional>
#include <string>
#include <vector>

#include "action_codec.hpp"
#include "engine.hpp"
#include "unit_phase.hpp"

namespace kagg::effects {

inline constexpr int kSpecVersion = 2;
inline constexpr const char* kAbiVersion = "atomic-effect-policy-v2";
inline constexpr int kCandidateFieldCount = 11;
inline constexpr int kCandidateFeatureCount = 12;
inline constexpr int kJobFieldCount = 8;
inline constexpr int kActionFieldCount = 6;

enum class Phase : int64_t { kWork = 0, kMarket = 1, kDone = 2 };

enum class RequestKind : int64_t {
  kStop = 0,
  kPlant = 1,
  kWater = 2,
  kHarvest = 3,
  kFertilize = 4,
  kDig = 5,
  kBuildCoop = 6,
  kBuildPasture = 7,
  kPlaceAnimal = 8,
  kFeed = 9,
  kCare = 10,
  kCollectFertilizer = 11,
  kBank = 12,
  kStage = 13,
  kCancel = 14,
  kBuySeed = 15,
  kBuyProduct = 16,
  kBuyAnimal = 17,
  kSell = 18,
  kHire = 19,
  kBuyLand = 20,
  kLoad = 21,
  kUnload = 22,
  kSkipMarketSlot = 23,
};

enum class ResourceKind : int64_t {
  kNone = 0,
  kSeed = 1,
  kItem = 2,
  kShedRoom = 3,
};

struct Candidate {
  RequestKind kind = RequestKind::kStop;
  // request kind, target, one-based item, exact quantity, job id,
  // one-based bound unit, resource kind, one-based resource item,
  // resource requirement, resource availability, and prefix position.
  std::array<int64_t, kCandidateFieldCount> fields{};
  std::array<float, kCandidateFeatureCount> features{};
  uint64_t canonical_id = 0;
};

struct Job {
  uint64_t id = 0;
  RequestKind kind = RequestKind::kStage;
  int target = -1;
  int item = -1;
  int unit = -1;
  int created_step = -1;
  int priority = 0;
  int64_t quantity = 0;
};

struct SemanticAction {
  RequestKind kind = RequestKind::kStop;
  int target = -1;
  int item = -1;
  int64_t quantity = 0;
  uint64_t job_id = 0;
  int unit = -1;
};

struct Observation {
  Phase phase = Phase::kWork;
  std::vector<Candidate> candidates;
  std::vector<uint8_t> candidate_mask;
  std::vector<std::array<int64_t, kJobFieldCount>> jobs;
  std::vector<std::array<int64_t, kActionFieldCount>> work_prefix;
  std::vector<std::array<int64_t, kActionFieldCount>> market_prefix;
  std::vector<std::array<int64_t, kActionFieldCount>> previous_action;
  int work_limit = 0;
};

struct NumericAction {
  std::vector<int64_t> tokens;
  std::vector<int64_t> quantities;
  int64_t decision_count = 0;
  int64_t unit_count = 1;
};

class Session {
 public:
  Session(Config config, int unit_limit, int maximum_quantity,
          bool task_conditioning = false, bool destination_tasks = false);

  Observation Observe(const Engine& engine, int player);
  Phase Select(const Engine& engine, int player, int candidate_index);
  PlayerAction Action(const Engine& engine, int player);
  NumericAction ActionNumeric(const Engine& engine, int player);
  bool DecisionRequired(const Engine& engine, int player);
  void Reset();

  Phase phase() const { return phase_; }
  int candidate_count() const { return static_cast<int>(candidates_.size()); }
  int step() const { return turn_step_; }
  int unit_limit() const { return unit_limit_; }
  int maximum_quantity() const { return maximum_quantity_; }
  bool task_conditioning() const { return task_conditioning_; }

 private:
  void BeginTurn(const Engine& engine, int player);
  void Reconcile(const Engine& engine, int player);
  void GenerateWorkCandidates(const Engine& engine, int player);
  void GenerateMarketCandidates(const Engine& engine, int player);
  void RefreshWorkMask(const Engine& engine, int player);
  void FinalizeWork(const Engine& engine, int player);
  void ProjectMarketOrder(const MarketOrder& order);
  void AddWorkCandidate(const Engine& engine, int player, Candidate candidate);
  void AddMarketCandidate(const Engine& engine, int player, Candidate candidate);
  UnitPhaseResult CompileJobs(const Engine& engine, int player);
  PlayerAction CompileAction(const Engine& engine, int player);
  int64_t MarketQuantityUpper(OrderKind kind, int item) const;
  std::array<int64_t, kJobFieldCount> EncodeJob(
      const Engine& engine, int player, const Job& job) const;

  Config config_;
  int unit_limit_ = 1;
  int maximum_quantity_ = 1;
  bool task_conditioning_ = false;
  bool destination_tasks_ = false;
  std::vector<Job> jobs_;
  uint64_t next_job_id_ = 1;

  Phase phase_ = Phase::kWork;
  int turn_step_ = -1;
  int player_ = -1;
  int work_limit_ = 1;
  int idle_units_ = 0;
  int selected_new_jobs_ = 0;
  std::vector<Candidate> candidates_;
  std::vector<uint8_t> candidate_mask_;
  std::vector<int> selected_work_;
  std::vector<SemanticAction> turn_work_;
  std::vector<SemanticAction> turn_market_;
  std::vector<SemanticAction> previous_action_;

  bool compiled_ready_ = false;
  PlayerAction compiled_action_;
  Farm projected_farm_;
  PrivateState projected_priv_;
  MarketState projected_market_;
  int last_action_step_ = -1;
  PlayerAction cached_action_;
};

bool IsWork(RequestKind kind);
bool IsMarket(RequestKind kind);
const char* PhaseName(Phase phase);
const char* RequestKindName(RequestKind kind);
const char* ResourceKindName(ResourceKind kind);
std::vector<std::string> CandidateFeatureNames();

}  // namespace kagg::effects
