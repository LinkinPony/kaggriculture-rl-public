#include "plans/session.hpp"

#include <algorithm>
#include <array>
#include <cmath>
#include <limits>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

namespace kagg::plans {
namespace {

constexpr std::array<int, kLineFieldCount> kLineCardinalities = {
    16, 2, 16, 16, 5, 2};
constexpr std::array<int, kGlobalFieldCount> kGlobalCardinalities = {
    16, 4, 16, 16, 16, 16, 16, 16, 16, 16};
constexpr int64_t kInitialCashReserveMaxToken = 9;
constexpr int64_t kInitialSpendCapMinToken = 5;

uint64_t EventBit(Event event) {
  return uint64_t{1} << static_cast<int>(event);
}

float SafeRatio(double numerator, double denominator) {
  return static_cast<float>(numerator / std::max(1.0, denominator));
}

int CountPlants(const Farm& farm, int crop = -1) {
  int count = 0;
  for (const Tile& tile : farm.tiles) {
    if (tile.kind == TileKind::kPlant && (crop < 0 || tile.crop == crop)) {
      ++count;
    }
  }
  return count;
}

int CountAnimals(const Farm& farm, int animal = -1) {
  int count = 0;
  for (const Tile& tile : farm.tiles) {
    if (tile.kind == TileKind::kStructure && tile.has_animal &&
        (animal < 0 || tile.animal == animal)) {
      ++count;
    }
  }
  return count;
}

int64_t Carried(const PrivateState& priv, int item_index) {
  int64_t result = 0;
  for (const Inventory& inventory : priv.inventories) {
    result += inventory.Get(item_index);
  }
  return result;
}

int64_t OwnedItem(const PrivateState& priv, int item_index) {
  return priv.shed[item_index] + Carried(priv, item_index);
}

int ProductForLine(int line) {
  return line < kNumCrops ? line : kAnimals[line - kNumCrops].product;
}

bool Crossed(int64_t previous, int64_t current, int64_t threshold) {
  return (previous < threshold && current >= threshold) ||
         (previous > threshold && current <= threshold);
}

double PriceThreshold(const ProductionLine& line) {
  switch (line.values[kPricePolicy]) {
    case 2:
      return 1.1 * static_cast<double>(line.price_anchor);
    case 4:
      return 0.9 * static_cast<double>(line.price_anchor);
    default:
      return static_cast<double>(line.price_anchor);
  }
}

void ValidateLineValues(const int64_t* values) {
  for (int field = 0; field < kLineFieldCount; ++field) {
    if (values[field] < 0 || values[field] >= kLineCardinalities[field]) {
      throw std::invalid_argument(
          "structured-plan line value is outside the ABI");
    }
  }
  if (values[kTarget] == 0) {
    throw std::invalid_argument(
        "structured-plan active line requires a nonzero target");
  }
}

void ValidateGlobalValues(const int64_t* values) {
  for (int field = 0; field < kGlobalFieldCount; ++field) {
    if (values[field] < 0 || values[field] >= kGlobalCardinalities[field]) {
      throw std::invalid_argument(
          "structured-plan global value is outside the ABI");
    }
  }
}

bool AllZero(const int64_t* values, int count) {
  return std::all_of(values, values + count,
                     [](int64_t value) { return value == 0; });
}

}  // namespace

Session::Session(Config config) : config_(std::move(config)) {}

Session::VisibleSnapshot Session::Snapshot(const Engine& engine,
                                           int player) const {
  const Farm& own = engine.farm(player);
  const Farm& opponent = engine.farm(1 - player);
  const PrivateState& priv = engine.priv(player);
  const int day = engine.step_index() / std::max(1, config_.turns_per_day);
  VisibleSnapshot result;
  result.step = engine.step_index();
  result.day = day;
  result.town_shops = static_cast<int>(engine.town_shops().size());
  result.own_workers = static_cast<int>(own.hands.size());
  result.own_land = own.extra_unlocked + 1;
  result.opponent_land = opponent.extra_unlocked + 1;
  result.own_crops = CountPlants(own);
  result.opponent_crops = CountPlants(opponent);
  result.own_animals = CountAnimals(own);
  result.opponent_animals = CountAnimals(opponent);
  result.shed_total = ShedTotal(priv);
  for (int item_index = 0; item_index < kNumItems; ++item_index) {
    result.owned_items[item_index] = OwnedItem(priv, item_index);
  }
  result.prices = engine.market().prices;
  result.market_inventory = engine.market().inventory;
  for (const Tile& tile : own.tiles) {
    if (tile.kind == TileKind::kPlant && tile.crop >= 0 &&
        tile.crop < kNumCrops && tile.yield_units > 0 &&
        day - tile.planted_day >= kCrops[tile.crop].first_yield_day) {
      result.crops_ready[tile.crop] = true;
    }
    if (tile.kind == TileKind::kStructure && tile.has_animal &&
        tile.animal >= 0 && tile.animal < kNumAnimals &&
        tile.yield_units > 0) {
      result.animals_ready[tile.animal] = true;
    }
  }
  return result;
}

void Session::ResetJournal(const VisibleSnapshot& current) {
  journal_start_ = current;
  journal_price_min_ = current.prices;
  journal_price_max_ = current.prices;
  task_successes_ = 0;
  task_failures_ = 0;
}

void Session::EvaluateSubscriptions(const VisibleSnapshot& previous,
                                    const VisibleSnapshot& current) {
  int64_t crop_threshold = 0;
  int64_t animal_threshold = 0;
  for (int line_id = 0; line_id < kProductionLineCount; ++line_id) {
    const ProductionLine& line = lines_[line_id];
    if (!line.active) continue;
    if (line_id < kNumCrops) {
      crop_threshold += kCountBuckets[line.values[kTarget]];
      if (!previous.crops_ready[line_id] && current.crops_ready[line_id]) {
        pending_events_ |= EventBit(static_cast<Event>(
            static_cast<int>(Event::kCropReadyFirst) + line_id));
      }
    } else {
      const int animal = line_id - kNumCrops;
      animal_threshold += kCountBuckets[line.values[kTarget]];
      if (!previous.animals_ready[animal] && current.animals_ready[animal]) {
        pending_events_ |= EventBit(static_cast<Event>(
            static_cast<int>(Event::kAnimalReadyFirst) + animal));
      }
    }

    const int product = ProductForLine(line_id);
    const int64_t reserve = kCountBuckets[line.values[kOutputReserve]];
    if (Crossed(previous.owned_items[product], current.owned_items[product],
                reserve)) {
      pending_events_ |= EventBit(Event::kShedBandCrossed);
    }
    if (line.values[kPricePolicy] != 0) {
      const double threshold = PriceThreshold(line);
      const double margin = std::max(1.0, threshold * 0.01);
      const bool crossed_up =
          previous.prices[product] < threshold - margin &&
          current.prices[product] >= threshold + margin;
      const bool crossed_down =
          previous.prices[product] > threshold + margin &&
          current.prices[product] <= threshold - margin;
      if (crossed_up || crossed_down) {
        pending_events_ |= EventBit(Event::kPriceBandCrossed);
      }
    }
  }
  if (!global_initialized_) return;
  const int64_t land_threshold = global_plan_[kLandCeiling] + 1;
  if (Crossed(previous.opponent_land, current.opponent_land,
              land_threshold)) {
    pending_events_ |= EventBit(Event::kOpponentLandBandCrossed);
  }
  if (crop_threshold > 0 &&
      Crossed(previous.opponent_crops, current.opponent_crops,
              crop_threshold)) {
    pending_events_ |= EventBit(Event::kOpponentCropBandCrossed);
  }
  if (animal_threshold > 0 &&
      Crossed(previous.opponent_animals, current.opponent_animals,
              animal_threshold)) {
    pending_events_ |= EventBit(Event::kOpponentAnimalBandCrossed);
  }
}

bool Session::PlanComplete(const Engine& engine, int player) const {
  if (!active()) return false;
  const Farm& farm = engine.farm(player);
  bool has_goal = false;
  for (int line_id = 0; line_id < kProductionLineCount; ++line_id) {
    const ProductionLine& line = lines_[line_id];
    if (!line.active) continue;
    has_goal = true;
    const int64_t target = kCountBuckets[line.values[kTarget]];
    const int count = line_id < kNumCrops
                          ? CountPlants(farm, line_id)
                          : CountAnimals(farm, line_id - kNumCrops);
    if (line.values[kScaleMode] == 1 ? count != target : count < target) {
      return false;
    }
  }
  return has_goal;
}

void Session::Refresh(const Engine& engine, int player) {
  if (player < 0 || player > 1) {
    throw std::invalid_argument("player must be 0 or 1");
  }
  if ((player_ >= 0 && player_ != player) ||
      (last_seen_step_ >= 0 && engine.step_index() < last_seen_step_)) {
    Reset();
  }
  player_ = player;
  if (initialized_ && engine.step_index() == last_seen_step_) return;
  const VisibleSnapshot current = Snapshot(engine, player);
  if (!initialized_) {
    initialized_ = true;
    previous_ = current;
    last_seen_step_ = current.step;
    ResetJournal(current);
    pending_events_ |= EventBit(Event::kInitial);
    if (current.step % std::max(1, config_.turns_per_day) == 0) {
      pending_events_ |= EventBit(Event::kDayStart);
    }
    return;
  }
  if (compiler_failed_) {
    pending_events_ |= EventBit(Event::kExecutionFailure);
    compiler_failed_ = false;
  }
  for (int product = 0; product < kNumProducts; ++product) {
    journal_price_min_[product] =
        std::min(journal_price_min_[product], current.prices[product]);
    journal_price_max_[product] =
        std::max(journal_price_max_[product], current.prices[product]);
  }
  if (current.day != previous_.day) {
    pending_events_ |= EventBit(Event::kDayStart);
    pending_events_ |= EventBit(Event::kLifecycleChanged);
    commitments_.clear();
  }
  if (current.town_shops > previous_.town_shops) {
    pending_events_ |= EventBit(Event::kTownShopUnlocked);
  }
  EvaluateSubscriptions(previous_, current);
  const bool complete = PlanComplete(engine, player);
  if (complete && !was_complete_) {
    pending_events_ |= EventBit(Event::kPlanComplete);
  }
  was_complete_ = complete;
  previous_ = current;
  last_seen_step_ = current.step;
}

bool Session::DecisionRequired(const Engine& engine, int player) {
  Refresh(engine, player);
  return pending_events_ != 0;
}

Observation Session::Observe(const Engine& engine, int player) {
  Refresh(engine, player);
  return BuildObservation(engine, player);
}

void Session::Apply(const Engine& engine, int player, Mode mode,
                    const int64_t* line_operations,
                    const int64_t* line_values,
                    GlobalOperation global_operation,
                    const int64_t* global_values) {
  Refresh(engine, player);
  if (line_operations == nullptr || line_values == nullptr ||
      global_values == nullptr) {
    throw std::invalid_argument(
        "structured-plan portfolio action tensors cannot be null");
  }
  if (mode != Mode::kContinue && mode != Mode::kStop) {
    throw std::invalid_argument("unknown structured-plan mode token");
  }
  if (global_operation != GlobalOperation::kKeep &&
      global_operation != GlobalOperation::kSet) {
    throw std::invalid_argument(
        "unknown structured-plan global operation token");
  }

  const bool was_active = active();
  if (!was_active && mode == Mode::kStop) {
    throw std::invalid_argument(
        "STOP requires an active production portfolio");
  }

  auto candidate_lines = lines_;
  auto candidate_global = global_plan_;
  int candidate_count = active_line_count_;
  bool line_changed = false;
  bool inserted_line = false;
  for (int line_id = 0; line_id < kProductionLineCount; ++line_id) {
    const auto operation =
        static_cast<LineOperation>(line_operations[line_id]);
    const int64_t* values =
        line_values + static_cast<size_t>(line_id) * kLineFieldCount;
    if (operation != LineOperation::kKeep &&
        operation != LineOperation::kUpsert &&
        operation != LineOperation::kRetire) {
      throw std::invalid_argument(
          "unknown structured-plan line operation token");
    }
    const bool line_active = lines_[line_id].active;
    if (operation == LineOperation::kKeep) {
      if (!AllZero(values, kLineFieldCount)) {
        throw std::invalid_argument(
            "line KEEP requires canonical zero values");
      }
      continue;
    }
    if (operation == LineOperation::kRetire) {
      if (!line_active || !AllZero(values, kLineFieldCount)) {
        throw std::invalid_argument(
            "line RETIRE requires one active line and zero values");
      }
      candidate_lines[line_id] = ProductionLine{};
      --candidate_count;
      line_changed = true;
      continue;
    }

    ValidateLineValues(values);
    std::array<int64_t, kLineFieldCount> replacement{};
    std::copy_n(values, kLineFieldCount, replacement.begin());
    if (line_active && replacement == lines_[line_id].values) {
      throw std::invalid_argument(
          "line UPSERT must make a semantic change");
    }
    ProductionLine& line = candidate_lines[line_id];
    line.values = replacement;
    line.price_anchor = engine.market().prices[ProductForLine(line_id)];
    line.active = true;
    if (!line_active) {
      ++candidate_count;
      inserted_line = true;
    }
    line_changed = true;
  }

  bool global_changed = false;
  if (global_operation == GlobalOperation::kKeep) {
    if (!AllZero(global_values, kGlobalFieldCount)) {
      throw std::invalid_argument(
          "global KEEP requires canonical zero values");
    }
  } else {
    ValidateGlobalValues(global_values);
    if (!was_active &&
        (global_values[kCashReserve] > kInitialCashReserveMaxToken ||
         global_values[kSpendCap] < kInitialSpendCapMinToken)) {
      throw std::invalid_argument(
          "initial portfolio must authorize one production input");
    }
    std::array<int64_t, kGlobalFieldCount> replacement{};
    std::copy_n(global_values, kGlobalFieldCount, replacement.begin());
    if (was_active && replacement == global_plan_) {
      throw std::invalid_argument(
          "global SET must make a semantic change");
    }
    candidate_global = replacement;
    global_changed = true;
  }
  if (!was_active &&
      (!inserted_line || global_operation != GlobalOperation::kSet)) {
    throw std::invalid_argument(
        "initial decision requires a line UPSERT and global SET");
  }
  lines_ = candidate_lines;
  global_plan_ = candidate_global;
  active_line_count_ = candidate_count;
  global_initialized_ =
      global_initialized_ || global_operation == GlobalOperation::kSet;
  paused_ = mode == Mode::kStop;
  if (line_changed || global_changed) was_complete_ = false;

  selected_mode_ = mode;
  last_decision_step_ = engine.step_index();
  last_decision_day_ =
      engine.step_index() / std::max(1, config_.turns_per_day);
  phase_spend_ = 0.0;
  pending_events_ = 0;
  compiler_failed_ = false;
  ResetJournal(Snapshot(engine, player));
}

Observation Session::BuildObservation(const Engine& engine, int player) const {
  Observation result;
  const Farm& own = engine.farm(player);
  const Farm& opponent = engine.farm(1 - player);
  const PrivateState& priv = engine.priv(player);
  const int board_cells = std::max(1, config_.board_size * config_.board_size);
  const int step = engine.step_index();
  const int day = step / std::max(1, config_.turns_per_day);
  const int turn = step % std::max(1, config_.turns_per_day);
  const int total_days =
      std::max(1, config_.episode_steps / config_.turns_per_day);
  int feature = 0;
  const auto add = [&result, &feature](float value) {
    if (feature >= kObservationFeatureCount) {
      throw std::logic_error(
          "structured-plan observation feature overflow");
    }
    result.features[feature++] = value;
  };
  add(SafeRatio(step, config_.episode_steps - 1));
  add(SafeRatio(day, total_days));
  add(SafeRatio(turn, config_.turns_per_day - 1));
  add(SafeRatio(config_.episode_steps - 1 - step,
                config_.episode_steps - 1));
  add(SafeRatio(own.money, config_.starting_money));
  add(SafeRatio(opponent.money, config_.starting_money));
  add(SafeRatio(own.hands.size(), board_cells));
  add(SafeRatio(opponent.hands.size(), board_cells));
  add(SafeRatio(own.extra_unlocked + 1, 4));
  add(SafeRatio(opponent.extra_unlocked + 1, 4));
  for (const Farm* farm : {&own, &opponent}) {
    std::array<int, 5> kinds{};
    for (const Tile& tile : farm->tiles) {
      ++kinds[static_cast<int>(tile.kind)];
    }
    for (int count : kinds) add(SafeRatio(count, board_cells));
  }
  for (const Farm* farm : {&own, &opponent}) {
    for (int crop = 0; crop < kNumCrops; ++crop) {
      add(SafeRatio(CountPlants(*farm, crop), board_cells));
    }
  }
  for (const Farm* farm : {&own, &opponent}) {
    for (int animal = 0; animal < kNumAnimals; ++animal) {
      add(SafeRatio(CountAnimals(*farm, animal), board_cells));
    }
  }
  for (int item_index = 0; item_index < kNumItems; ++item_index) {
    add(SafeRatio(priv.shed[item_index], config_.shed_capacity));
  }
  for (int item_index = 0; item_index < kNumItems; ++item_index) {
    add(SafeRatio(Carried(priv, item_index), config_.shed_capacity));
  }
  for (int product = 0; product < kNumProducts; ++product) {
    add(SafeRatio(engine.market().inventory[product],
                  config_.market_params[product].i0));
  }
  for (int product = 0; product < kNumProducts; ++product) {
    add(SafeRatio(engine.market().prices[product],
                  config_.market_params[product].base));
  }
  std::array<bool, kNumShops> unlocked{};
  for (int shop : engine.town_shops()) {
    if (shop >= 0 && shop < kNumShops) unlocked[shop] = true;
  }
  for (bool value : unlocked) add(value ? 1.0F : 0.0F);
  add(active() ? 1.0F : 0.0F);
  add(paused_ ? 1.0F : 0.0F);
  add(SafeRatio(active_line_count_, kProductionLineCount));
  add(last_decision_step_ < 0
          ? 0.0F
          : SafeRatio(step - last_decision_step_,
                      config_.episode_steps - 1));
  if (feature != kObservationFeatureCount) {
    throw std::logic_error(
        "structured-plan observation feature count mismatch");
  }

  int journal = 0;
  for (int product = 0; product < kNumProducts; ++product) {
    result.journal[journal++] = SafeRatio(
        journal_price_min_[product] - journal_start_.prices[product],
        config_.market_params[product].base);
  }
  for (int product = 0; product < kNumProducts; ++product) {
    result.journal[journal++] = SafeRatio(
        journal_price_max_[product] - journal_start_.prices[product],
        config_.market_params[product].base);
  }
  for (int product = 0; product < kNumProducts; ++product) {
    result.journal[journal++] = SafeRatio(
        engine.market().inventory[product] -
            journal_start_.market_inventory[product],
        config_.market_params[product].i0);
  }
  result.journal[journal++] = SafeRatio(
      previous_.opponent_land - journal_start_.opponent_land, 4);
  result.journal[journal++] = SafeRatio(
      previous_.opponent_crops - journal_start_.opponent_crops,
      board_cells);
  result.journal[journal++] = SafeRatio(
      previous_.opponent_animals - journal_start_.opponent_animals,
      board_cells);
  result.journal[journal++] =
      SafeRatio(task_successes_, config_.turns_per_day);
  result.journal[journal++] =
      SafeRatio(task_failures_, config_.turns_per_day);
  if (journal != kJournalFeatureCount) {
    throw std::logic_error(
        "structured-plan journal feature count mismatch");
  }
  result.event_mask = pending_events_;
  result.global_plan = global_plan_;
  for (int line = 0; line < kProductionLineCount; ++line) {
    if (!lines_[line].active) continue;
    result.active_lines[line] = lines_[line].values;
    result.active_line_mask[line] = 1;
  }
  return result;
}

void Session::Reset() {
  lines_.fill(ProductionLine{});
  global_plan_.fill(0);
  commitments_.clear();
  submitted_market_sources_.clear();
  active_line_count_ = 0;
  global_initialized_ = false;
  paused_ = false;
  initialized_ = false;
  compiler_failed_ = false;
  was_complete_ = false;
  market_slots_truncated_ = false;
  budget_truncated_ = false;
  selected_mode_ = Mode::kStop;
  player_ = -1;
  last_seen_step_ = -1;
  last_decision_step_ = -1;
  last_decision_day_ = -1;
  task_successes_ = 0;
  task_failures_ = 0;
  phase_spend_ = 0.0;
  pending_events_ = 0;
  previous_ = VisibleSnapshot{};
  journal_start_ = VisibleSnapshot{};
  journal_price_min_.fill(0);
  journal_price_max_.fill(0);
}

const char* ModeName(Mode mode) {
  switch (mode) {
    case Mode::kContinue:
      return "CONTINUE";
    case Mode::kStop:
      return "STOP";
  }
  return "UNKNOWN";
}

const char* LineOperationName(LineOperation operation) {
  switch (operation) {
    case LineOperation::kKeep:
      return "KEEP";
    case LineOperation::kUpsert:
      return "UPSERT";
    case LineOperation::kRetire:
      return "RETIRE";
  }
  return "UNKNOWN";
}

const char* GlobalOperationName(GlobalOperation operation) {
  switch (operation) {
    case GlobalOperation::kKeep:
      return "KEEP";
    case GlobalOperation::kSet:
      return "SET";
  }
  return "UNKNOWN";
}

std::vector<std::string> ObservationFeatureNames() {
  std::vector<std::string> names = {
      "step",          "day",              "turn_in_day",
      "remaining_steps", "own_money",      "opponent_money",
      "own_workers",   "opponent_workers", "own_land",
      "opponent_land"};
  for (const char* seat : {"own", "opponent"}) {
    for (const char* kind : {"empty", "locked", "weed", "plant",
                             "structure"}) {
      names.push_back(std::string(seat) + "_tiles_" + kind);
    }
  }
  for (const char* seat : {"own", "opponent"}) {
    for (int crop = 0; crop < kNumCrops; ++crop) {
      names.push_back(std::string(seat) + "_crop_" + kItemNames[crop]);
    }
  }
  for (const char* seat : {"own", "opponent"}) {
    for (int animal = 0; animal < kNumAnimals; ++animal) {
      names.push_back(std::string(seat) + "_animal_" +
                      kItemNames[item::kGoose + animal]);
    }
  }
  for (const char* item_name : kItemNames) {
    names.push_back(std::string("shed_") + item_name);
  }
  for (const char* item_name : kItemNames) {
    names.push_back(std::string("carried_") + item_name);
  }
  for (int product = 0; product < kNumProducts; ++product) {
    names.push_back(std::string("market_inventory_") +
                    kItemNames[product]);
  }
  for (int product = 0; product < kNumProducts; ++product) {
    names.push_back(std::string("market_price_") + kItemNames[product]);
  }
  for (const ShopData& shop : kShops) {
    names.push_back(std::string("shop_") + shop.name);
  }
  names.insert(names.end(), {"portfolio_active", "portfolio_paused",
                             "portfolio_active_lines", "portfolio_age"});
  if (static_cast<int>(names.size()) != kObservationFeatureCount) {
    throw std::logic_error(
        "structured-plan observation name count mismatch");
  }
  return names;
}

std::vector<std::string> JournalFeatureNames() {
  std::vector<std::string> names;
  for (int product = 0; product < kNumProducts; ++product) {
    names.push_back(std::string("price_min_delta_") +
                    kItemNames[product]);
  }
  for (int product = 0; product < kNumProducts; ++product) {
    names.push_back(std::string("price_max_delta_") +
                    kItemNames[product]);
  }
  for (int product = 0; product < kNumProducts; ++product) {
    names.push_back(std::string("market_inventory_delta_") +
                    kItemNames[product]);
  }
  names.insert(names.end(), {"opponent_land_delta", "opponent_crop_delta",
                             "opponent_animal_delta", "task_successes",
                             "task_failures"});
  if (static_cast<int>(names.size()) != kJournalFeatureCount) {
    throw std::logic_error(
        "structured-plan journal name count mismatch");
  }
  return names;
}

std::vector<std::string> EventNames() {
  std::vector<std::string> names(kEventCount, "RESERVED");
  names[0] = "INITIAL";
  names[1] = "DAY_START";
  names[2] = "PORTFOLIO_TARGET_REACHED";
  names[3] = "PORTFOLIO_EXPIRED";
  names[4] = "EXECUTION_FAILURE";
  names[5] = "LIFECYCLE_CHANGED";
  names[6] = "TOWN_SHOP_UNLOCKED";
  names[7] = "MARKET_TARGET_MISSED";
  names[8] = "MARKET_SLOTS_TRUNCATED";
  for (int crop = 0; crop < kNumCrops; ++crop) {
    names[9 + crop] = std::string("CROP_READY_") + kItemNames[crop];
  }
  for (int animal = 0; animal < kNumAnimals; ++animal) {
    names[14 + animal] =
        std::string("ANIMAL_READY_") +
        kItemNames[item::kGoose + animal];
  }
  names[17] = "INVENTORY_BAND_CROSSED";
  names[18] = "PRICE_BAND_CROSSED";
  names[19] = "OPPONENT_LAND_BAND_CROSSED";
  names[20] = "OPPONENT_CROP_BAND_CROSSED";
  names[21] = "OPPONENT_ANIMAL_BAND_CROSSED";
  names[22] = "BUDGET_TRUNCATED";
  return names;
}

}  // namespace kagg::plans
