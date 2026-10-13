#include "policy_session.hpp"

#include <pybind11/numpy.h>
#include <pybind11/pybind11.h>

#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <exception>
#include <limits>
#include <mutex>
#include <optional>
#include <string>
#include <vector>

#include "action_codec.hpp"
#include "actor_encoding.hpp"
#include "derived_facts.hpp"
#include "engine.hpp"
#include "policy_gpu_state.hpp"
#include "py_convert.hpp"
#include "unit_phase.hpp"

namespace py = pybind11;

namespace kagg {
namespace {

int ShopIndex(const std::string& name) {
  for (int index = 0; index < kNumShops; ++index) {
    if (name == kShops[index].name) return index;
  }
  return -1;
}

template <typename T>
py::array_t<T> MakeArray(std::initializer_list<py::ssize_t> shape) {
  return py::array_t<T>(std::vector<py::ssize_t>(shape));
}

template <typename Function>
std::exception_ptr ParallelFor(int count, int workers, Function function) {
#ifndef _OPENMP
  static_cast<void>(workers);
#endif
  std::exception_ptr first_error;
  std::mutex error_mutex;
#ifdef _OPENMP
#pragma omp parallel for schedule(static) num_threads(workers)
#endif
  for (int index = 0; index < count; ++index) {
    try {
      function(index);
    } catch (...) {
      std::lock_guard<std::mutex> lock(error_mutex);
      if (!first_error) first_error = std::current_exception();
    }
  }
  return first_error;
}

std::array<int64_t, kNumProducts> ParseProductBounds(
    const py::object& value, const char* name, int64_t default_value) {
  std::array<int64_t, kNumProducts> result{};
  if (value.is_none()) {
    result.fill(default_value);
    return result;
  }
  const auto array = py::array_t<int64_t,
                                 py::array::c_style | py::array::forcecast>(value);
  const py::buffer_info info = array.request();
  if (info.ndim != 1 || info.shape[0] != kNumProducts) {
    throw py::value_error(std::string(name) + " must have one value per product");
  }
  const auto* data = static_cast<const int64_t*>(info.ptr);
  for (int product = 0; product < kNumProducts; ++product) {
    if (data[product] < 0) {
      throw py::value_error(std::string(name) + " cannot contain negative values");
    }
    result[product] = data[product];
  }
  return result;
}

using IntArray =
    py::array_t<int64_t, py::array::c_style | py::array::forcecast>;
using ByteArray =
    py::array_t<uint8_t, py::array::c_style | py::array::forcecast>;

class PolicySession {
 public:
  PolicySession(const py::dict& observation, py::object configuration, int unit_limit)
      : config_(pyconv::ParseConfig(configuration)), unit_limit_(unit_limit) {
    if (unit_limit_ < 1) throw py::value_error("unit_limit must be positive");
    player_ = py::cast<int>(observation["player"]);
    if (player_ < 0 || player_ > 1) {
      throw py::value_error("observation player must be 0 or 1");
    }
    step_ = py::cast<int>(observation["step"]);
    const auto farms = py::reinterpret_borrow<py::list>(observation["farms"]);
    own_farm_ = pyconv::ParseFarm(
        py::reinterpret_borrow<py::dict>(farms[player_]), config_.board_size);
    opponent_farm_ = pyconv::ParseFarm(
        py::reinterpret_borrow<py::dict>(farms[1 - player_]), config_.board_size);
    own_private_ =
        pyconv::ParsePrivate(py::reinterpret_borrow<py::dict>(observation["private"]));
    const auto market = py::reinterpret_borrow<py::dict>(observation["market"]);
    const auto inventory = py::reinterpret_borrow<py::dict>(market["inventory"]);
    const auto prices = py::reinterpret_borrow<py::dict>(market["prices"]);
    for (int product = 0; product < kNumProducts; ++product) {
      market_.inventory[product] = py::cast<int64_t>(inventory[kItemNames[product]]);
      market_.prices[product] = py::cast<int64_t>(prices[kItemNames[product]]);
    }
    shop_counts_.fill(0);
    const auto town = py::reinterpret_borrow<py::dict>(observation["town"]);
    for (py::handle value :
         py::reinterpret_borrow<py::list>(town["unlocked_shops"])) {
      const int shop = ShopIndex(py::cast<std::string>(value));
      if (shop >= 0) ++shop_counts_[shop];
    }
    unit_count_ = std::min<int>(1 + static_cast<int>(own_farm_.hands.size()),
                                unit_limit_);
    projected_unit_count_ = unit_count_;
    unit_farm_ = own_farm_;
    unit_private_ = own_private_;
  }

  PolicySession(const Engine& engine, int player, int unit_limit)
      : config_(engine.config()),
        player_(player),
        step_(engine.step_index()),
        unit_limit_(unit_limit) {
    if (unit_limit_ < 1) throw py::value_error("unit_limit must be positive");
    if (player_ < 0 || player_ > 1) {
      throw py::value_error("player must be 0 or 1");
    }
    own_farm_ = engine.farm(player_);
    opponent_farm_ = engine.farm(1 - player_);
    own_private_ = engine.priv(player_);
    market_ = engine.market();
    shop_counts_.fill(0);
    for (const int shop : engine.town_shops()) ++shop_counts_[shop];
    unit_count_ = std::min<int>(1 + static_cast<int>(own_farm_.hands.size()),
                                unit_limit_);
    projected_unit_count_ = unit_count_;
    unit_farm_ = own_farm_;
    unit_private_ = own_private_;
  }

  py::tuple Encode() const {
    const int board_size = config_.board_size;
    auto board = MakeArray<float>(
        {2, actor::kBoardChannels, board_size, board_size});
    auto units = MakeArray<float>({2, unit_limit_, actor::kUnitFeat});
    auto global = MakeArray<float>({actor::kGlobalFeat});
    {
      py::gil_scoped_release release;
      EncodeTo(board.mutable_data(), units.mutable_data(), global.mutable_data());
    }
    return py::make_tuple(std::move(board), std::move(units), std::move(global));
  }

  py::array_t<uint8_t> LegalMask() const {
    auto result = MakeArray<uint8_t>({policy::kActionTokens});
    {
      py::gil_scoped_release release;
      FillLegalMask(result.mutable_data());
    }
    return result;
  }

  py::array_t<float> TurnFacts(py::object lower, py::object upper) const {
    const auto lower_bounds = ParseProductBounds(lower, "lower bounds", 0);
    const auto upper_bounds = ParseProductBounds(
        upper, "upper bounds", std::numeric_limits<int64_t>::max());
    for (int product = 0; product < kNumProducts; ++product) {
      if (lower_bounds[product] > upper_bounds[product]) {
        throw py::value_error("opponent lower bound exceeds upper bound");
      }
    }
    int tokens = 0;
    const std::vector<float> values =
        TurnFactValues(lower_bounds, upper_bounds, &tokens);
    auto result = MakeArray<float>({tokens, facts::kTurnFactFeatures});
    std::copy(values.begin(), values.end(), result.mutable_data());
    return result;
  }

  py::array_t<float> PrefixFacts() const {
    const auto values = facts::EncodePrefixFacts(
        FactView(), tokens_, quantities_, unit_count_, phase_, market_slots_);
    auto result = MakeArray<float>({facts::kPrefixFactFeatures});
    std::copy(values.begin(), values.end(), result.mutable_data());
    return result;
  }

  py::array_t<float> CandidateFacts() const {
    const std::vector<float> values = facts::EncodeCandidateFacts(
        FactView(), tokens_, quantities_, unit_count_, phase_, unit_index_,
        market_slots_);
    auto result = MakeArray<float>(
        {policy::kActionTokens, facts::kCandidateFactFeatures});
    std::copy(values.begin(), values.end(), result.mutable_data());
    return result;
  }

