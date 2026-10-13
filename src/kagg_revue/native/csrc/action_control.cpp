// Canonical official-request construction with diagnostic local projection.

#include "action_control.hpp"

#include <pybind11/pybind11.h>

#include <algorithm>
#include <array>
#include <cstdint>
#include <limits>
#include <optional>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

#include "market_phase.hpp"
#include "py_convert.hpp"
#include "types.hpp"
#include "unit_phase.hpp"

namespace py = pybind11;

namespace kagg::control {
namespace {

enum class Phase { kUnit, kMarket, kDone };
enum class SpecialChoice { kNone, kStop, kSkipSlot };

struct Candidate {
  std::string key;
  std::string operation;
  int item = -1;
  bool has_quantity = false;
  std::optional<UnitAction> unit;
  std::optional<MarketOrder> market;
  SpecialChoice special = SpecialChoice::kNone;
};

struct MarketProjection {
  Farm farm;
  PrivateState priv;
  MarketState market;
  MarketSlotTrace trace;
  bool has_trace = false;
};

const char* PhaseName(Phase phase) {
  switch (phase) {
    case Phase::kUnit:
      return "unit";
    case Phase::kMarket:
      return "market";
    case Phase::kDone:
      return "done";
  }
  return "done";
}

MarketState ParseMarket(const py::dict& observation) {
  MarketState state;
  const auto market = py::reinterpret_borrow<py::dict>(observation["market"]);
  const auto inventory = py::reinterpret_borrow<py::dict>(market["inventory"]);
  const auto prices = py::reinterpret_borrow<py::dict>(market["prices"]);
  for (int product = 0; product < kNumProducts; ++product) {
    state.inventory[product] = py::cast<int64_t>(inventory[kItemNames[product]]);
    state.prices[product] = py::cast<int64_t>(prices[kItemNames[product]]);
  }
  return state;
}

py::dict MarketToPy(const MarketState& state) {
  py::dict inventory;
  py::dict prices;
  for (int product = 0; product < kNumProducts; ++product) {
    inventory[kItemNames[product]] = state.inventory[product];
    prices[kItemNames[product]] = state.prices[product];
  }
  py::dict result;
  result["inventory"] = inventory;
  result["prices"] = prices;
  return result;
}

std::string CandidateKey(const char* phase, const std::string& operation,
                         int item_index) {
  std::string result = std::string(phase) + ":" + operation;
  if (item_index >= 0) result += ":" + std::string(kItemNames[item_index]);
  return result;
}

bool IsPositiveInteger(const py::object& quantity) {
  if (quantity.is_none() || py::isinstance<py::bool_>(quantity) ||
      !py::isinstance<py::int_>(quantity)) {
    return false;
  }
  const py::int_ zero(0);
  const int result = PyObject_RichCompareBool(quantity.ptr(), zero.ptr(), Py_GT);
  if (result < 0) throw py::error_already_set();
  return result == 1;
}

bool IntegerExceeds(const py::object& quantity, int64_t limit) {
  const py::int_ maximum(limit);
  const int result = PyObject_RichCompareBool(quantity.ptr(), maximum.ptr(), Py_GT);
  if (result < 0) throw py::error_already_set();
  return result == 1;
}

int64_t SimulationQuantity(const py::object& quantity, int64_t limit) {
  if (IntegerExceeds(quantity, limit)) return limit;
  int overflow = 0;
  const long long value = PyLong_AsLongLongAndOverflow(quantity.ptr(), &overflow);
  if (value == -1 && PyErr_Occurred()) throw py::error_already_set();
  if (overflow > 0) return limit;
  if (overflow < 0) return 0;
  return std::min<int64_t>(value, limit);
}

py::dict CandidateToPy(const Candidate& candidate) {
  py::dict result;
  result["key"] = candidate.key;
  result["operation"] = candidate.operation;
  result["item"] =
      candidate.item >= 0 ? py::cast(kItemNames[candidate.item]) : py::none();
  if (candidate.has_quantity) {
    py::dict quantity;
    quantity["minimum"] = 1;
    result["quantity"] = quantity;
  } else {
    result["quantity"] = py::none();
  }
  return result;
}

py::list RequestToPy(const Candidate& candidate, const py::object& quantity) {
  py::list result;
  result.append(candidate.operation);
  if (candidate.item >= 0) result.append(kItemNames[candidate.item]);
  if (candidate.has_quantity) result.append(quantity);
  return result;
}

class OfficialActionBuilder {
 public:
  OfficialActionBuilder(const py::dict& observation, py::object configuration)
      : config_(pyconv::ParseConfig(std::move(configuration))) {
    config_.max_market_orders = std::max(1, config_.max_market_orders);
    config_.turns_per_day = std::max(1, config_.turns_per_day);
    player_ = py::cast<int>(observation["player"]);
    if (player_ < 0 || player_ > 1) {
      throw py::value_error("observation player must be 0 or 1");
    }
    const int step = py::cast<int>(observation["step"]);
    if (step < 0) throw py::value_error("observation step must be non-negative");
    day_ = step / config_.turns_per_day;

    const auto farms = py::reinterpret_borrow<py::list>(observation["farms"]);
    base_farm_ = pyconv::ParseFarm(
        py::reinterpret_borrow<py::dict>(farms[player_]), config_.board_size);
    opponent_farm_ = pyconv::ParseFarm(
        py::reinterpret_borrow<py::dict>(farms[1 - player_]), config_.board_size);
    base_priv_ =
        pyconv::ParsePrivate(py::reinterpret_borrow<py::dict>(observation["private"]));
    farm_ = base_farm_;
    priv_ = base_priv_;
    market_ = ParseMarket(observation);
    unit_count_ = 1 + static_cast<int>(farm_.hands.size());
  }

