// Shared deterministic calculations for DerivedFact-v1.
#pragma once

#include <array>
#include <optional>
#include <utility>
#include <vector>

#include "derived_facts.hpp"
#include "unit_phase.hpp"

namespace kagg::facts::internal {

enum class ServiceKind : int {
  kWater = 0,
  kHarvest,
  kFertilize,
  kFeed,
  kCare,
  kCollect,
  kDig,
  kPlace,
  kShed,
};

struct Service {
  int x = 0;
  int y = 0;
  int tile_index = -1;
  ServiceKind kind = ServiceKind::kWater;
  int item = -1;
  int required_item = -1;
  std::optional<int> opportunity_deadline;
  std::optional<int> terminal_deadline;
  int maturity_step = -1;
  int production_step = -1;
  int first_decay_step = -1;
  int last_positive_step = -1;
};

struct ProjectedState {
  Farm farm;
  PrivateState priv;
  MarketState market;
  bool market_conditional = false;
};

struct SlackSummary {
  int minimum = 0;
  int reachable = 0;
  bool present = false;
};

float ClampRatio(double value, double scale);
float SignedLog(double value);
int Manhattan(std::pair<int, int> left, std::pair<int, int> right);
std::pair<int, int> UnitPosition(const Farm& farm, int unit_index);
const Inventory* UnitInventory(const PrivateState& priv, int unit_index);
int DistanceToShed(std::pair<int, int> position, int board_size);
int EndOfDay(const Config& config, int step);
int NextProductionStep(const Config& config, const Tile& tile, int step);
std::vector<Service> BuildServices(const View& view, const Farm& farm);
int CompletionStep(const View& view, const Farm& farm, const PrivateState& priv,
                   int unit_index, const Service& service);
SlackSummary UnitSlack(const View& view, const Farm& farm,
                       const PrivateState& priv, int unit_index);
ProjectedState ProjectPrefix(const View& view,
                             const std::vector<int64_t>& tokens,
                             const std::vector<int64_t>& quantities,
                             int unit_count);
int RelevantItem(const UnitAction& action);
int RelevantItem(const MarketOrder& order);
std::array<int64_t, kNumProducts> TownConsumption(const View& view);

}  // namespace kagg::facts::internal