  py::dict FlowSnapshot() const {
    const facts::FlowSnapshot snapshot = FlowSnapshotValue();
    auto market = MakeArray<int64_t>({kNumProducts});
    auto town = MakeArray<int64_t>({kNumProducts});
    auto unit_gain = MakeArray<int64_t>({kNumProducts});
    for (int product = 0; product < kNumProducts; ++product) {
      market.mutable_at(product) = snapshot.market_inventory[product];
      town.mutable_at(product) = snapshot.town_consumption[product];
      unit_gain.mutable_at(product) = snapshot.opponent_unit_gain_upper[product];
    }
    py::dict result;
    result["step"] = snapshot.step;
    result["market_inventory"] = std::move(market);
    result["town_consumption"] = std::move(town);
    result["opponent_unit_gain_upper"] = std::move(unit_gain);
    return result;
  }

  py::array_t<int64_t> MarketFlowBounds() const {
    const auto values = MarketFlowBoundsValue();
    auto result = MakeArray<int64_t>({kNumProducts, 2});
    for (int product = 0; product < kNumProducts; ++product) {
      result.mutable_at(product, 0) = values[product][0];
      result.mutable_at(product, 1) = values[product][1];
    }
    return result;
  }

  void Select(int token, int64_t quantity) {
    if (phase_ == 2) throw py::value_error("numeric action is already complete");
    if (token < 0 || token >= policy::kActionTokens) {
      throw py::value_error("numeric action token is out of range");
    }
    if (policy::TokenHasQuantity(token) && quantity <= 0) {
      throw py::value_error("numeric action token requires a positive quantity");
    }
    if (phase_ == 0 && !policy::IsUnitToken(token)) {
      throw py::value_error("market token selected during the unit phase");
    }
    if (phase_ == 0 && !UnitLegal(token)) {
      throw py::value_error("unit token is physically illegal for the current prefix");
    }
    if (phase_ == 1 && !policy::IsMarketToken(token)) {
      throw py::value_error("unit token selected during the market phase");
    }
    if (phase_ == 1 && token == policy::kMarketHireToken &&
        projected_unit_count_ >= unit_limit_) {
      throw py::value_error("HIRE exceeds the actor unit capacity");
    }
    tokens_.push_back(token);
    quantities_.push_back(quantity);
    if (phase_ == 0) {
      const UnitAction action = policy::DecodeUnitToken(token, quantity);
      const UnitActionTrace trace = ApplyUnitAction(
          config_, &unit_farm_, &unit_private_, unit_index_, action,
          step_ / config_.turns_per_day);
      if (trace.status != UnitActionStatus::kApplied &&
          trace.status != UnitActionStatus::kPass) {
        throw std::logic_error(
            "legal policy token failed incremental unit application");
      }
      ++unit_index_;
      if (unit_index_ >= unit_count_) phase_ = 1;
      return;
    }
    if (token == policy::kMarketStopToken) {
      phase_ = 2;
      return;
    }
    if (token == policy::kMarketHireToken) ++projected_unit_count_;
    ++market_slots_;
    if (market_slots_ >= config_.max_market_orders) phase_ = 2;
  }

  void SelectCompiledUnitPrefix(const int64_t* tokens,
                                const int64_t* quantities, int count) {
    if (phase_ != 0 || !tokens_.empty() || unit_index_ != 0) {
      throw py::value_error(
          "compiled unit prefix requires a fresh unit-phase session");
    }
    if (count != unit_count_) {
      throw py::value_error(
          "compiled unit prefix must contain exactly one token per unit");
    }
    for (int unit = 0; unit < count; ++unit) {
      const int token = static_cast<int>(tokens[unit]);
      const int64_t quantity = quantities[unit];
      if (!policy::IsUnitToken(token)) {
        throw py::value_error("compiled unit prefix contains a market token");
      }
      if (policy::TokenHasQuantity(token) && quantity <= 0) {
        throw py::value_error(
            "compiled unit prefix contains a non-positive quantity");
      }
    }
    const PlayerAction requested = policy::DecodePlayerAction(
        tokens, quantities, count, unit_count_, config_.max_market_orders);
    const UnitPhaseResult compiled = CompileUnitPhase(
        config_, unit_farm_, unit_private_, requested,
        step_ / std::max(1, config_.turns_per_day));
    unit_farm_ = compiled.farm;
    unit_private_ = compiled.priv;
    tokens_.assign(tokens, tokens + count);
    quantities_.assign(quantities, quantities + count);
    unit_index_ = unit_count_;
    phase_ = 1;
  }

  void SelectCompiledUnits(IntArray tokens, IntArray quantities) {
    const py::buffer_info token_info = tokens.request();
    const py::buffer_info quantity_info = quantities.request();
    if (token_info.ndim != 1 || token_info.shape[0] != unit_count_ ||
        quantity_info.ndim != 1 || quantity_info.shape != token_info.shape) {
      throw py::value_error(
          "compiled unit tokens and quantities must have shape [unit_count]");
    }
    SelectCompiledUnitPrefix(
        static_cast<const int64_t*>(token_info.ptr),
        static_cast<const int64_t*>(quantity_info.ptr), unit_count_);
  }

  void WriteCompiledUnitInputs(const int64_t* tokens,
                               const int64_t* quantities, int count,
                               float* prefix_facts,
                               float* candidate_facts,
                               int64_t* gpu_states) const {
    if (phase_ != 0 || !tokens_.empty() || unit_index_ != 0) {
      throw std::invalid_argument(
          "compiled unit inputs require a fresh unit-phase session");
    }
    if (count != unit_count_) {
      throw std::invalid_argument(
          "compiled unit inputs require exactly one token per unit");
    }
    const policy_gpu::Layout layout =
        policy_gpu::MakeLayout(config_.board_size, unit_limit_);
    std::vector<int64_t> prefix_tokens;
    std::vector<int64_t> prefix_quantities;
    prefix_tokens.reserve(static_cast<size_t>(count));
    prefix_quantities.reserve(static_cast<size_t>(count));
    for (int unit = 0; unit < count; ++unit) {
      const int token = static_cast<int>(tokens[unit]);
      const int64_t quantity = quantities[unit];
      if (!policy::IsUnitToken(token)) {
        throw std::invalid_argument(
            "compiled unit inputs contain a market token");
      }
      if (policy::TokenHasQuantity(token) && quantity <= 0) {
        throw std::invalid_argument(
            "compiled unit inputs contain a non-positive quantity");
      }
      if (prefix_facts != nullptr && candidate_facts != nullptr) {
        const auto prefix = facts::EncodePrefixFacts(
            FactView(), prefix_tokens, prefix_quantities, unit_count_, 0, 0);
        std::copy(prefix.begin(), prefix.end(),
                  prefix_facts + static_cast<size_t>(unit) *
                                     facts::kPrefixFactFeatures);
        const std::vector<float> candidates = facts::EncodeCandidateFacts(
            FactView(), prefix_tokens, prefix_quantities, unit_count_, 0,
            unit, 0);
        std::copy(candidates.begin(), candidates.end(),
                  candidate_facts + static_cast<size_t>(unit) *
                                        policy::kActionTokens *
                                        facts::kCandidateFactFeatures);
      }
      if (gpu_states != nullptr) {
        const PlayerAction partial = policy::DecodePlayerAction(
            prefix_tokens.data(), prefix_quantities.data(),
            static_cast<int>(prefix_tokens.size()), unit_count_,
            config_.max_market_orders);
        const UnitPhaseResult projected = CompileUnitPhase(
            config_, own_farm_, own_private_, partial,
            step_ / std::max(1, config_.turns_per_day));
        PolicySession state = *this;
        state.unit_farm_ = projected.farm;
        state.unit_private_ = projected.priv;
        state.tokens_ = prefix_tokens;
        state.quantities_ = prefix_quantities;
        state.unit_index_ = unit;
        state.WriteGpuState(
            layout, gpu_states + static_cast<size_t>(unit) * layout.width);
      }
      prefix_tokens.push_back(token);
      prefix_quantities.push_back(quantity);
    }
  }