  py::dict Choices() const {
    const std::vector<Candidate> candidates = Candidates();
    py::list encoded;
    for (const Candidate& candidate : candidates) {
      encoded.append(CandidateToPy(candidate));
    }

    py::dict result;
    result["spec_version"] = kOfficialActionControlSpecVersion;
    result["phase"] = PhaseName(phase_);
    result["unit_index"] =
        phase_ == Phase::kUnit ? py::cast(unit_index_) : py::none();
    result["market_slot"] =
        phase_ == Phase::kMarket ? py::cast(market_slot_) : py::none();
    result["candidate_basis"] = kCandidateBasis;
    result["market_projection"] = kLocalMarketProjection;
    result["projection_role"] = kProjectionRole;
    result["candidates"] = encoded;
    return result;
  }

  void Select(const std::string& key, py::object quantity) {
    if (phase_ == Phase::kDone) {
      throw py::value_error("official action is already complete");
    }
    const std::vector<Candidate> candidates = Candidates();
    const auto found =
        std::find_if(candidates.begin(), candidates.end(), [&](const Candidate& candidate) {
          return candidate.key == key;
        });
    if (found == candidates.end()) {
      throw py::value_error("candidate is unavailable in the request grammar: " + key);
    }

    int64_t simulation_quantity = 0;
    bool projection_limited = false;
    if (found->has_quantity) {
      if (!IsPositiveInteger(quantity)) {
        throw py::value_error("candidate requires a positive integer quantity");
      }
      const int64_t simulation_limit = phase_ == Phase::kMarket
                                           ? kMaxMarketUnitsPerSlot
                                           : std::numeric_limits<int64_t>::max();
      projection_limited = IntegerExceeds(quantity, simulation_limit);
      simulation_quantity = SimulationQuantity(quantity, simulation_limit);
    } else if (!quantity.is_none()) {
      throw py::value_error("candidate does not accept a quantity");
    }

    if (phase_ == Phase::kUnit) {
      SelectUnit(*found, simulation_quantity, quantity, projection_limited);
    } else {
      SelectMarket(*found, simulation_quantity, quantity, projection_limited);
    }
  }

