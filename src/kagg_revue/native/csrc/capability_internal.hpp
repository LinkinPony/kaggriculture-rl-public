// Internal helpers shared by the capability implementation units.
#pragma once

#include <array>
#include <cstdint>
#include <vector>

#include "capability.hpp"

namespace kagg::capability::internal {

struct FarmSummary {
  int workers = 1;
  int quadrants = 1;
  int owned = 0;
  int empty = 0;
  int weeds = 0;
  int crops = 0;
  int animals = 0;
  int crops_needing_water = 0;
  int animals_needing_feed = 0;
  int crops_ready = 0;
  int animals_ready = 0;
  std::array<int, kNumCrops> crop_counts{};
  std::array<int, kNumAnimals> animal_counts{};
};

struct StateSummary {
  FarmSummary farm;
  std::array<int64_t, kNumItems> owned_items{};
  int64_t shed_total = 0;
  int64_t carried_total = 0;
  int occupied = 0;
};

int64_t Carried(const PrivateState& priv, int item_index);
FarmSummary SummarizeFarm(const Config& config, const Farm& farm, int day);
StateSummary Summarize(const Engine& engine, int player);

std::array<float, kCandidateFeatureCount> CandidateFeatures(
    const Engine& engine, int player, const StateSummary& state, Mode mode,
    const std::vector<Edit>& edits, const GoalLedger& projected,
    int max_edits);

}  // namespace kagg::capability::internal