  void WriteDecisionFacts(float* prefix_facts,
                          float* candidate_facts) const {
    const auto prefix = facts::EncodePrefixFacts(
        FactView(), tokens_, quantities_, unit_count_, phase_, market_slots_);
    std::copy(prefix.begin(), prefix.end(), prefix_facts);
    const std::vector<float> candidates = facts::EncodeCandidateFacts(
        FactView(), tokens_, quantities_, unit_count_, phase_, unit_index_,
        market_slots_);
    std::copy(candidates.begin(), candidates.end(), candidate_facts);
  }

  py::dict Action() const {
    if (phase_ != 2) throw py::value_error("numeric action is incomplete");
    const PlayerAction action = policy::DecodePlayerAction(
        tokens_.data(), quantities_.data(), static_cast<int>(tokens_.size()),
        unit_count_, config_.max_market_orders);
    return pyconv::PlayerActionToPy(action);
  }

  int phase() const { return phase_; }
  int unit_count() const { return unit_count_; }
  int decision_count() const { return static_cast<int>(tokens_.size()); }
  int board_size() const { return config_.board_size; }
  int unit_limit() const { return unit_limit_; }

  facts::FlowSnapshot FlowSnapshotValue() const {
    return facts::MakeFlowSnapshot(FactView());
  }

  std::vector<float> TurnFactValues(
      const std::array<int64_t, kNumProducts>& lower,
      const std::array<int64_t, kNumProducts>& upper, int* tokens) const {
    return facts::EncodeTurnFacts(FactView(), lower, upper, tokens);
  }

  std::array<std::array<int64_t, 2>, kNumProducts>
  MarketFlowBoundsValue() const {
    return facts::OwnMarketFlowBounds(tokens_, quantities_, unit_count_);
  }

  py::array_t<int64_t> GpuState() const {
    const policy_gpu::Layout layout =
        policy_gpu::MakeLayout(config_.board_size, unit_limit_);
    auto state = MakeArray<int64_t>({layout.width});
    WriteGpuState(layout, state.mutable_data());
    return state;
  }

  template <typename State>
  void WriteGpuState(const policy_gpu::Layout& layout, State* output) const {
    std::fill(output, output + layout.width, State{0});
    std::fill(output + layout.inventory_order, output + layout.shed, State{-1});
    output[policy_gpu::kDay] = step_ / config_.turns_per_day;
    output[policy_gpu::kUnitCount] = projected_unit_count_;
    output[policy_gpu::kUnitIndex] = unit_index_;
    output[policy_gpu::kMarketSlots] = market_slots_;
    output[policy_gpu::kPhase] = phase_;
    output[policy_gpu::kShedCapacity] = config_.shed_capacity;
    output[policy_gpu::kMaxMarketOrders] = config_.max_market_orders;
    output[policy_gpu::kBoardSize] = config_.board_size;
    output[policy_gpu::kShedTotal] = ShedTotal(unit_private_);
    output[policy_gpu::kMoney] = static_cast<State>(unit_farm_.money);
    output[policy_gpu::kHiresToday] = unit_farm_.hires_today;
    output[policy_gpu::kExtraUnlocked] = unit_farm_.extra_unlocked;
    output[policy_gpu::kFarmHandCostMultiplier] =
        static_cast<State>(config_.farm_hand_cost_mult);
    output[policy_gpu::kMarketProjectionConditional] = 0;

    for (int unit = 0; unit < unit_count_; ++unit) {
      const int x = unit == 0 ? unit_farm_.farmer_x
                              : unit_farm_.hands[unit - 1].first;
      const int y = unit == 0 ? unit_farm_.farmer_y
                              : unit_farm_.hands[unit - 1].second;
      output[layout.positions + unit * 2] = x;
      output[layout.positions + unit * 2 + 1] = y;
      if (unit >= static_cast<int>(unit_private_.inventories.size())) continue;
      const Inventory& inventory = unit_private_.inventories[unit];
      for (size_t order = 0; order < inventory.items.size(); ++order) {
        const auto [item, count] = inventory.items[order];
        output[layout.inventories + unit * kNumItems + item] = count;
        output[layout.inventory_order + unit * kNumItems + order] = item;
      }
    }
    for (int item = 0; item < kNumItems; ++item) {
      output[layout.shed + item] = unit_private_.shed[item];
    }
    for (int crop = 0; crop < kNumCrops; ++crop) {
      output[layout.seeds + crop] = unit_private_.seeds[crop];
      output[layout.seed_costs + crop] = kCrops[crop].seed_cost;
    }
    for (int product = 0; product < kNumProducts; ++product) {
      const MarketParams& params = config_.market_params[product];
      output[layout.market_inventory + product] = market_.inventory[product];
      output[layout.market_prices + product] = market_.prices[product];
      output[layout.market_base_milli + product] =
          static_cast<State>(std::llround(params.base * 1000.0));
      output[layout.market_i0 + product] = params.i0;
      output[layout.market_t_milli + product] =
          static_cast<State>(std::llround(params.t * 1000.0));
      output[layout.market_below_function + product] =
          static_cast<int>(params.below_func);
      output[layout.market_below_target_milli + product] =
          static_cast<State>(std::llround(params.below_target * 1000.0));
      output[layout.market_above_function + product] =
          static_cast<int>(params.above_func);
      output[layout.market_above_target_milli + product] =
          static_cast<State>(std::llround(params.above_target * 1000.0));
    }
    for (int animal = 0; animal < kNumAnimals; ++animal) {
      output[layout.animal_costs + animal] = kAnimals[animal].cost;
    }
    for (int land = 0; land < static_cast<int>(kLandPrices.size()); ++land) {
      output[layout.land_costs + land] = kLandPrices[land];
    }
    for (size_t index = 0; index < unit_farm_.tiles.size(); ++index) {
      const Tile& tile = unit_farm_.tiles[index];
      State* fields =
          output + layout.tiles + index * policy_gpu::kTileFields;
      fields[policy_gpu::kKind] = static_cast<int>(tile.kind);
      fields[policy_gpu::kCrop] = tile.crop;
      fields[policy_gpu::kPlantedDay] = tile.planted_day;
      fields[policy_gpu::kWateredToday] = tile.watered_today ? 1 : 0;
      fields[policy_gpu::kFertilizedUntilDay] = tile.fertilized_until_day;
      fields[policy_gpu::kYieldUnits] = tile.yield_units;
      fields[policy_gpu::kStructure] = static_cast<int>(tile.structure);
      fields[policy_gpu::kHasAnimal] = tile.has_animal ? 1 : 0;
      fields[policy_gpu::kAnimal] = tile.animal;
      fields[policy_gpu::kFedToday] = tile.fed_today ? 1 : 0;
      fields[policy_gpu::kCaredToday] = tile.cared_today ? 1 : 0;
      fields[policy_gpu::kFertilizerAvailable] =
          tile.fertilizer_available ? 1 : 0;
    }
  }

  void EncodeTo(float* board, float* units, float* global) const {
    const size_t board_stride = static_cast<size_t>(actor::kBoardChannels) *
                                config_.board_size * config_.board_size;
    const size_t unit_stride =
        static_cast<size_t>(unit_limit_) * actor::kUnitFeat;
    actor::EncodeBoard(config_, own_farm_, step_, board);
    actor::EncodeBoard(config_, opponent_farm_, step_, board + board_stride);
    actor::EncodeUnits(config_, own_farm_, &own_private_, step_, unit_limit_,
                       units);
    actor::EncodeUnits(config_, opponent_farm_, nullptr, step_, unit_limit_,
                       units + unit_stride);
    actor::SeatView view;
    view.config = &config_;
    view.step = step_;
    view.own_farm = &own_farm_;
    view.opponent_farm = &opponent_farm_;
    view.own_private = &own_private_;
    view.market_inventory = market_.inventory;
    view.market_prices = market_.prices;
    view.shop_counts = shop_counts_;
    actor::EncodeGlobal(view, global);
  }