  py::dict Action() const {
    if (phase_ != Phase::kDone) {
      throw py::value_error("official action is incomplete");
    }
    if (raw_units_.size() != static_cast<size_t>(unit_count_)) {
      throw std::logic_error("completed official action has an incomplete unit queue");
    }
    py::list hands;
    for (size_t index = 1; index < raw_units_.size(); ++index) {
      hands.append(raw_units_[index]);
    }
    py::list market;
    for (const py::object& order : raw_market_) market.append(order);
    py::dict result;
    result["farmer"] = raw_units_[0];
    result["hands"] = hands;
    result["market"] = market;
    return result;
  }

  py::dict LocalState() const {
    py::list unit_outcomes;
    for (const std::string& outcome : unit_outcomes_) unit_outcomes.append(outcome);
    py::list market_outcomes;
    for (const std::string& outcome : market_outcomes_) {
      market_outcomes.append(outcome);
    }
    py::dict result;
    result["spec_version"] = kOfficialActionControlSpecVersion;
    result["phase"] = PhaseName(phase_);
    result["market_projection"] = kLocalMarketProjection;
    result["projection_role"] = kProjectionRole;
    result["farm"] = pyconv::FarmToPy(farm_, config_.board_size);
    result["private"] = pyconv::PrivateToPy(priv_);
    result["market"] = MarketToPy(market_);
    result["unit_outcomes"] = unit_outcomes;
    result["market_outcomes"] = market_outcomes;
    return result;
  }

  const char* spec_version() const { return kOfficialActionControlSpecVersion; }

 private:
  void AddUnit(std::vector<Candidate>* output, const std::string& operation,
               UnitAction action, int item_index = -1,
               bool has_quantity = false) const {
    output->push_back(Candidate{CandidateKey("UNIT", operation, item_index), operation,
                                item_index, has_quantity, action, std::nullopt,
                                SpecialChoice::kNone});
  }

  std::vector<Candidate> UnitCandidates() const {
    std::vector<Candidate> result;
    AddUnit(&result, "PASS", UnitAction{UnitOp::kPass, -1, 1});
    AddUnit(&result, "NORTH", UnitAction{UnitOp::kNorth, -1, 1});
    AddUnit(&result, "SOUTH", UnitAction{UnitOp::kSouth, -1, 1});
    AddUnit(&result, "EAST", UnitAction{UnitOp::kEast, -1, 1});
    AddUnit(&result, "WEST", UnitAction{UnitOp::kWest, -1, 1});
    for (int item_index = 0; item_index < kNumItems; ++item_index) {
      AddUnit(&result, "PICKUP", UnitAction{UnitOp::kPickup, item_index, 1},
              item_index, true);
    }
    AddUnit(&result, "DROP", UnitAction{UnitOp::kDrop, -1, 1});
    for (int item_index = 0; item_index < kNumItems; ++item_index) {
      AddUnit(&result, "PLACE", UnitAction{UnitOp::kPlace, item_index, 1},
              item_index, true);
    }
    for (int crop = 0; crop < kNumCrops; ++crop) {
      AddUnit(&result, "PLANT", UnitAction{UnitOp::kPlant, crop, 1}, crop);
    }
    AddUnit(&result, "WATER", UnitAction{UnitOp::kWater, -1, 1});
    AddUnit(&result, "HARVEST", UnitAction{UnitOp::kHarvest, -1, 1});
    AddUnit(&result, "FERTILIZE", UnitAction{UnitOp::kFertilize, -1, 1});
    AddUnit(&result, "DIG", UnitAction{UnitOp::kDig, -1, 1});
    AddUnit(&result, "BUILD_COOP", UnitAction{UnitOp::kBuildCoop, -1, 1});
    AddUnit(&result, "BUILD_PASTURE", UnitAction{UnitOp::kBuildPasture, -1, 1});
    AddUnit(&result, "FEED", UnitAction{UnitOp::kFeed, -1, 1});
    AddUnit(&result, "COLLECT_FERTILIZER",
            UnitAction{UnitOp::kCollectFertilizer, -1, 1});
    AddUnit(&result, "CARE", UnitAction{UnitOp::kCare, -1, 1});
    return result;
  }

