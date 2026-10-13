#include "capability_internal.hpp"

#include <algorithm>
#include <bit>
#include <limits>
#include <tuple>
#include <unordered_set>
#include <utility>

namespace kagg::capability {
namespace {

constexpr uint64_t kFnvOffset = 1469598103934665603ULL;
constexpr uint64_t kFnvPrime = 1099511628211ULL;

Goal* GoalFor(GoalLedger* ledger, ObjectKind object, int reference) {
  switch (object) {
    case ObjectKind::kWorker:
      return reference == 0 ? &ledger->workers : nullptr;
    case ObjectKind::kLand:
      return reference == 0 ? &ledger->land : nullptr;
    case ObjectKind::kCrop:
      return reference >= 0 && reference < kNumCrops
                 ? &ledger->crops[reference]
                 : nullptr;
    case ObjectKind::kAnimal:
      return reference >= 0 && reference < kNumAnimals
                 ? &ledger->animals[reference]
                 : nullptr;
    case ObjectKind::kProduct:
      return reference >= 0 && reference < kNumProducts
                 ? &ledger->products[reference]
                 : nullptr;
    case ObjectKind::kNone:
      return nullptr;
  }
  return nullptr;
}

bool ApplyEdit(const Edit& edit, GoalLedger* ledger) {
  Goal* goal = GoalFor(ledger, edit.object, static_cast<int>(edit.reference));
  if (goal == nullptr || edit.target < 0) return false;
  const int target = static_cast<int>(std::min<int64_t>(
      edit.target, static_cast<int64_t>(std::numeric_limits<int>::max())));
  switch (edit.type) {
    case EditType::kEnsure:
      goal->lower = std::max(goal->lower, target);
      if (goal->upper >= 0) goal->upper = std::max(goal->upper, goal->lower);
      break;
    case EditType::kReduce:
      goal->upper = goal->upper < 0 ? target : std::min(goal->upper, target);
      goal->lower = std::min(goal->lower, goal->upper);
      break;
    case EditType::kTrade:
      if (edit.object != ObjectKind::kProduct) return false;
      goal->lower = target;
      goal->upper = target;
      break;
    case EditType::kNone:
      return false;
  }
  if (edit.deadline_step >= 0) {
    goal->deadline_step = static_cast<int>(std::min<int64_t>(
        edit.deadline_step,
        static_cast<int64_t>(std::numeric_limits<int>::max())));
  }
  goal->spend_cap = edit.spend_cap;
  goal->price_guard = edit.price_guard;
  goal->urgency = edit.urgency;
  goal->priority = edit.priority;
  ledger->active = true;
  return true;
}

void HashWord(uint64_t value, uint64_t* hash) {
  for (int byte = 0; byte < 8; ++byte) {
    *hash ^= (value >> (byte * 8)) & 0xffULL;
    *hash *= kFnvPrime;
  }
}

uint64_t CanonicalId(Mode mode, const std::vector<Edit>& edits) {
  uint64_t hash = kFnvOffset;
  HashWord(kCapabilitySpecVersion, &hash);
  HashWord(static_cast<uint64_t>(mode), &hash);
  HashWord(edits.size(), &hash);
  for (const Edit& edit : edits) {
    HashWord(static_cast<uint64_t>(edit.type), &hash);
    HashWord(static_cast<uint64_t>(edit.object), &hash);
    HashWord(static_cast<uint64_t>(edit.reference), &hash);
    HashWord(static_cast<uint64_t>(edit.target), &hash);
    HashWord(static_cast<uint64_t>(edit.deadline_step), &hash);
    HashWord(static_cast<uint64_t>(edit.flags), &hash);
    HashWord(std::bit_cast<uint32_t>(edit.spend_cap), &hash);
    HashWord(std::bit_cast<uint32_t>(edit.price_guard), &hash);
    HashWord(std::bit_cast<uint32_t>(edit.urgency), &hash);
    HashWord(std::bit_cast<uint32_t>(edit.priority), &hash);
  }
  return hash == 0 ? 1 : hash;
}

Candidate MakeControlCandidate(const Engine& engine, int player,
                               const internal::StateSummary& state, Mode mode,
                               const GoalLedger& projected, int max_edits) {
  Candidate candidate;
  candidate.mode = mode;
  candidate.valid = true;
  candidate.projected = projected;
  candidate.canonical_id = CanonicalId(mode, candidate.edits);
  candidate.features = internal::CandidateFeatures(
      engine, player, state, mode, candidate.edits, projected, max_edits);
  return candidate;
}

Candidate MakePatchCandidate(const Engine& engine, int player,
                             const internal::StateSummary& state,
                             const GoalLedger& base,
                             std::vector<Edit> edits, int max_edits) {
  Candidate candidate;
  candidate.mode = Mode::kPatch;
  candidate.edits = std::move(edits);
  candidate.projected = base;
  candidate.valid = !candidate.edits.empty() &&
                    static_cast<int>(candidate.edits.size()) <= max_edits;
  for (const Edit& edit : candidate.edits) {
    candidate.valid = ApplyEdit(edit, &candidate.projected) && candidate.valid;
  }
  candidate.canonical_id = CanonicalId(candidate.mode, candidate.edits);
  candidate.features = internal::CandidateFeatures(
      engine, player, state, candidate.mode, candidate.edits,
      candidate.projected, max_edits);
  return candidate;
}

Edit MakeEdit(EditType type, ObjectKind object, int reference, int target,
              int deadline, float spend_cap, float price_guard,
              float urgency, float priority) {
  Edit edit;
  edit.type = type;
  edit.object = object;
  edit.reference = reference;
  edit.target = target;
  edit.deadline_step = deadline;
  edit.spend_cap = spend_cap;
  edit.price_guard = price_guard;
  edit.urgency = urgency;
  edit.priority = priority;
  return edit;
}

}  // namespace

const std::vector<Candidate>& Session::Candidates(const Engine& engine,
                                                   int player) {
  ObserveEpisode(engine, player);
  const internal::StateSummary state = internal::Summarize(engine, player);
  proposal_base_ = ledger_.active ? ledger_ : LedgerFromState(engine, player);
  candidates_.clear();
  const int step = engine.step_index();
  const int turns_per_day = std::max(1, config_.turns_per_day);
  const int day_end = std::min(
      config_.episode_steps - 2,
      ((step / turns_per_day) + 1) * turns_per_day - 1);
  const int final_step = std::max(0, config_.episode_steps - 2);
  const float cash = static_cast<float>(std::max(0.0, engine.farm(player).money));

  if (ledger_.active) {
    candidates_.push_back(MakeControlCandidate(
        engine, player, state, Mode::kContinue, ledger_, max_edits_));
  } else {
    GoalLedger direct = proposal_base_;
    direct.active = false;
    candidates_.push_back(MakeControlCandidate(
        engine, player, state, Mode::kDirectTurn, direct, max_edits_));
  }

  std::vector<Candidate> controls;
  if (ledger_.active) {
    controls.push_back(MakeControlCandidate(
        engine, player, state, Mode::kDirectTurn, ledger_, max_edits_));
    GoalLedger cancelled = ledger_;
    cancelled.active = false;
    controls.push_back(MakeControlCandidate(
        engine, player, state, Mode::kCancel, cancelled, max_edits_));
  }

  std::vector<Candidate> patches;
  const auto add_patch = [&](std::vector<Edit> edits) {
    Candidate candidate = MakePatchCandidate(
        engine, player, state, proposal_base_, std::move(edits), max_edits_);
    if (candidate.valid) patches.push_back(std::move(candidate));
  };

  // A no-growth maintenance option activates the closed-loop service
  // executor without imposing an investment template.
  add_patch({MakeEdit(EditType::kEnsure, ObjectKind::kWorker, 0,
                      proposal_base_.workers.lower, day_end, 0.0F, 0.0F,
                      0.9F, 1.0F)});

  add_patch({MakeEdit(EditType::kEnsure, ObjectKind::kWorker, 0,
                      std::max(state.farm.workers,
                               proposal_base_.workers.lower) +
                          1,
                      day_end, cash * 0.5F, 0.0F, 0.45F, 0.55F)});
  if (std::max(state.farm.quadrants, proposal_base_.land.lower) < 4) {
    add_patch({MakeEdit(EditType::kEnsure, ObjectKind::kLand, 0,
                        std::max(state.farm.quadrants,
                                 proposal_base_.land.lower) +
                            1,
                        day_end, cash * 0.75F, 0.0F, 0.35F, 0.45F)});
  }

  for (int crop = 0; crop < kNumCrops; ++crop) {
    const int target = std::max(state.farm.crop_counts[crop],
                                proposal_base_.crops[crop].lower) +
                       1;
    const int deadline = std::min(
        final_step,
        step + (kCrops[crop].first_yield_day + 1) * turns_per_day);
    add_patch({MakeEdit(EditType::kEnsure, ObjectKind::kCrop, crop, target,
                        deadline, cash * 0.6F, 0.0F, 0.55F, 0.65F)});
    if (max_edits_ >= 2) {
      const int projected_load =
          state.farm.crops + 2 + state.farm.animals * 4 + 4;
      const int workers = std::max(
          proposal_base_.workers.lower,
          (projected_load + turns_per_day - 1) / turns_per_day);
      add_patch({MakeEdit(EditType::kEnsure, ObjectKind::kCrop, crop,
                          target + 1, deadline, cash * 0.8F, 0.0F, 0.5F,
                          0.6F),
                 MakeEdit(EditType::kEnsure, ObjectKind::kWorker, 0,
                          std::max(1, workers), day_end, cash * 0.8F, 0.0F,
                          0.5F, 0.6F)});
    }
  }

  for (int animal = 0; animal < kNumAnimals; ++animal) {
    const int target = std::max(state.farm.animal_counts[animal],
                                proposal_base_.animals[animal].lower) +
                       1;
    const int deadline = std::min(
        final_step,
        step + (kAnimals[animal].first_yield_day + 1) * turns_per_day);
    std::vector<Edit> edits = {
        MakeEdit(EditType::kEnsure, ObjectKind::kAnimal, animal, target,
                 deadline, cash * 0.8F, 0.0F, 0.7F, 0.8F)};
    if (max_edits_ >= 2) {
      const int feed_reserve = std::max<int64_t>(
          state.owned_items[item::kWheat], state.farm.animals + 2);
      edits.push_back(MakeEdit(
          EditType::kTrade, ObjectKind::kProduct, item::kWheat,
          feed_reserve, day_end, cash * 0.8F,
          static_cast<float>(engine.market().prices[item::kWheat]) * 1.25F,
          0.8F, 0.85F));
    }
    add_patch(std::move(edits));
  }

  for (int product = 0; product < kNumProducts; ++product) {
    if (state.owned_items[product] <= 0) continue;
    add_patch({MakeEdit(
        EditType::kTrade, ObjectKind::kProduct, product, 0, day_end, 0.0F,
        static_cast<float>(engine.market().prices[product]), 0.6F, 0.7F)});
  }

  // Rank only proposals, never the mandatory fallback.  The feature is a
  // cheap native proposal prior; PPO/search retain final decision authority.
  std::stable_sort(patches.begin(), patches.end(), [](const Candidate& left,
                                                       const Candidate& right) {
    return std::tuple(-left.features[15], -left.features[17],
                      -left.features[31], left.canonical_id) <
           std::tuple(-right.features[15], -right.features[17],
                      -right.features[31], right.canonical_id);
  });

  std::unordered_set<uint64_t> ids;
  ids.insert(candidates_.front().canonical_id);
  const auto append_unique = [&](const Candidate& candidate) {
    if (static_cast<int>(candidates_.size()) >= max_candidates_) return;
    if (ids.insert(candidate.canonical_id).second) {
      candidates_.push_back(candidate);
    }
  };
  for (const Candidate& control : controls) append_unique(control);
  for (const Candidate& patch : patches) append_unique(patch);

  generated_step_ = step;
  generated_player_ = player;
  return candidates_;
}

}  // namespace kagg::capability