  void EncodeCompactTo(std::uint16_t* board, std::uint16_t* units,
                       float* global) const {
    const size_t board_stride = static_cast<size_t>(actor::kBoardChannels) *
                                config_.board_size * config_.board_size;
    const size_t unit_stride =
        static_cast<size_t>(unit_limit_) * actor::kUnitFeat;
    actor::EncodeBoardHalf(config_, own_farm_, step_, board);
    actor::EncodeBoardHalf(config_, opponent_farm_, step_,
                           board + board_stride);
    actor::EncodeUnitsHalf(config_, own_farm_, &own_private_, step_,
                           unit_limit_, units);
    actor::EncodeUnitsHalf(config_, opponent_farm_, nullptr, step_,
                           unit_limit_, units + unit_stride);
    actor::SeatView view;
    view.config = &config_;
    view.step = step_;
    view.own_farm = &own_farm_;
    view.opponent_farm = &opponent_farm_;
    view.own_private = &own_private_;
    view.market_inventory = market_.inventory;
    view.market_prices = market_.prices;
    view.shop_counts = shop_counts_;
    actor::EncodeGlobal(view, global);
  }

  void FillLegalMask(uint8_t* data) const {
    std::fill(data, data + policy::kActionTokens, 0);
    if (phase_ == 0) {
      for (int token = 0; token < policy::kUnitActionTokens; ++token) {
        data[token] = UnitLegal(token) ? 1 : 0;
      }
    } else if (phase_ == 1) {
      std::fill(data + policy::kUnitActionTokens,
                data + policy::kActionTokens, 1);
      if (projected_unit_count_ >= unit_limit_) {
        data[policy::kMarketHireToken] = 0;
      }
    }
  }

 private:
  facts::View FactView() const {
    return facts::View{config_,       own_farm_, opponent_farm_, own_private_,
                       market_,       shop_counts_, step_,       unit_limit_};
  }

  bool UnitLegal(int token) const {
    return WouldApplyUnitAction(
        config_, unit_farm_, unit_private_, unit_index_,
        policy::DecodeUnitToken(token, 1), step_ / config_.turns_per_day);
  }

  Config config_;
  int player_ = 0;
  int step_ = 0;
  int unit_limit_ = 1;
  int unit_count_ = 1;
  int projected_unit_count_ = 1;
  int unit_index_ = 0;
  int market_slots_ = 0;
  int phase_ = 0;
  Farm own_farm_;
  Farm opponent_farm_;
  PrivateState own_private_;
  MarketState market_;
  Farm unit_farm_;
  PrivateState unit_private_;
  std::array<int, kNumShops> shop_counts_{};
  std::vector<int64_t> tokens_;
  std::vector<int64_t> quantities_;
};

class PolicySessionBatch {
 public:
  PolicySessionBatch(py::list owners, int workers)
      : owners_(std::move(owners)), workers_(workers) {
    if (py::len(owners_) < 1) {
      throw py::value_error("policy session batch cannot be empty");
    }
    sessions_.reserve(static_cast<size_t>(py::len(owners_)));
    for (py::handle owner : owners_) {
      sessions_.push_back(&py::cast<PolicySession&>(owner));
    }
    Initialize();
  }

  PolicySessionBatch(std::vector<PolicySession> sessions, int workers)
      : owned_sessions_(std::move(sessions)), workers_(workers) {
    sessions_.reserve(owned_sessions_.size());
    for (PolicySession& session : owned_sessions_) {
      sessions_.push_back(&session);
    }
    Initialize();
  }

  void Initialize() {
    if (sessions_.empty()) {
      throw py::value_error("policy session batch cannot be empty");
    }
    if (workers_ < 1 || workers_ > 256) {
      throw py::value_error("policy session batch workers must be in [1, 256]");
    }
    board_size_ = sessions_.front()->board_size();
    unit_limit_ = sessions_.front()->unit_limit();
    for (const PolicySession* session : sessions_) {
      if (session->board_size() != board_size_ ||
          session->unit_limit() != unit_limit_) {
        throw py::value_error(
            "policy session batch requires one tensor architecture");
      }
    }
  }

  py::tuple Encode() const {
    const py::ssize_t batch = static_cast<py::ssize_t>(sessions_.size());
    auto board = MakeArray<float>(
        {batch, 2, actor::kBoardChannels, board_size_, board_size_});
    auto units =
        MakeArray<float>({batch, 2, unit_limit_, actor::kUnitFeat});
    auto global = MakeArray<float>({batch, actor::kGlobalFeat});
    const size_t board_stride = static_cast<size_t>(2) *
                                actor::kBoardChannels * board_size_ * board_size_;
    const size_t unit_stride =
        static_cast<size_t>(2) * unit_limit_ * actor::kUnitFeat;
    const size_t global_stride = actor::kGlobalFeat;
    float* board_data = board.mutable_data();
    float* unit_data = units.mutable_data();
    float* global_data = global.mutable_data();
    const std::exception_ptr error = Run([&](int index) {
      sessions_[index]->EncodeTo(
          board_data + static_cast<size_t>(index) * board_stride,
          unit_data + static_cast<size_t>(index) * unit_stride,
          global_data + static_cast<size_t>(index) * global_stride);
    });
    if (error) std::rethrow_exception(error);
    return py::make_tuple(std::move(board), std::move(units),
                          std::move(global));
  }

  py::tuple EncodeCompact() const {
    const py::ssize_t batch = static_cast<py::ssize_t>(sessions_.size());
    py::array board(
        py::dtype("float16"),
        std::vector<py::ssize_t>{batch, 2, actor::kBoardChannels, board_size_,
                                 board_size_});
    py::array units(
        py::dtype("float16"),
        std::vector<py::ssize_t>{batch, 2, unit_limit_, actor::kUnitFeat});
    auto global = MakeArray<float>({batch, actor::kGlobalFeat});
    const size_t board_stride = static_cast<size_t>(2) *
                                actor::kBoardChannels * board_size_ * board_size_;
    const size_t unit_stride =
        static_cast<size_t>(2) * unit_limit_ * actor::kUnitFeat;
    const size_t global_stride = actor::kGlobalFeat;
    auto* board_data = static_cast<std::uint16_t*>(board.mutable_data());
    auto* unit_data = static_cast<std::uint16_t*>(units.mutable_data());
    float* global_data = global.mutable_data();
    const std::exception_ptr error = Run([&](int index) {
      sessions_[index]->EncodeCompactTo(
          board_data + static_cast<size_t>(index) * board_stride,
          unit_data + static_cast<size_t>(index) * unit_stride,
          global_data + static_cast<size_t>(index) * global_stride);
    });
    if (error) std::rethrow_exception(error);
    return py::make_tuple(std::move(board), std::move(units),
                          std::move(global));
  }

  py::array_t<int64_t> Phases() const {
    auto phases = MakeArray<int64_t>(
        {static_cast<py::ssize_t>(sessions_.size())});
    for (size_t index = 0; index < sessions_.size(); ++index) {
      phases.mutable_at(index) = sessions_[index]->phase();
    }
    return phases;
  }

  py::array_t<int64_t> UnitCounts() const {
    auto counts = MakeArray<int64_t>(
        {static_cast<py::ssize_t>(sessions_.size())});
    for (size_t index = 0; index < sessions_.size(); ++index) {
      counts.mutable_at(index) = sessions_[index]->unit_count();
    }
    return counts;
  }

  py::array_t<uint8_t> LegalMasks() const {
    auto masks = MakeArray<uint8_t>(
        {static_cast<py::ssize_t>(sessions_.size()), policy::kActionTokens});
    uint8_t* mask_data = masks.mutable_data();
    const std::exception_ptr error = Run([&](int index) {
      sessions_[index]->FillLegalMask(
          mask_data + static_cast<size_t>(index) * policy::kActionTokens);
    });
    if (error) std::rethrow_exception(error);
    return masks;
  }