  MarketProjection ProjectMarket(const MarketOrder& order) const {
    std::array<Farm, 2> farms;
    farms[player_] = farm_;
    farms[1 - player_] = opponent_farm_;
    std::array<PrivateState, 2> privates;
    privates[player_] = priv_;
    std::array<PlayerAction, 2> actions;
    actions[player_].market.push_back(order);
    MarketState market = market_;
    const std::array<Farm*, 2> farm_ptrs = {&farms[0], &farms[1]};
    const std::array<PrivateState*, 2> private_ptrs = {&privates[0], &privates[1]};
    std::vector<MarketSlotTrace> trace;
    ApplyMarketPhase(config_, farm_ptrs, private_ptrs, &market, actions[0], actions[1],
                     &trace);

    MarketProjection result{farms[player_], privates[player_], market, {}, false};
    for (const MarketSlotTrace& entry : trace) {
      if (entry.player == player_) {
        result.trace = entry;
        result.has_trace = true;
        break;
      }
    }
    return result;
  }

  void AddMarket(std::vector<Candidate>* output, const std::string& operation,
                 MarketOrder order, int display_item = -1,
                 bool has_quantity = false) const {
    output->push_back(Candidate{CandidateKey("MARKET", operation, display_item),
                                operation, display_item, has_quantity, std::nullopt,
                                order, SpecialChoice::kNone});
  }

  std::vector<Candidate> MarketCandidates() const {
    std::vector<Candidate> result;
    result.push_back(Candidate{"MARKET:STOP", "STOP", -1, false, std::nullopt,
                               std::nullopt, SpecialChoice::kStop});
    result.push_back(Candidate{"MARKET:SKIP_SLOT", "SKIP_SLOT", -1, false,
                               std::nullopt, std::nullopt,
                               SpecialChoice::kSkipSlot});
    for (int product = 0; product < kNumProducts; ++product) {
      AddMarket(&result, "SELL", MarketOrder{OrderKind::kSell, product, 1},
                product, true);
    }
    for (int crop = 0; crop < kNumCrops; ++crop) {
      AddMarket(&result, "BUY_SEED", MarketOrder{OrderKind::kBuySeed, crop, 1},
                crop, true);
    }
    for (const int product : {item::kWheat, item::kFertilizer}) {
      AddMarket(&result, "BUY_PRODUCT",
                MarketOrder{OrderKind::kBuyProduct, product, 1}, product, true);
    }
    for (int animal = 0; animal < kNumAnimals; ++animal) {
      AddMarket(&result, "BUY_ANIMAL",
                MarketOrder{OrderKind::kBuyAnimal, animal, 1},
                item::kGoose + animal, true);
    }
    AddMarket(&result, "HIRE", MarketOrder{OrderKind::kHire, 0, 0});
    AddMarket(&result, "BUY_LAND", MarketOrder{OrderKind::kBuyLand, 0, 0});
    return result;
  }

  std::vector<Candidate> Candidates() const {
    switch (phase_) {
      case Phase::kUnit:
        return UnitCandidates();
      case Phase::kMarket:
        return MarketCandidates();
      case Phase::kDone:
        return {};
    }
    return {};
  }

  void ReprojectUnitPrefix() {
    const UnitPhaseResult projection =
        CompileUnitPhase(config_, base_farm_, base_priv_, selected_units_, day_);
    farm_ = projection.farm;
    priv_ = projection.priv;
    if (projection.trace.size() < static_cast<size_t>(unit_index_)) {
      throw std::logic_error("unit projection omitted a selected request");
    }
    unit_outcomes_.clear();
    for (int index = 0; index < unit_index_; ++index) {
      const UnitActionTrace& trace = projection.trace[index];
      const UnitAction& requested = index == 0
                                        ? selected_units_.farmer
                                        : selected_units_.hands[index - 1];
      const bool quantity_changed =
          (requested.op == UnitOp::kPickup || requested.op == UnitOp::kPlace) &&
          trace.status == UnitActionStatus::kApplied &&
          trace.actual.n != requested.n;
      const bool projection_limited =
          index < static_cast<int>(unit_projection_limited_.size()) &&
          unit_projection_limited_[index] &&
          trace.status == UnitActionStatus::kApplied;
      unit_outcomes_.push_back(quantity_changed || projection_limited
                                   ? "normalized"
                                   : UnitActionStatusName(trace.status));
    }
  }

