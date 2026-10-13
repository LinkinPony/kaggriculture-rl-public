// Native conditional action tree, persistent options, and shadow execution.
#pragma once

#include <array>
#include <cstdint>
#include <optional>
#include <vector>

#include "engine.hpp"
#include "types.hpp"

namespace kagg::programs {

inline constexpr const char* kAbiVersion = "conditional-turn-program-v2";
inline constexpr int kControlCount = 5;
inline constexpr int kDirectionCount = 4;
inline constexpr int kTaskCount = 16;
inline constexpr int kRawOperationCount = 13;
inline constexpr int kMarketOrderCount = 7;
inline constexpr int kQuantityModeCount = 5;
inline constexpr int kCoopArgument = kNumItems;
inline constexpr int kPastureArgument = kNumItems + 1;
inline constexpr int kNoneArgument = kNumItems + 2;
inline constexpr int kArgumentCount = kNumItems + 3;
inline constexpr int kRootFeatureCount = 18;
inline constexpr int kOptionFeatureCount = 12;

enum class Phase : int64_t { kUnit = 0, kMarket = 1, kDone = 2 };

enum class Control : int64_t {
  kKeep = 0,
  kAssign = 1,
  kStep = 2,
  kRawLocal = 3,
  kCancelPass = 4,
};

enum class Direction : int64_t {
  kNorth = 0,
  kSouth = 1,
  kEast = 2,
  kWest = 3,
};

enum class Task : int64_t {
  kSafePlant = 0,
  kWater = 1,
  kHarvest = 2,
  kFertilize = 3,
  kDig = 4,
  kBuild = 5,
  kDeployAnimal = 6,
  kFeed = 7,
  kCare = 8,
  kCollect = 9,
  kFetch = 10,
  kStore = 11,
  kGoTo = 12,
  kPlant = 13,
  kStoreAll = 14,
  kWait = 15,
};

enum class RawOperation : int64_t {
  kPickup = 0,
  kDrop = 1,
  kPlace = 2,
  kPlant = 3,
  kWater = 4,
  kHarvest = 5,
  kFertilize = 6,
  kDig = 7,
  kBuildCoop = 8,
  kBuildPasture = 9,
  kFeed = 10,
  kCollectFertilizer = 11,
  kCare = 12,
};

enum class MarketOrderType : int64_t {
  kEnd = 0,
  kSell = 1,
  kBuySeed = 2,
  kBuyProduct = 3,
  kBuyAnimal = 4,
  kHire = 5,
  kBuyLand = 6,
};

enum class QuantityMode : int64_t {
  kOne = 0,
  kAllAvailable = 1,
  kPlanDeficit = 2,
  kMaxAffordable = 3,
  kExact = 4,
};

enum class OptionPhase : int64_t {
  kApproach = 0,
  kOperate = 1,
  kFetch = 2,
  kBuild = 3,
  kPlace = 4,
  kWater = 5,
};

struct Selection {
  int64_t control = 0;
  int64_t task = 0;
  int64_t target = -1;
  int64_t argument = kNoneArgument;
  int64_t direction = 0;
  int64_t raw_operation = 0;
  int64_t quantity_mode = 0;
  int64_t exact_quantity = 1;
};

struct Option {
  Task task = Task::kGoTo;
  int target = -1;
  int argument = kNoneArgument;
  QuantityMode quantity_mode = QuantityMode::kOne;
  int64_t exact_quantity = 1;
  OptionPhase phase = OptionPhase::kApproach;
  int created_step = 0;
};

struct Decision {
  Phase phase = Phase::kDone;
  int unit_index = -1;
  int market_slot = -1;
  int unit_count = 0;
  int current_x = 0;
  int current_y = 0;
  std::array<uint8_t, kControlCount> control_mask{};
  std::array<uint8_t, kDirectionCount> direction_mask{};
  std::array<uint8_t, kTaskCount> task_mask{};
  std::vector<uint8_t> task_argument_mask;
  std::vector<uint8_t> task_target_mask;
  std::vector<uint8_t> task_quantity_mode_mask;
  std::vector<int64_t> task_quantity_max;
  std::array<uint8_t, kRawOperationCount> raw_operation_mask{};
  std::vector<uint8_t> raw_argument_mask;
  std::vector<uint8_t> raw_quantity_mode_mask;
  std::vector<int64_t> raw_quantity_max;
  std::array<uint8_t, kMarketOrderCount> market_order_mask{};
  std::vector<uint8_t> market_item_mask;
  std::vector<uint8_t> market_quantity_mode_mask;
  std::vector<int64_t> market_quantity_max;
  std::vector<int16_t> target_reservations;
  std::array<float, kRootFeatureCount> root_features{};
  std::array<int64_t, kOptionFeatureCount> option_features{};
  int forced = 0;
};

struct NumericAction {
  std::vector<int64_t> tokens;
  std::vector<int64_t> quantities;
  int64_t decision_count = 0;
  int64_t unit_count = 0;
  bool requires_decision = false;
  PlayerAction action;
};

struct VisibleState {
  Farm farm;
  PrivateState priv;
  MarketState market;
  int step = 0;
  int player = 0;
};

class Session {
 public:
  Session(Config config, int unit_limit);