  py::tuple DecisionInputs() const {
    const py::ssize_t batch = static_cast<py::ssize_t>(sessions_.size());
    auto phases = MakeArray<int64_t>({batch});
    auto masks = MakeArray<uint8_t>({batch, policy::kActionTokens});
    int64_t* phase_data = phases.mutable_data();
    uint8_t* mask_data = masks.mutable_data();
    const std::exception_ptr error = Run([&](int index) {
      phase_data[index] = sessions_[index]->phase();
      sessions_[index]->FillLegalMask(
          mask_data + static_cast<size_t>(index) * policy::kActionTokens);
    });
    if (error) std::rethrow_exception(error);
    return py::make_tuple(std::move(phases), std::move(masks));
  }

  py::array_t<int64_t> GpuState() const {
    const py::ssize_t batch = static_cast<py::ssize_t>(sessions_.size());
    const policy_gpu::Layout layout =
        policy_gpu::MakeLayout(board_size_, unit_limit_);
    auto state = MakeArray<int64_t>({batch, layout.width});
    int64_t* data = state.mutable_data();
    const std::exception_ptr error = Run([&](int index) {
      sessions_[index]->WriteGpuState(
          layout, data + static_cast<size_t>(index) * layout.width);
    });
    if (error) std::rethrow_exception(error);
    return state;
  }

  py::array_t<int32_t> GpuStateCompact() const {
    const py::ssize_t batch = static_cast<py::ssize_t>(sessions_.size());
    const policy_gpu::Layout layout =
        policy_gpu::MakeLayout(board_size_, unit_limit_);
    auto state = MakeArray<int32_t>({batch, layout.width});
    int32_t* data = state.mutable_data();
    const std::exception_ptr error = Run([&](int index) {
      sessions_[index]->WriteGpuState(
          layout, data + static_cast<size_t>(index) * layout.width);
    });
    if (error) std::rethrow_exception(error);
    return state;
  }

  py::dict FlowSnapshots() const {
    const py::ssize_t batch = static_cast<py::ssize_t>(sessions_.size());
    auto steps = MakeArray<int64_t>({batch});
    auto market = MakeArray<int64_t>({batch, kNumProducts});
    auto town = MakeArray<int64_t>({batch, kNumProducts});
    auto unit_gain = MakeArray<int64_t>({batch, kNumProducts});
    const std::exception_ptr error = Run([&](int index) {
      const facts::FlowSnapshot snapshot =
          sessions_[index]->FlowSnapshotValue();
      steps.mutable_at(index) = snapshot.step;
      for (int product = 0; product < kNumProducts; ++product) {
        market.mutable_at(index, product) = snapshot.market_inventory[product];
        town.mutable_at(index, product) = snapshot.town_consumption[product];
        unit_gain.mutable_at(index, product) =
            snapshot.opponent_unit_gain_upper[product];
      }
    });
    if (error) std::rethrow_exception(error);
    py::dict result;
    result["step"] = std::move(steps);
    result["market_inventory"] = std::move(market);
    result["town_consumption"] = std::move(town);
    result["opponent_unit_gain_upper"] = std::move(unit_gain);
    return result;
  }

  py::dict TurnFactsBatch(IntArray lower, IntArray upper) const {
    const py::buffer_info lower_info = lower.request();
    const py::buffer_info upper_info = upper.request();
    const py::ssize_t batch = static_cast<py::ssize_t>(sessions_.size());
    if (lower_info.ndim != 2 || lower_info.shape[0] != batch ||
        lower_info.shape[1] != kNumProducts ||
        upper_info.shape != lower_info.shape) {
      throw py::value_error(
          "batched turn-fact bounds require shape [B, products]");
    }
    const auto* lower_data = static_cast<const int64_t*>(lower_info.ptr);
    const auto* upper_data = static_cast<const int64_t*>(upper_info.ptr);
    std::vector<std::vector<float>> rows(static_cast<size_t>(batch));
    std::vector<int> counts(static_cast<size_t>(batch), 0);
    const std::exception_ptr error = Run([&](int index) {
      std::array<int64_t, kNumProducts> lower_values{};
      std::array<int64_t, kNumProducts> upper_values{};
      for (int product = 0; product < kNumProducts; ++product) {
        const size_t offset =
            static_cast<size_t>(index) * kNumProducts + product;
        lower_values[product] = lower_data[offset];
        upper_values[product] = upper_data[offset];
        if (lower_values[product] < 0 ||
            lower_values[product] > upper_values[product]) {
          throw std::invalid_argument("batched turn-fact bounds are invalid");
        }
      }
      rows[index] = sessions_[index]->TurnFactValues(
          lower_values, upper_values, &counts[index]);
    });
    if (error) std::rethrow_exception(error);
    const int maximum = *std::max_element(counts.begin(), counts.end());
    auto values = MakeArray<float>(
        {batch, maximum, facts::kTurnFactFeatures});
    auto count_values = MakeArray<int64_t>({batch});
    std::fill_n(values.mutable_data(), values.size(), 0.0F);
    for (py::ssize_t index = 0; index < batch; ++index) {
      count_values.mutable_at(index) = counts[index];
      std::copy(
          rows[index].begin(), rows[index].end(),
          values.mutable_data() + static_cast<size_t>(index) * maximum *
                                      facts::kTurnFactFeatures);
    }
    py::dict result;
    result["values"] = std::move(values);
    result["counts"] = std::move(count_values);
    return result;
  }

  py::array_t<int64_t> MarketFlowBoundsBatch() const {
    const py::ssize_t batch = static_cast<py::ssize_t>(sessions_.size());
    auto result = MakeArray<int64_t>({batch, kNumProducts, 2});
    const std::exception_ptr error = Run([&](int index) {
      const auto values = sessions_[index]->MarketFlowBoundsValue();
      for (int product = 0; product < kNumProducts; ++product) {
        result.mutable_at(index, product, 0) = values[product][0];
        result.mutable_at(index, product, 1) = values[product][1];
      }
    });
    if (error) std::rethrow_exception(error);
    return result;
  }

  void Select(IntArray tokens, IntArray quantities, ByteArray active) {
    const py::buffer_info token_info = tokens.request();
    const py::buffer_info quantity_info = quantities.request();
    const py::buffer_info active_info = active.request();
    const py::ssize_t batch = static_cast<py::ssize_t>(sessions_.size());
    if (token_info.ndim != 1 || token_info.shape[0] != batch ||
        quantity_info.ndim != 1 || quantity_info.shape != token_info.shape ||
        active_info.ndim != 1 || active_info.shape[0] != batch) {
      throw py::value_error(
          "batched policy selections require matching one-dimensional arrays");
    }
    const auto* token_data = static_cast<const int64_t*>(token_info.ptr);
    const auto* quantity_data = static_cast<const int64_t*>(quantity_info.ptr);
    const auto* active_data = static_cast<const uint8_t*>(active_info.ptr);
    const std::exception_ptr error = Run([&](int index) {
      if (active_data[index]) {
        sessions_[index]->Select(token_data[index], quantity_data[index]);
      }
    });
    if (error) std::rethrow_exception(error);
  }

