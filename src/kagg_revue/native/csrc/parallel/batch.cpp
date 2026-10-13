#include "parallel/batch.hpp"

#include <algorithm>
#include <exception>
#include <stdexcept>

#include "action_codec.hpp"
#include "actor_encoding.hpp"
#include "parallel/production.hpp"
#include "parallel/context.hpp"
#include "parallel/work.hpp"
#include "py_convert.hpp"
#include "unit_phase.hpp"

namespace kagg::parallel {
namespace {

void Check(py::array array, const std::vector<py::ssize_t>& shape,
           const py::dtype& dtype, bool writable) {
  if (!(array.flags() & py::array::c_style) || !array.dtype().is(dtype) ||
      (writable && !array.writeable()) || array.request().shape != shape) {
    throw std::invalid_argument("parallel buffer has wrong shape, dtype or layout");
  }
}

}  // namespace

Batch::Batch(py::dict configuration, std::vector<int64_t> seeds,
             std::vector<int> seats, int units, int workers,
             std::vector<int64_t> quantities)
    : config_(pyconv::ParseConfig(configuration)), seats_(std::move(seats)),
      units_(units), workers_(workers), quantities_(std::move(quantities)) {
  const size_t count = seeds.size();
  if (count == 0 || seats_.size() != count ||
      units < 1 || workers < 1 || quantities_.empty() ||
      quantities_.front() < 1 ||
      !std::is_sorted(quantities_.begin(), quantities_.end()) ||
      std::adjacent_find(quantities_.begin(), quantities_.end()) != quantities_.end()) {
    throw std::invalid_argument("invalid parallel batch construction");
  }
  for (size_t i = 0; i < count; ++i) {
    if (seeds[i] < 0 || seats_[i] < 0 || seats_[i] > 1) {
      throw std::invalid_argument("invalid seed or seat");
    }
    engines_.emplace_back(config_, seeds[i]);
    history_.emplace_back(config_.turns_per_day);
    history_.back().Record(engines_.back());

  }
}

int Batch::features() const {
  return 2 * actor::kBoardChannels * config_.board_size * config_.board_size +
         units_ * actor::kUnitFeat + actor::kGlobalFeat + kMaxShopInstances * kNumShops;
}

int Batch::slots() const { return units_ + config_.max_market_orders; }

void Batch::ForEach(const std::function<void(int)>& function) const {
  std::vector<std::exception_ptr> errors(size());
  const int threads = std::min(workers_, size());
#pragma omp parallel for schedule(static) num_threads(threads) if(threads > 1)
  for (int i = 0; i < size(); ++i) {
    try { function(i); } catch (...) { errors[i] = std::current_exception(); }
  }
  for (const auto& error : errors) if (error) std::rethrow_exception(error);
}

void Batch::Observe(py::array output) {
  const int grounded_width = entity_features() + units_ * kUnitSupportFeatures;
  const bool derived = output.ndim() == 2 &&
      output.shape(1) == grounded_width + ContextFeatures(config_.board_size, true, units_, true);
  const bool agronomy = derived || (output.ndim() == 2 &&
      output.shape(1) == grounded_width + ContextFeatures(config_.board_size, true, units_));
  const int context_width = ContextFeatures(config_.board_size, agronomy, units_, derived);
  const bool context = output.ndim() == 2 && output.shape(1) == grounded_width + context_width;
  const bool grounded = context || (output.ndim() == 2 && output.shape(1) == grounded_width);
  const bool entities = grounded || (output.ndim() == 2 && output.shape(1) == entity_features());
  const int width = context ? grounded_width + context_width :
                    grounded ? grounded_width : entities ? entity_features() : features();
  Check(output, {size(), width}, py::dtype("float16"), true);
  auto* destination = static_cast<uint16_t*>(output.mutable_data());
  py::gil_scoped_release release;
  ForEach([&](int i) {
    auto* row = destination + static_cast<size_t>(i) * width;
    ObserveSeat(i, seats_[i], row);
    if (entities) EncodeEntityExtras(engines_[i], seats_[i], units_, history_[i], row + features(),
        row + actor::kBoardChannels * config_.board_size * config_.board_size);
    if (context) EncodeContext(engines_[i], seats_[i], history_[i], row + entity_features(), agronomy, units_, derived);
    if (grounded) EncodeUnitSupport(engines_[i], seats_[i], units_, row + width - units_ * kUnitSupportFeatures);
  });
}

void Batch::ObserveSelfPlay(py::array output) {
  const int grounded_width = entity_features() + units_ * kUnitSupportFeatures;
  const bool derived = output.ndim() == 2 &&
      output.shape(1) == grounded_width + ContextFeatures(config_.board_size, true, units_, true);
  const bool agronomy = derived || (output.ndim() == 2 &&
      output.shape(1) == grounded_width + ContextFeatures(config_.board_size, true, units_));
  const int context_width = ContextFeatures(config_.board_size, agronomy, units_, derived);
  const bool context = output.ndim() == 2 && output.shape(1) == grounded_width + context_width;
  const bool grounded = context || (output.ndim() == 2 && output.shape(1) == grounded_width);
  const bool entities = grounded || (output.ndim() == 2 && output.shape(1) == entity_features());
  const int width = context ? grounded_width + context_width :
                    grounded ? grounded_width : entities ? entity_features() : features();
  Check(output, {2 * size(), width}, py::dtype("float16"), true);
  auto* destination = static_cast<uint16_t*>(output.mutable_data());
  py::gil_scoped_release release;
  ForEach([&](int i) {
    for (int seat = 0; seat < 2; ++seat) {
      auto* row = destination + static_cast<size_t>(2 * i + seat) * width;
      ObserveSeat(i, seat, row);
      if (entities) EncodeEntityExtras(engines_[i], seat, units_, history_[i], row + features(),
          row + actor::kBoardChannels * config_.board_size * config_.board_size);
      if (context) EncodeContext(engines_[i], seat, history_[i], row + entity_features(), agronomy, units_, derived);
      if (grounded) EncodeUnitSupport(engines_[i], seat, units_, row + width - units_ * kUnitSupportFeatures);
    }
  });
}

void Batch::ObserveSeat(int lane, int seat, uint16_t* row) const {
  EncodeObservation(engines_[lane], seat, units_, row);
}

void Batch::Encode(int lane, const PlayerAction& action, int64_t* output) const {
  const int count = 1 + engines_[lane].farm(seats_[lane]).hands.size();
  const int width = count + config_.max_market_orders;
  std::vector<int64_t> tokens(width), quantities(width);
  const int decisions = policy::EncodePlayerAction(action, count, tokens.data(),
                                                   quantities.data(), width);
  std::fill(output, output + 2 * slots(), 0);
  for (int i = 0; i < decisions; ++i) {
    const int slot = i < count ? i : units_ + i - count;
    output[2 * slot] = i < count ? tokens[i] : tokens[i] - policy::kUnitActionTokens;
    if (!policy::TokenHasQuantity(tokens[i])) continue;
    const int64_t quantity = std::max<int64_t>(1, quantities[i]);
    const auto found = std::lower_bound(quantities_.begin(), quantities_.end(), quantity);
    if (found == quantities_.end() || *found != quantity) {
      throw std::runtime_error("teacher quantity not representable: " + std::to_string(quantity));
    }
    output[2 * slot + 1] = found - quantities_.begin();
  }
}

void Batch::Teacher(py::array labels) {
  Check(labels, {size(), slots(), 2}, py::dtype::of<int64_t>(), true);
  if (teachers_.size() != engines_.size()) throw std::logic_error("batch has no teachers");
  auto* output = static_cast<int64_t*>(labels.mutable_data());
  py::gil_scoped_release release;
  ForEach([&](int i) {
    const auto& engine = engines_[i];
    const int seat = seats_[i];
    auto action = teachers_[i](engine, seat);
    auto compiled = CompileUnitPhase(config_, engine.farm(seat), engine.priv(seat),
                                      action, engine.step_index() / config_.turns_per_day);
    compiled.actual.market = action.market;
    Encode(i, compiled.actual, output + static_cast<size_t>(i) * slots() * 2);
  });
}

PlayerAction Batch::Decode(int lane, const int64_t* actions) const {
  const int count = 1 + engines_[lane].farm(seats_[lane]).hands.size();
  if (count > units_) throw std::runtime_error("parallel unit capacity exceeded");
  PlayerAction result;
  for (int slot = 0; slot < slots(); ++slot) {
    const int64_t token = actions[2 * slot];
    const int64_t q = actions[2 * slot + 1];
    if (q < 0 || q >= static_cast<int64_t>(quantities_.size()) || token < 0 ||
        token >= (slot < units_ ? policy::kUnitActionTokens : policy::kMarketActionTokens)) {
      throw std::invalid_argument("parallel action outside vocabulary");
    }
    if (slot < count) {
      auto unit = policy::DecodeUnitToken(token, quantities_[q]);
      if (slot == 0) result.farmer = unit; else result.hands.push_back(unit);
    } else if (slot >= units_) {
      if (token == 0) break;
      result.market.push_back(policy::DecodeMarketToken(token + policy::kUnitActionTokens,
                                                        quantities_[q]));
    }
  }
  return result;
}

void Batch::Step(py::array actions) {
  if (opponents_.size() != engines_.size()) throw std::logic_error("use self-play advance");
  Check(actions, {size(), slots(), 2}, py::dtype::of<int64_t>(), false);
  const auto* data = static_cast<const int64_t*>(actions.data());
  py::gil_scoped_release release;
  ForEach([&](int i) {
    auto candidate = Decode(i, data + static_cast<size_t>(i) * slots() * 2);
    auto opponent = OpponentAction(i);
    if (seats_[i] == 0) Apply(i, candidate, opponent);
    else Apply(i, opponent, candidate);
  });
}

py::array_t<double> Batch::Cash() const {
  py::array_t<double> result({size(), 2});
  auto* data = result.mutable_data();
  for (int i = 0; i < size(); ++i) {
    data[2 * i] = engines_[i].farm(seats_[i]).money;
    data[2 * i + 1] = engines_[i].farm(1 - seats_[i]).money;
  }
  return result;
}

void Batch::Advance(py::array contracts, int turns) {
  if (opponents_.size() != engines_.size()) throw std::logic_error("use self-play advance");
  Check(contracts, {size(), ContractSize(config_)}, py::dtype::of<int64_t>(), false);
  if (turns < 1) throw std::invalid_argument("advance requires positive turns");
  const auto* data = static_cast<const int64_t*>(contracts.data());
  for (int i = 0; i < size(); ++i) {
    ValidateContract(config_, data + static_cast<size_t>(i) * ContractSize(config_), units_);
  }
  py::gil_scoped_release release;
  ForEach([&](int i) {
    const auto* plan = data + static_cast<size_t>(i) * ContractSize(config_);
    for (int turn = 0; turn < turns && !engines_[i].done(); ++turn) {
      auto candidate = ExecuteContract(engines_[i], seats_[i], plan, units_);
      auto opponent = OpponentAction(i);
      if (seats_[i] == 0) Apply(i, candidate, opponent);
      else Apply(i, opponent, candidate);
    }
  });
}

void Batch::AdvanceSelfPlay(py::array contracts, int turns) {
  Check(contracts, {2 * size(), ContractSize(config_)}, py::dtype::of<int64_t>(), false);
  if (turns < 1) throw std::invalid_argument("advance requires positive turns");
  const auto* data = static_cast<const int64_t*>(contracts.data());
  for (int i = 0; i < 2 * size(); ++i) {
    ValidateContract(config_, data + static_cast<size_t>(i) * ContractSize(config_), units_);
  }
  py::gil_scoped_release release;
  ForEach([&](int i) {
    const auto* first = data + static_cast<size_t>(2 * i) * ContractSize(config_);
    const auto* second = first + ContractSize(config_);
    for (int turn = 0; turn < turns && !engines_[i].done(); ++turn) {
      auto left = ExecuteContract(engines_[i], 0, first, units_);
      auto right = ExecuteContract(engines_[i], 1, second, units_);
      Apply(i, left, right);
    }
  });
}

void Batch::AdvancePrograms(py::array plans, int turns, int capacity, bool selfplay) {
  if (capacity < 1 || capacity >= config_.episode_steps || turns < 1 || turns > capacity) {
    throw std::invalid_argument("invalid program duration");
  }
  if (!selfplay && opponents_.size() != engines_.size()) {
    throw std::logic_error("program batch requires opponents");
  }
  const int rows = size() * (selfplay ? 2 : 1);
  const int width = ProgramSize(config_, units_, capacity);
  Check(plans, {rows, width}, py::dtype::of<int64_t>(), false);
  const auto* data = static_cast<const int64_t*>(plans.data());
  for (int row = 0; row < rows; ++row) {
    ValidateProgram(config_, data + static_cast<size_t>(row) * width,
                    units_, capacity, quantities_.size());
  }
  py::gil_scoped_release release;
  ForEach([&](int lane) {
    std::vector<int> first_cursor(units_, 0), second_cursor(units_, 0);
    const auto* first = data + static_cast<size_t>(lane * (selfplay ? 2 : 1)) * width;
    for (int turn = 0; turn < turns && !engines_[lane].done(); ++turn) {
      const int seat = selfplay ? 0 : seats_[lane];
      auto left = ExecuteProgram(engines_[lane], seat, first, capacity, units_, quantities_,
                                  turn, &first_cursor);
      auto right = selfplay
          ? ExecuteProgram(engines_[lane], 1, first + width, capacity, units_, quantities_,
                           turn, &second_cursor)
          : OpponentAction(lane);
      if (seat == 0) Apply(lane, left, right);
      else Apply(lane, right, left);
    }
  });
}

void Batch::PrepareOpponents() {
  if (opponents_.size() != engines_.size()) {
    throw std::logic_error("opponent preparation requires scripted games");
  }
  if (prepared_steps_.empty()) {
    prepared_steps_.assign(size(), -1);
    prepared_opponents_.resize(size());
  }
  py::gil_scoped_release release;
  ForEach([&](int lane) {
    const auto& engine = engines_[lane];
    if (engine.done() || prepared_steps_[lane] == engine.step_index()) return;
    prepared_opponents_[lane] = opponents_[lane](engine, 1 - seats_[lane]);
    prepared_steps_[lane] = engine.step_index();
  });
}

PlayerAction Batch::OpponentAction(int lane) {
  if (!prepared_steps_.empty() &&
      prepared_steps_[lane] == engines_[lane].step_index()) {
    prepared_steps_[lane] = -1;
    return std::move(prepared_opponents_[lane]);
  }
  return opponents_[lane](engines_[lane], 1 - seats_[lane]);
}

py::dict Batch::Observation(int lane, int player) const {
  if (lane < 0 || lane >= size()) throw std::out_of_range("invalid lane");
  if (player < -1 || player > 1) throw std::out_of_range("invalid player");
  return pyconv::ObservationToPy(engines_[lane], player < 0 ? seats_[lane] : player);
}

py::dict Batch::Action(int lane, py::array actions) const {
  Check(actions, {size(), slots(), 2}, py::dtype::of<int64_t>(), false);
  if (lane < 0 || lane >= size()) throw std::out_of_range("invalid lane");
  return pyconv::PlayerActionToPy(Decode(lane, static_cast<const int64_t*>(actions.data()) +
                                               static_cast<size_t>(lane) * slots() * 2));
}

py::dict Batch::ContractAction(int lane, py::array contracts, int player) const {
  Check(contracts, {size(), ContractSize(config_)}, py::dtype::of<int64_t>(), false);
  if (lane < 0 || lane >= size()) throw std::out_of_range("invalid lane");
  if (player < -1 || player > 1) throw std::out_of_range("invalid player");
  const auto* plan = static_cast<const int64_t*>(contracts.data()) +
                     static_cast<size_t>(lane) * ContractSize(config_);
  ValidateContract(config_, plan, units_);
  return pyconv::PlayerActionToPy(ExecuteContract(
      engines_[lane], player < 0 ? seats_[lane] : player, plan, units_));
}

int Batch::completed() const {
  return std::count_if(engines_.begin(), engines_.end(), [](const Engine& e) { return e.done(); });
}

void Batch::Apply(int lane, const PlayerAction& left, const PlayerAction& right) {
  engines_[lane].Step(left, right);
  history_[lane].Record(engines_[lane]);
}

int64_t Batch::transitions() const {
  int64_t result = 0;
  for (const auto& engine : engines_) result += engine.step_index();
  return result;
}

}  // namespace kagg::parallel
