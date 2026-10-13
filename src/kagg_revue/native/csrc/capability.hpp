// Fixed-shape capability language and deterministic native executor.
//
// A capability is a persistent, actor-visible goal ledger.  The policy only
// chooses among a bounded candidate set at macro decision boundaries; the
// existing native planner compiles the selected ledger into legal turn
// actions between boundaries.
#pragma once

#include <array>
#include <cstdint>
#include <memory>
#include <string>
#include <vector>

#include "action_codec.hpp"
#include "engine.hpp"
#include "planner.hpp"

namespace kagg::capability {

inline constexpr int kCapabilitySpecVersion = 1;
inline constexpr int kIntegerFieldCount = 6;
inline constexpr int kFloatFieldCount = 4;
inline constexpr int kCandidateFeatureCount = 32;
inline constexpr int kRootFeatureCount = 90;

// Zero is intentionally the padding value for every enum exposed through the
// numeric ABI.
enum class Mode : int64_t {
  kDirectTurn = 0,
  kContinue = 1,
  kCancel = 2,
  kPatch = 3,
};

enum class EditType : int64_t {
  kNone = 0,
  kEnsure = 1,
  kReduce = 2,
  kTrade = 3,
};

enum class ObjectKind : int64_t {
  kNone = 0,
  kWorker = 1,
  kLand = 2,
  kCrop = 3,
  kAnimal = 4,
  kProduct = 5,
};

struct Edit {
  EditType type = EditType::kNone;
  ObjectKind object = ObjectKind::kNone;
  int64_t reference = 0;
  int64_t target = 0;
  int64_t deadline_step = -1;
  int64_t flags = 0;
  float spend_cap = 0.0F;
  float price_guard = 0.0F;
  float urgency = 0.0F;
  float priority = 0.0F;
};

struct Goal {
  int lower = 0;
  int upper = -1;
  int deadline_step = -1;
  float spend_cap = 0.0F;
  float price_guard = 0.0F;
  float urgency = 0.0F;
  float priority = 0.0F;
};

struct GoalLedger {
  Goal workers;
  Goal land;
  std::array<Goal, kNumCrops> crops{};
  std::array<Goal, kNumAnimals> animals{};
  std::array<Goal, kNumProducts> products{};
  bool active = false;
};

struct Candidate {
  Mode mode = Mode::kDirectTurn;
  std::vector<Edit> edits;
  std::array<float, kCandidateFeatureCount> features{};
  uint64_t canonical_id = 0;
  bool valid = false;
  GoalLedger projected;
};

struct NumericAction {
  std::vector<int64_t> tokens;
  std::vector<int64_t> quantities;
  int64_t decision_count = 0;
  int64_t unit_count = 1;
  bool requires_direct = true;
};

// One Session belongs to one rollout seat.  It deliberately owns planner
// commitments and the selected goal ledger so no Python object participates
// in per-turn execution.
class Session {
 public:
  Session(Config config, int max_candidates, int max_edits);
  ~Session();
  Session(Session&&) noexcept;
  Session& operator=(Session&&) noexcept;
  Session(const Session&) = delete;
  Session& operator=(const Session&) = delete;

  const std::vector<Candidate>& Candidates(const Engine& engine, int player);
  Mode Select(int candidate_index);
  NumericAction Action(const Engine& engine, int player);
  bool DecisionRequired(const Engine& engine, int player);
  void Reset();

  int max_candidates() const { return max_candidates_; }
  int max_edits() const { return max_edits_; }
  bool active() const { return ledger_.active; }
  Mode selected_mode() const { return selected_mode_; }
  uint64_t selected_canonical_id() const { return selected_canonical_id_; }
  const GoalLedger& ledger() const { return ledger_; }

 private:
  void ObserveEpisode(const Engine& engine, int player);
  GoalLedger LedgerFromState(const Engine& engine, int player) const;
  planner::PlannerOptions PlannerOptionsFromLedger() const;
  void RebuildPlanner();

  Config config_;
  int max_candidates_ = 0;
  int max_edits_ = 0;
  GoalLedger ledger_;
  GoalLedger proposal_base_;
  std::vector<Candidate> candidates_;
  std::unique_ptr<planner::NativePlanner> planner_;
  Mode selected_mode_ = Mode::kDirectTurn;
  uint64_t selected_canonical_id_ = 0;
  int selected_day_ = -1;
  int generated_step_ = -1;
  int generated_player_ = -1;
  int last_seen_step_ = -1;
  int player_ = -1;
};

std::array<float, kRootFeatureCount> EncodeRootFeatures(const Engine& engine,
                                                        int player,
                                                        const Session& session);
std::vector<std::string> RootFeatureNames();
std::vector<std::string> CandidateFeatureNames();
const char* ModeName(Mode mode);
const char* EditTypeName(EditType type);
const char* ObjectKindName(ObjectKind kind);

}  // namespace kagg::capability