  void SelectUnit(const Candidate& candidate, int64_t quantity,
                  const py::object& raw_quantity, bool projection_limited) {
    if (!candidate.unit) throw std::logic_error("unit candidate has no request");
    UnitAction requested = *candidate.unit;
    if (candidate.has_quantity) requested.n = quantity;
    if (unit_index_ == 0) {
      selected_units_.farmer = requested;
    } else {
      selected_units_.hands.push_back(requested);
    }
    raw_units_.push_back(RequestToPy(candidate, raw_quantity));
    unit_projection_limited_.push_back(projection_limited);
    ++unit_index_;
    ReprojectUnitPrefix();
    if (unit_index_ == unit_count_) phase_ = Phase::kMarket;
  }

  void AdvanceMarketSlot() {
    ++market_slot_;
    if (market_slot_ >= config_.max_market_orders) phase_ = Phase::kDone;
  }

  void SelectMarket(const Candidate& candidate, int64_t quantity,
                    const py::object& raw_quantity, bool projection_limited) {
    if (candidate.special == SpecialChoice::kStop) {
      phase_ = Phase::kDone;
      return;
    }
    if (candidate.special == SpecialChoice::kSkipSlot) {
      raw_market_.push_back(py::list());
      market_outcomes_.push_back("skip_slot");
      AdvanceMarketSlot();
      return;
    }
    if (!candidate.market) throw std::logic_error("market candidate has no request");
    MarketOrder requested = *candidate.market;
    if (candidate.has_quantity) requested.remaining = quantity;
    const MarketProjection projection = ProjectMarket(requested);
    farm_ = projection.farm;
    priv_ = projection.priv;
    market_ = projection.market;
    raw_market_.push_back(RequestToPy(candidate, raw_quantity));
    if (!projection.has_trace) {
      market_outcomes_.push_back("malformed");
    } else if (projection_limited && projection.trace.committed > 0) {
      market_outcomes_.push_back("partial");
    } else {
      market_outcomes_.push_back(MarketOrderStatusName(projection.trace.status));
    }
    AdvanceMarketSlot();
  }

  Config config_;
  int player_ = 0;
  int day_ = 0;
  Farm base_farm_;
  PrivateState base_priv_;
  Farm farm_;
  Farm opponent_farm_;
  PrivateState priv_;
  MarketState market_;
  PlayerAction selected_units_;
  std::vector<py::object> raw_units_;
  std::vector<py::object> raw_market_;
  std::vector<bool> unit_projection_limited_;
  std::vector<std::string> unit_outcomes_;
  std::vector<std::string> market_outcomes_;
  int unit_count_ = 1;
  int unit_index_ = 0;
  int market_slot_ = 0;
  Phase phase_ = Phase::kUnit;
};

py::dict OfficialActionControlSpec() {
  py::dict result;
  result["version"] = kOfficialActionControlSpecVersion;
  result["unit_order"] = "farmer-then-hands";
  result["candidate_basis"] = kCandidateBasis;
  result["market_projection"] = kLocalMarketProjection;
  result["projection_role"] = kProjectionRole;
  result["quantity"] = "positive-integer-no-state-upper-bound";
  result["market_skip_payload"] = py::list();
  return result;
}

}  // namespace

void BindOfficialActionControl(py::module_& module) {
  module.def("official_action_control_spec", &OfficialActionControlSpec,
             "Return the canonical official-request control contract.");
  py::class_<OfficialActionBuilder>(module, "NativeOfficialActionBuilder")
      .def(py::init<const py::dict&, py::object>(), py::arg("observation"),
           py::arg("configuration") = py::none())
      .def("choices", &OfficialActionBuilder::Choices)
      .def("select", &OfficialActionBuilder::Select, py::arg("key"),
           py::arg("quantity") = py::none())
      .def("action", &OfficialActionBuilder::Action)
      .def("local_state", &OfficialActionBuilder::LocalState)
      .def_property_readonly("spec_version", &OfficialActionBuilder::spec_version);
}

}  // namespace kagg::control