  bool DecisionRequired(const Engine& engine, int player);
  Decision Observe(const Engine& engine, int player);
  void Select(const Engine& engine, int player, const Selection& selection);
  NumericAction Action(const Engine& engine, int player);
  bool DecisionRequiredVisible(const VisibleState& state);
  Decision ObserveVisible(const VisibleState& state);
  void SelectVisible(const VisibleState& state, const Selection& selection);
  Selection SelectReplayUnitVisible(
      const VisibleState& state, const Selection& fallback,
      const std::vector<Selection>& proposals);
  NumericAction ActionVisible(const VisibleState& state);
  void Reset();

  const Config& config() const { return config_; }
  int unit_limit() const { return unit_limit_; }
  int maximum_decisions() const {
    return unit_limit_ + config_.max_market_orders;
  }
  Phase phase() const { return phase_; }

 private:
  void Refresh(const Farm& farm, const PrivateState& priv,
               const MarketState& market, int step, int player);
  Decision BuildDecision() const;
  void SelectCurrent(const Selection& selection);
  void SelectUnit(const Selection& selection);
  void SelectMarket(const Selection& selection);
  UnitAction CompileOption(int unit_index, bool* completed);
  UnitAction CompileRaw(const Selection& selection) const;
  UnitAction CompileForcedWater(int unit_index, bool* completed);
  bool CanKeep(int unit_index) const;
  bool ValidateOption(const Option& option, int unit_index) const;
  int FindLaterWaterer(int target, int unit_index) const;
  void ApplyUnit(int unit_index, const UnitAction& action);
  int64_t UnitQuantityMaximum(Task task, int argument,
                              int unit_index) const;
  int64_t ResolveUnitQuantity(Task task, int argument,
                              QuantityMode mode, int64_t exact,
                              int unit_index) const;
  int64_t ResolveMarketQuantity(MarketOrderType order_type, int item,
                                QuantityMode mode, int64_t exact) const;
  int64_t MarketQuantityMaximum(MarketOrderType order_type, int item) const;
  int64_t PlanDeficit(MarketOrderType order_type, int item) const;
  void ProjectMarket(const MarketOrder& order);
  void AdvanceUnit();

  Config config_;
  int unit_limit_ = 1;
  std::vector<std::optional<Option>> options_;
  std::vector<int> forced_water_targets_;
  std::vector<int> forced_water_owners_;
  Farm shadow_farm_;
  PrivateState shadow_priv_;
  MarketState shadow_market_;
  PlayerAction action_;
  Phase phase_ = Phase::kDone;
  int player_ = -1;
  int step_ = -1;
  int day_ = -1;
  int unit_count_ = 0;
  int unit_index_ = 0;
  int market_slot_ = 0;
};

std::vector<const char*> RootFeatureNames();
std::vector<const char*> OptionFeatureNames();

}  // namespace kagg::programs