  void SelectCompiledUnits(IntArray tokens, IntArray quantities,
                           IntArray unit_counts) {
    const py::buffer_info token_info = tokens.request();
    const py::buffer_info quantity_info = quantities.request();
    const py::buffer_info count_info = unit_counts.request();
    const py::ssize_t batch = static_cast<py::ssize_t>(sessions_.size());
    if (token_info.ndim != 2 || token_info.shape[0] != batch ||
        quantity_info.ndim != 2 || quantity_info.shape != token_info.shape ||
        count_info.ndim != 1 || count_info.shape[0] != batch) {
      throw py::value_error(
          "batched compiled units require [B,U] tokens and [B] counts");
    }
    const auto* token_data = static_cast<const int64_t*>(token_info.ptr);
    const auto* quantity_data =
        static_cast<const int64_t*>(quantity_info.ptr);
    const auto* count_data = static_cast<const int64_t*>(count_info.ptr);
    const int width = static_cast<int>(token_info.shape[1]);
    const std::exception_ptr error = Run([&](int index) {
      const int64_t count = count_data[index];
      if (count < 1 || count > width) {
        throw py::value_error(
            "compiled unit count lies outside the batched prefix width");
      }
      sessions_[index]->SelectCompiledUnitPrefix(
          token_data + static_cast<size_t>(index) * width,
          quantity_data + static_cast<size_t>(index) * width,
          static_cast<int>(count));
    });
    if (error) std::rethrow_exception(error);
  }

  void SelectSequences(IntArray tokens, IntArray quantities,
                       IntArray decision_counts, IntArray unit_counts) {
    const py::buffer_info token_info = tokens.request();
    const py::buffer_info quantity_info = quantities.request();
    const py::buffer_info count_info = decision_counts.request();
    const py::buffer_info unit_count_info = unit_counts.request();
    const py::ssize_t batch = static_cast<py::ssize_t>(sessions_.size());
    if (token_info.ndim != 2 || token_info.shape[0] != batch ||
        quantity_info.ndim != 2 || quantity_info.shape != token_info.shape ||
        count_info.ndim != 1 || count_info.shape[0] != batch ||
        unit_count_info.ndim != 1 || unit_count_info.shape[0] != batch) {
      throw py::value_error(
          "batched policy sequences require [B,D] actions and [B] counts");
    }
    const auto* token_data = static_cast<const int64_t*>(token_info.ptr);
    const auto* quantity_data =
        static_cast<const int64_t*>(quantity_info.ptr);
    const auto* count_data = static_cast<const int64_t*>(count_info.ptr);
    const auto* unit_count_data =
        static_cast<const int64_t*>(unit_count_info.ptr);
    const int width = static_cast<int>(token_info.shape[1]);
    const std::exception_ptr error = Run([&](int index) {
      const int64_t count = count_data[index];
      const int64_t unit_count = unit_count_data[index];
      if (count < 1 || count > width || unit_count < 1 ||
          unit_count > count) {
        throw std::invalid_argument(
            "policy decision count lies outside the sequence width");
      }
      const size_t offset = static_cast<size_t>(index) * width;
      sessions_[index]->SelectCompiledUnitPrefix(
          token_data + offset, quantity_data + offset,
          static_cast<int>(unit_count));
      for (int decision = static_cast<int>(unit_count); decision < count;
           ++decision) {
        sessions_[index]->Select(token_data[offset + decision],
                                 quantity_data[offset + decision]);
      }
      if (sessions_[index]->phase() != 2) {
        throw std::invalid_argument(
            "policy sequence ended before the session completed");
      }
    });
    if (error) std::rethrow_exception(error);
  }

  py::dict CompiledUnitInputs(IntArray tokens, IntArray quantities,
                              IntArray unit_counts, bool include_facts,
                              bool include_gpu_state) const {
    const py::buffer_info token_info = tokens.request();
    const py::buffer_info quantity_info = quantities.request();
    const py::buffer_info count_info = unit_counts.request();
    const py::ssize_t batch = static_cast<py::ssize_t>(sessions_.size());
    if (token_info.ndim != 2 || token_info.shape[0] != batch ||
        quantity_info.ndim != 2 || quantity_info.shape != token_info.shape ||
        count_info.ndim != 1 || count_info.shape[0] != batch) {
      throw py::value_error(
          "batched compiled inputs require [B,U] tokens and [B] counts");
    }
    const int width = static_cast<int>(token_info.shape[1]);
    const policy_gpu::Layout layout =
        policy_gpu::MakeLayout(board_size_, unit_limit_);
    std::optional<py::array_t<float>> prefix;
    std::optional<py::array_t<float>> candidates;
    std::optional<py::array_t<int64_t>> state;
    if (include_facts) {
      prefix.emplace(MakeArray<float>(
          {batch, width, facts::kPrefixFactFeatures}));
      candidates.emplace(MakeArray<float>(
          {batch, width, policy::kActionTokens,
           facts::kCandidateFactFeatures}));
      std::fill_n(prefix->mutable_data(), prefix->size(), 0.0F);
      std::fill_n(candidates->mutable_data(), candidates->size(), 0.0F);
    }
    if (include_gpu_state) {
      state.emplace(MakeArray<int64_t>({batch, width, layout.width}));
      std::fill_n(state->mutable_data(), state->size(), int64_t{0});
    }
    const auto* token_data = static_cast<const int64_t*>(token_info.ptr);
    const auto* quantity_data =
        static_cast<const int64_t*>(quantity_info.ptr);
    const auto* count_data = static_cast<const int64_t*>(count_info.ptr);
    const std::exception_ptr error = Run([&](int index) {
      const int64_t count = count_data[index];
      if (count < 1 || count > width) {
        throw std::invalid_argument(
            "compiled unit count lies outside the input width");
      }
      sessions_[index]->WriteCompiledUnitInputs(
          token_data + static_cast<size_t>(index) * width,
          quantity_data + static_cast<size_t>(index) * width,
          static_cast<int>(count),
          include_facts
              ? prefix->mutable_data() +
                    static_cast<size_t>(index) * width *
                        facts::kPrefixFactFeatures
              : nullptr,
          include_facts
              ? candidates->mutable_data() +
                    static_cast<size_t>(index) * width *
                        policy::kActionTokens *
                        facts::kCandidateFactFeatures
              : nullptr,
          include_gpu_state
              ? state->mutable_data() +
                    static_cast<size_t>(index) * width * layout.width
              : nullptr);
    });
    if (error) std::rethrow_exception(error);
    py::dict result;
    if (include_facts) {
      result["prefix_facts"] = std::move(*prefix);
      result["candidate_facts"] = std::move(*candidates);
    } else {
      result["prefix_facts"] = py::none();
      result["candidate_facts"] = py::none();
    }
    if (include_gpu_state) {
      result["gpu_state"] = std::move(*state);
    } else {
      result["gpu_state"] = py::none();
    }
    return result;
  }

  py::tuple DecisionFacts() const {
    const py::ssize_t batch = static_cast<py::ssize_t>(sessions_.size());
    auto prefix =
        MakeArray<float>({batch, facts::kPrefixFactFeatures});
    auto candidates = MakeArray<float>(
        {batch, policy::kActionTokens, facts::kCandidateFactFeatures});
    const std::exception_ptr error = Run([&](int index) {
      sessions_[index]->WriteDecisionFacts(
          prefix.mutable_data() + static_cast<size_t>(index) *
                                      facts::kPrefixFactFeatures,
          candidates.mutable_data() + static_cast<size_t>(index) *
                                          policy::kActionTokens *
                                          facts::kCandidateFactFeatures);
    });
    if (error) std::rethrow_exception(error);
    return py::make_tuple(std::move(prefix), std::move(candidates));
  }

  int size() const { return static_cast<int>(sessions_.size()); }
  int workers() const { return workers_; }

 private:
  template <typename Function>
  std::exception_ptr Run(Function function) const {
    std::exception_ptr error;
    {
      py::gil_scoped_release release;
      error = ParallelFor(size(), std::min(size(), workers_), function);
    }
    return error;
  }

