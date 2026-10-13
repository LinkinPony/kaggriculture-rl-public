#include "parallel/deployment.hpp"

#include <algorithm>
#include <stdexcept>

#include "actor_encoding.hpp"
#include "action_codec.hpp"
#include "parallel/production.hpp"
#include "parallel/context.hpp"
#include "parallel/work.hpp"
#include "py_convert.hpp"
#include "unit_phase.hpp"

namespace kagg::parallel {
namespace py = pybind11;

ContractSession::ContractSession(py::dict configuration, int units)
    : config_(pyconv::ParseConfig(configuration)), units_(units),
      history_(config_.turns_per_day) {
  if (units < 1) throw std::invalid_argument("unit limit must be positive");
}

StateView ContractSession::view() const {
  if (step_ < 0) throw std::logic_error("official observation has not been supplied");
  return {config_, step_, farms_[0], farms_[1], private_[0], private_[1], market_, shops_};
}

void ContractSession::Update(py::dict observation) {
  const int seat = py::cast<int>(observation["player"]);
  const int step = py::cast<int>(observation["step"]);
  if (seat < 0 || seat > 1 || step < 0 ||
      (seat_ >= 0 && seat != seat_) || (step != step_ && step != step_ + 1)) {
    throw std::invalid_argument("official observations must arrive in seat/turn order");
  }
  const auto farms = py::reinterpret_borrow<py::list>(observation["farms"]);
  for (int player = 0; player < 2; ++player) {
    farms_[player] = pyconv::ParseFarm(py::cast<py::dict>(farms[player]), config_.board_size);
  }
  private_[seat] = pyconv::ParsePrivate(py::cast<py::dict>(observation["private"]));
  private_[1 - seat] = PrivateState{};
  const auto market = py::cast<py::dict>(observation["market"]);
  const auto inventory = py::cast<py::dict>(market["inventory"]);
  const auto prices = py::cast<py::dict>(market["prices"]);
  for (int product = 0; product < kNumProducts; ++product) {
    market_.inventory[product] = py::cast<int64_t>(inventory[kItemNames[product]]);
    market_.prices[product] = py::cast<int64_t>(prices[kItemNames[product]]);
  }
  shops_.clear();
  const auto town = py::cast<py::dict>(observation["town"]);
  for (auto item : py::cast<py::list>(town["unlocked_shops"])) {
    const auto name = py::cast<std::string>(item);
    int found = -1;
    for (int shop = 0; shop < kNumShops; ++shop) {
      if (name == kShops[shop].name) found = shop;
    }
    if (found < 0) throw std::invalid_argument("unknown official shop");
    shops_.push_back(found);
  }
  seat_ = seat;
  step_ = step;
  py::gil_scoped_release release;
  history_.Record(view());
}

void ContractSession::Observe(py::array output) const {
  const int base = 2 * actor::kBoardChannels * config_.board_size * config_.board_size +
                   units_ * actor::kUnitFeat + actor::kGlobalFeat + kMaxShopInstances * kNumShops;
  const int regular = base + EntityExtraFeatures(units_);
  const bool derived = output.ndim() == 2 &&
      output.shape(1) == regular + ContextFeatures(config_.board_size, true, units_, true) + units_ * kUnitSupportFeatures;
  const bool agronomy = derived || (output.ndim() == 2 &&
      output.shape(1) == regular + ContextFeatures(config_.board_size, true, units_) + units_ * kUnitSupportFeatures);
  const int context_width = ContextFeatures(config_.board_size, agronomy, units_, derived);
  const bool context = output.ndim() == 2 &&
      output.shape(1) == regular + context_width + units_ * kUnitSupportFeatures;
  const bool grounded = context || (output.ndim() == 2 &&
      output.shape(1) == regular + units_ * kUnitSupportFeatures);
  if (output.ndim() != 2 || output.shape(0) != 1 ||
      (!grounded && output.shape(1) != regular) ||
      !output.dtype().is(py::dtype("float16")) || !output.writeable() ||
      !(output.flags() & py::array::c_style)) {
    throw std::invalid_argument("official feature destination has the wrong ABI");
  }
  auto* data = static_cast<uint16_t*>(output.mutable_data());
  py::gil_scoped_release release;
  WriteObservation(data);
  if (context) EncodeContext(view(), seat_, history_, data + regular, agronomy, units_, derived);
  if (grounded) EncodeUnitSupport(view(), seat_, units_, data + regular + (context ? context_width : 0));
}

void ContractSession::WriteObservation(uint16_t* data) const {
  const int base = 2 * actor::kBoardChannels * config_.board_size * config_.board_size +
                   units_ * actor::kUnitFeat + actor::kGlobalFeat + kMaxShopInstances * kNumShops;
  EncodeObservation(view(), seat_, units_, data);
  EncodeEntityExtras(view(), seat_, units_, history_, data + base,
      data + actor::kBoardChannels * config_.board_size * config_.board_size);
}

void ContractSession::EncodeReplay(py::list steps, int seat, py::array observations,
                                   py::array actions) {
  const int turns = config_.episode_steps - 1;
  const int regular = 2 * actor::kBoardChannels * config_.board_size * config_.board_size +
      units_ * actor::kUnitFeat + actor::kGlobalFeat + kMaxShopInstances * kNumShops +
      EntityExtraFeatures(units_);
  const bool derived = observations.ndim() == 2 &&
      observations.shape(1) == regular + ContextFeatures(config_.board_size, true, units_, true) + units_ * kUnitSupportFeatures;
  const bool agronomy = derived || (observations.ndim() == 2 &&
      observations.shape(1) == regular + ContextFeatures(config_.board_size, true, units_) + units_ * kUnitSupportFeatures);
  const int context_width = ContextFeatures(config_.board_size, agronomy, units_, derived);
  const bool context = observations.ndim() == 2 &&
      observations.shape(1) == regular + context_width + units_ * kUnitSupportFeatures;
  const bool grounded = context || (observations.ndim() == 2 &&
      observations.shape(1) == regular + units_ * kUnitSupportFeatures);
  const int features = regular + (context ? context_width : 0) + (grounded ? units_ * kUnitSupportFeatures : 0);
  const int slots = units_ + config_.max_market_orders;
  if (seat < 0 || seat > 1 || step_ != -1 || steps.size() != static_cast<size_t>(turns + 1) ||
      observations.ndim() != 2 || observations.shape(0) != turns ||
      observations.shape(1) != features || !observations.dtype().is(py::dtype("float16")) ||
      actions.ndim() != 3 || actions.shape(0) != turns || actions.shape(1) != slots ||
      actions.shape(2) != 2 || !actions.dtype().is(py::dtype::of<int64_t>()) ||
      !observations.writeable() || !actions.writeable() ||
      !(observations.flags() & py::array::c_style) || !(actions.flags() & py::array::c_style)) {
    throw std::invalid_argument("replay destinations have the wrong ABI or session is not fresh");
  }
  auto* encoded = static_cast<uint16_t*>(observations.mutable_data());
  auto* labels = static_cast<int64_t*>(actions.mutable_data());
  std::vector<int64_t> tokens(slots), quantities(slots);
  for (int turn = 0; turn < turns; ++turn) {
    const auto source = py::cast<py::list>(steps[turn]);
    const auto target = py::cast<py::list>(steps[turn + 1]);
    if (source.size() != 2 || target.size() != 2) {
      throw std::invalid_argument("replay must contain both seats at every turn");
    }
    const auto state = py::cast<py::dict>(source[seat]);
    if (py::cast<std::string>(state["status"]) != "ACTIVE") {
      throw std::invalid_argument("replay contains an inactive decision");
    }
    auto observation = py::cast<py::dict>(state["observation"]);
    if (!observation.contains("step")) {
      observation = py::cast<py::dict>(observation.attr("copy")());
      observation["step"] = turn;
    }
    Update(observation);
    if (seat_ != seat || step_ != turn || 1 + static_cast<int>(farms_[seat].hands.size()) > units_) {
      throw std::invalid_argument("replay seat, step or unit capacity differs");
    }
    auto requested = pyconv::ParsePlayerAction(py::cast<py::dict>(target[seat])["action"],
                                               config_.max_market_orders);
    py::gil_scoped_release release;
    WriteObservation(encoded + static_cast<size_t>(turn) * features);
    if (context) EncodeContext(view(), seat_, history_, encoded + static_cast<size_t>(turn) * features + regular, agronomy, units_, derived);
    if (grounded) {
      EncodeUnitSupport(view(), seat_, units_,
                        encoded + static_cast<size_t>(turn) * features + features - units_ * kUnitSupportFeatures);
    }
    auto compiled = CompileUnitPhase(config_, farms_[seat], private_[seat], requested,
                                      turn / config_.turns_per_day);
    compiled.actual.market = std::move(requested.market);
    const int count = 1 + farms_[seat].hands.size();
    const int decisions = policy::EncodePlayerAction(compiled.actual, count, tokens.data(),
                                                      quantities.data(), slots);
    auto* row = labels + static_cast<size_t>(turn) * slots * 2;
    std::fill(row, row + slots * 2, 0);
    for (int i = 0; i < decisions; ++i) {
      const int slot = i < count ? i : units_ + i - count;
      row[2 * slot] = i < count ? tokens[i] : tokens[i] - policy::kUnitActionTokens;
      if (policy::TokenHasQuantity(tokens[i])) row[2 * slot + 1] = std::max<int64_t>(1, quantities[i]);
    }
  }
}

void ContractSession::SetProgram(py::array plan, int capacity, std::vector<int64_t> quantities) {
  view();
  if (capacity < 1 || capacity >= config_.episode_steps || quantities.empty() ||
      std::any_of(quantities.begin(), quantities.end(), [](int64_t q) { return q < 1; }) ||
      plan.ndim() != 2 || plan.shape(0) != 1 ||
      plan.shape(1) != ProgramSize(config_, units_, capacity) ||
      !plan.dtype().is(py::dtype::of<int64_t>()) || !(plan.flags() & py::array::c_style)) {
    throw std::invalid_argument("official work program has the wrong ABI");
  }
  const auto* data = static_cast<const int64_t*>(plan.data());
  py::gil_scoped_release release;
  ValidateProgram(config_, data, units_, capacity, quantities.size());
  program_.assign(data, data + plan.shape(1));
  quantities_ = std::move(quantities);
  cursors_.assign(units_, 0);
  capacity_ = capacity;
  program_start_ = step_;
  action_step_ = -1;
}

py::dict ContractSession::ProgramAction() {
  if (program_.empty()) throw std::logic_error("no work program supplied");
  if (action_step_ != step_) {
    py::gil_scoped_release release;
    cached_action_ = ExecuteProgram(view(), seat_, program_.data(), capacity_, units_,
                                    quantities_, step_ - program_start_, &cursors_);
    action_step_ = step_;
  }
  return pyconv::PlayerActionToPy(cached_action_);
}

py::dict ContractSession::Action(py::array plan) const {
  if (plan.ndim() != 2 || plan.shape(0) != 1 || plan.shape(1) != ContractSize(config_) ||
      !plan.dtype().is(py::dtype::of<int64_t>()) || !(plan.flags() & py::array::c_style)) {
    throw std::invalid_argument("official contract has the wrong ABI");
  }
  const auto* data = static_cast<const int64_t*>(plan.data());
  PlayerAction action;
  {
    py::gil_scoped_release release;
    ValidateContract(config_, data, units_);
    action = ExecuteContract(view(), seat_, data, units_);
  }
  return pyconv::PlayerActionToPy(action);
}

}  // namespace kagg::parallel