  py::list owners_;
  std::vector<PolicySession> owned_sessions_;
  std::vector<PolicySession*> sessions_;
  int workers_;
  int board_size_ = 0;
  int unit_limit_ = 0;
};

struct EnginePolicyInputLayout {
  int count;
  int board_size;
  policy_gpu::Layout state;
};

EnginePolicyInputLayout ValidateEnginePolicyInputs(
    const std::vector<const Engine*>& engines, const std::vector<int>& players,
    int unit_limit, int workers) {
  const int count = static_cast<int>(engines.size());
  if (count < 1 || players.size() != engines.size()) {
    throw py::value_error("engine policy inputs must be nonempty and aligned");
  }
  if (unit_limit < 1) throw py::value_error("unit_limit must be positive");
  if (workers < 1 || workers > 256) {
    throw py::value_error("policy input workers must be in [1, 256]");
  }
  const Engine* first = engines.front();
  if (first == nullptr) {
    throw py::value_error("engine policy inputs contain a null engine");
  }
  const int board_size = first->config().board_size;
  for (int index = 0; index < count; ++index) {
    if (engines[index] == nullptr || players[index] < 0 || players[index] > 1) {
      throw py::value_error("engine policy inputs contain an invalid row");
    }
    if (engines[index]->config().board_size != board_size) {
      throw py::value_error("engine policy inputs require one board size");
    }
  }
  return EnginePolicyInputLayout{
      count, board_size, policy_gpu::MakeLayout(board_size, unit_limit)};
}

template <typename T, int Flags>
void ValidateOutputArray(const py::array_t<T, Flags>& value,
                         std::initializer_list<py::ssize_t> expected,
                         const char* name) {
  if (!value.writeable()) {
    throw py::value_error(std::string(name) + " must be writable");
  }
  if (value.ndim() != static_cast<py::ssize_t>(expected.size())) {
    throw py::value_error(std::string(name) + " has the wrong rank");
  }
  py::ssize_t axis = 0;
  for (const py::ssize_t size : expected) {
    if (value.shape(axis) != size) {
      throw py::value_error(std::string(name) + " has the wrong shape");
    }
    ++axis;
  }
}

void FillEnginePolicyTurnInputs(
    const std::vector<const Engine*>& engines, const std::vector<int>& players,
    int unit_limit, int workers, const EnginePolicyInputLayout& input_layout,
    float* board_data, float* unit_data, float* global_data,
    int64_t* count_data, int64_t* state_data) {
  const size_t board_stride =
      static_cast<size_t>(2) * actor::kBoardChannels *
      input_layout.board_size * input_layout.board_size;
  const size_t unit_stride =
      static_cast<size_t>(2) * unit_limit * actor::kUnitFeat;
  const size_t global_stride = actor::kGlobalFeat;
  std::exception_ptr error;
  {
    py::gil_scoped_release release;
    error = ParallelFor(
        input_layout.count, std::min(input_layout.count, workers),
        [&](int index) {
          const PolicySession session(*engines[index], players[index],
                                      unit_limit);
          session.EncodeTo(
              board_data + static_cast<size_t>(index) * board_stride,
              unit_data + static_cast<size_t>(index) * unit_stride,
              global_data + static_cast<size_t>(index) * global_stride);
          count_data[index] = session.unit_count();
          session.WriteGpuState(
              input_layout.state,
              state_data +
                  static_cast<size_t>(index) * input_layout.state.width);
        });
  }
  if (error) std::rethrow_exception(error);
}

void FillCompactEnginePolicyTurnInputs(
    const std::vector<const Engine*>& engines, const std::vector<int>& players,
    int unit_limit, int workers, const EnginePolicyInputLayout& input_layout,
    std::uint16_t* board_data, std::uint16_t* unit_data,
    float* global_data, int64_t* count_data, int32_t* state_data) {
  const size_t board_stride =
      static_cast<size_t>(2) * actor::kBoardChannels *
      input_layout.board_size * input_layout.board_size;
  const size_t unit_stride =
      static_cast<size_t>(2) * unit_limit * actor::kUnitFeat;
  const size_t global_stride = actor::kGlobalFeat;
  std::exception_ptr error;
  {
    py::gil_scoped_release release;
    error = ParallelFor(
        input_layout.count, std::min(input_layout.count, workers),
        [&](int index) {
          const PolicySession session(*engines[index], players[index],
                                      unit_limit);
          session.EncodeCompactTo(
              board_data + static_cast<size_t>(index) * board_stride,
              unit_data + static_cast<size_t>(index) * unit_stride,
              global_data + static_cast<size_t>(index) * global_stride);
          count_data[index] = session.unit_count();
          session.WriteGpuState(
              input_layout.state,
              state_data +
                  static_cast<size_t>(index) * input_layout.state.width);
        });
  }
  if (error) std::rethrow_exception(error);
}

void ValidateHalfOutputArray(const py::array& value,
                             std::initializer_list<py::ssize_t> expected,
                             const char* name) {
  if (!value.writeable() || !(value.flags() & py::array::c_style)) {
    throw py::value_error(std::string(name) +
                          " must be writable and C-contiguous");
  }
  if (!value.dtype().is(py::dtype("float16"))) {
    throw py::value_error(std::string(name) + " must use float16");
  }
  if (value.ndim() != static_cast<py::ssize_t>(expected.size())) {
    throw py::value_error(std::string(name) + " has the wrong rank");
  }
  py::ssize_t axis = 0;
  for (const py::ssize_t size : expected) {
    if (value.shape(axis) != size) {
      throw py::value_error(std::string(name) + " has the wrong shape");
    }
    ++axis;
  }
}

}  // namespace

py::object MakeEnginePolicySession(const Engine& engine, int player,
                                   int unit_limit) {
  PolicySession session = [&]() {
    py::gil_scoped_release release;
    return PolicySession(engine, player, unit_limit);
  }();
  return py::cast(std::move(session),
                  py::return_value_policy::move);
}

py::object MakeEnginePolicySessionBatch(
    const std::vector<const Engine*>& engines, const std::vector<int>& players,
    int unit_limit, int workers) {
  const int count = static_cast<int>(engines.size());
  if (count < 1 || players.size() != engines.size()) {
    throw py::value_error("engine policy batch inputs must be nonempty and aligned");
  }
  if (unit_limit < 1) throw py::value_error("unit_limit must be positive");
  if (workers < 1 || workers > 256) {
    throw py::value_error("policy session batch workers must be in [1, 256]");
  }
  for (int index = 0; index < count; ++index) {
    if (engines[index] == nullptr || players[index] < 0 || players[index] > 1) {
      throw py::value_error("engine policy batch contains an invalid row");
    }
  }
  std::vector<std::optional<PolicySession>> values(
      static_cast<size_t>(count));
  std::exception_ptr error;
  {
    py::gil_scoped_release release;
    error = ParallelFor(count, std::min(count, workers), [&](int index) {
      values[index].emplace(*engines[index], players[index], unit_limit);
    });
  }
  if (error) std::rethrow_exception(error);
  std::vector<PolicySession> sessions;
  sessions.reserve(static_cast<size_t>(count));
  for (std::optional<PolicySession>& value : values) {
    sessions.push_back(std::move(value.value()));
  }
  return py::cast(PolicySessionBatch(std::move(sessions), workers),
                  py::return_value_policy::move);
}

py::object MakeEnginePolicyTurnInputs(
    const std::vector<const Engine*>& engines, const std::vector<int>& players,
    int unit_limit, int workers) {
  const EnginePolicyInputLayout layout =
      ValidateEnginePolicyInputs(engines, players, unit_limit, workers);
  const py::ssize_t batch = static_cast<py::ssize_t>(layout.count);
  auto board = MakeArray<float>(
      {batch, 2, actor::kBoardChannels, layout.board_size, layout.board_size});
  auto units = MakeArray<float>({batch, 2, unit_limit, actor::kUnitFeat});
  auto global = MakeArray<float>({batch, actor::kGlobalFeat});
  auto unit_counts = MakeArray<int64_t>({batch});
  auto state = MakeArray<int64_t>({batch, layout.state.width});
  FillEnginePolicyTurnInputs(
      engines, players, unit_limit, workers, layout, board.mutable_data(),
      units.mutable_data(), global.mutable_data(), unit_counts.mutable_data(),
      state.mutable_data());
  return py::make_tuple(std::move(board), std::move(units),
                        std::move(global), std::move(unit_counts),
                        std::move(state));
}

void WriteEnginePolicyTurnInputs(
    const std::vector<const Engine*>& engines, const std::vector<int>& players,
    int unit_limit, int workers, py::array_t<float, py::array::c_style> board,
    py::array_t<float, py::array::c_style> units,
    py::array_t<float, py::array::c_style> global,
    py::array_t<int64_t, py::array::c_style> unit_counts,
    py::array_t<int64_t, py::array::c_style> state) {
  const EnginePolicyInputLayout layout =
      ValidateEnginePolicyInputs(engines, players, unit_limit, workers);
  const py::ssize_t batch = static_cast<py::ssize_t>(layout.count);
  ValidateOutputArray(
      board,
      {batch, 2, actor::kBoardChannels, layout.board_size, layout.board_size},
      "board output");
  ValidateOutputArray(units, {batch, 2, unit_limit, actor::kUnitFeat},
                      "unit output");
  ValidateOutputArray(global, {batch, actor::kGlobalFeat}, "global output");
  ValidateOutputArray(unit_counts, {batch}, "unit-count output");
  ValidateOutputArray(state, {batch, layout.state.width}, "state output");
  FillEnginePolicyTurnInputs(
      engines, players, unit_limit, workers, layout, board.mutable_data(),
      units.mutable_data(), global.mutable_data(), unit_counts.mutable_data(),
      state.mutable_data());
}

void WriteCompactEnginePolicyTurnInputs(
    const std::vector<const Engine*>& engines,
    const std::vector<int>& players, int unit_limit, int workers,
    py::array board, py::array units,
    py::array_t<float, py::array::c_style> global,
    py::array_t<int64_t, py::array::c_style> unit_counts,
    py::array_t<int32_t, py::array::c_style> state) {
  const EnginePolicyInputLayout layout =
      ValidateEnginePolicyInputs(engines, players, unit_limit, workers);
  const py::ssize_t batch = static_cast<py::ssize_t>(layout.count);
  ValidateHalfOutputArray(
      board,
      {batch, 2, actor::kBoardChannels, layout.board_size, layout.board_size},
      "board output");
  ValidateHalfOutputArray(units, {batch, 2, unit_limit, actor::kUnitFeat},
                          "unit output");
  ValidateOutputArray(global, {batch, actor::kGlobalFeat}, "global output");
  ValidateOutputArray(unit_counts, {batch}, "unit-count output");
  ValidateOutputArray(state, {batch, layout.state.width}, "state output");
  FillCompactEnginePolicyTurnInputs(
      engines, players, unit_limit, workers, layout,
      static_cast<std::uint16_t*>(board.mutable_data()),
      static_cast<std::uint16_t*>(units.mutable_data()),
      global.mutable_data(), unit_counts.mutable_data(), state.mutable_data());
}

void BindPolicySession(py::module_& module) {
  module.def(
      "gpu_policy_state_spec",
      [](int board_size, int unit_limit) {
        if (board_size < 2 || unit_limit < 1) {
          throw py::value_error("GPU policy state shape must be positive");
        }
        const policy_gpu::Layout layout =
            policy_gpu::MakeLayout(board_size, unit_limit);
        py::dict result;
        result["version"] = policy_gpu::kVersion;
        result["header_fields"] = static_cast<int>(policy_gpu::kHeaderFields);
        result["positions"] = layout.positions;
        result["inventories"] = layout.inventories;
        result["inventory_order"] = layout.inventory_order;
        result["shed"] = layout.shed;
        result["seeds"] = layout.seeds;
        result["market_inventory"] = layout.market_inventory;
        result["market_prices"] = layout.market_prices;
        result["market_base_milli"] = layout.market_base_milli;
        result["market_i0"] = layout.market_i0;
        result["market_t_milli"] = layout.market_t_milli;
        result["market_below_function"] = layout.market_below_function;
        result["market_below_target_milli"] =
            layout.market_below_target_milli;
        result["market_above_function"] = layout.market_above_function;
        result["market_above_target_milli"] =
            layout.market_above_target_milli;
        result["seed_costs"] = layout.seed_costs;
        result["animal_costs"] = layout.animal_costs;
        result["land_costs"] = layout.land_costs;
        result["tiles"] = layout.tiles;
        result["tile_fields"] = static_cast<int>(policy_gpu::kTileFields);
        result["width"] = layout.width;
        return result;
      },
      py::arg("board_size"), py::arg("unit_limit"));
  py::class_<PolicySession>(module, "PolicySession")
      .def(py::init<const py::dict&, py::object, int>(), py::arg("observation"),
           py::arg("configuration"), py::arg("unit_limit"))
      .def("encode", &PolicySession::Encode)
      .def("legal_mask", &PolicySession::LegalMask)
      .def("turn_facts", &PolicySession::TurnFacts,
           py::arg("opponent_lower") = py::none(),
           py::arg("opponent_upper") = py::none())
      .def("prefix_facts", &PolicySession::PrefixFacts)
      .def("candidate_facts", &PolicySession::CandidateFacts)
      .def("flow_snapshot", &PolicySession::FlowSnapshot)
      .def("own_market_flow_bounds", &PolicySession::MarketFlowBounds)
      .def("select", &PolicySession::Select, py::arg("token"),
           py::arg("quantity") = 0,
           py::call_guard<py::gil_scoped_release>())
      .def("select_compiled_units", &PolicySession::SelectCompiledUnits,
           py::arg("tokens"), py::arg("quantities"))
      .def("action", &PolicySession::Action)
      .def("gpu_state", &PolicySession::GpuState)
      .def_property_readonly("phase", &PolicySession::phase)
      .def_property_readonly("unit_count", &PolicySession::unit_count)
      .def_property_readonly("decision_count", &PolicySession::decision_count);
  py::class_<PolicySessionBatch>(module, "PolicySessionBatch")
      .def(py::init<py::list, int>(), py::arg("sessions"), py::arg("workers"))
      .def("encode", &PolicySessionBatch::Encode)
      .def("encode_compact", &PolicySessionBatch::EncodeCompact)
      .def("phases", &PolicySessionBatch::Phases)
      .def("unit_counts", &PolicySessionBatch::UnitCounts)
      .def("legal_masks", &PolicySessionBatch::LegalMasks)
      .def("decision_inputs", &PolicySessionBatch::DecisionInputs)
      .def("gpu_state", &PolicySessionBatch::GpuState)
      .def("gpu_state_compact", &PolicySessionBatch::GpuStateCompact)
      .def("flow_snapshots", &PolicySessionBatch::FlowSnapshots)
      .def("turn_facts_batch", &PolicySessionBatch::TurnFactsBatch,
           py::arg("opponent_lower"), py::arg("opponent_upper"))
      .def("own_market_flow_bounds_batch",
           &PolicySessionBatch::MarketFlowBoundsBatch)
      .def("select", &PolicySessionBatch::Select, py::arg("tokens"),
           py::arg("quantities"), py::arg("active"))
      .def("select_compiled_units", &PolicySessionBatch::SelectCompiledUnits,
           py::arg("tokens"), py::arg("quantities"),
           py::arg("unit_counts"))
      .def("select_sequences", &PolicySessionBatch::SelectSequences,
           py::arg("tokens"), py::arg("quantities"),
           py::arg("decision_counts"), py::arg("unit_counts"))
      .def("compiled_unit_inputs", &PolicySessionBatch::CompiledUnitInputs,
           py::arg("tokens"), py::arg("quantities"),
           py::arg("unit_counts"), py::arg("include_facts"),
           py::arg("include_gpu_state"))
      .def("decision_facts", &PolicySessionBatch::DecisionFacts)
      .def_property_readonly("size", &PolicySessionBatch::size)
      .def_property_readonly("workers", &PolicySessionBatch::workers);
}

}  // namespace kagg
