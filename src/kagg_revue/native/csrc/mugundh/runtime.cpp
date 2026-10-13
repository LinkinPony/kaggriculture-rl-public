#include "mugundh/runtime.hpp"

#include <algorithm>
#include <array>
#include <cstdint>
#include <memory>
#include <stdexcept>
#include <utility>

#include "action_codec.hpp"
#include "mugundh/detail.hpp"

namespace kagg::mugundh {
namespace {

int TapeIndex(Tape tape) { return static_cast<int>(tape); }

std::array<int64_t, kNumProducts> SellTotals(const PlayerAction& action) {
  std::array<int64_t, kNumProducts> result{};
  for (const auto& slot : action.market) {
    if (slot.has_value() && slot->kind == OrderKind::kSell &&
        slot->item >= 0 && slot->item < kNumProducts) {
      result[slot->item] += std::max<int64_t>(0, slot->remaining);
    }
  }
  return result;
}

}  // namespace

Portfolio::Portfolio(const int64_t* tokens, const int64_t* quantities,
                     const int64_t* decision_counts,
                     const int64_t* unit_counts, int width) {
  if (tokens == nullptr || quantities == nullptr || decision_counts == nullptr ||
      unit_counts == nullptr || width < 1) {
    throw std::invalid_argument("invalid Mugundh v21 portfolio buffers");
  }
  actions_.reserve(static_cast<size_t>(kTapeCount) * kTapeTurns);
  for (int tape = 0; tape < kTapeCount; ++tape) {
    for (int step = 0; step < kTapeTurns; ++step) {
      const size_t row = static_cast<size_t>(tape) * kTapeTurns + step;
      const int64_t decisions = decision_counts[row];
      const int64_t units = unit_counts[row];
      if (decisions < units || decisions > width || units < 1) {
        throw std::invalid_argument("Mugundh v21 route action shape is invalid");
      }
      const size_t offset = row * width;
      actions_.push_back(policy::DecodePlayerAction(
          tokens + offset, quantities + offset, static_cast<int>(decisions),
          static_cast<int>(units), 10));
    }
  }
}

size_t Portfolio::index(Tape tape, int step) const {
  const int tape_index = TapeIndex(tape);
  if (tape_index < 0 || tape_index >= kTapeCount) {
    throw std::out_of_range("Mugundh v21 tape is outside the portfolio");
  }
  const int bounded = std::clamp(step, 0, kTapeTurns - 1);
  return static_cast<size_t>(tape_index) * kTapeTurns + bounded;
}

const PlayerAction& Portfolio::action(Tape tape, int step) const {
  return actions_[index(tape, step)];
}

UnitAction Portfolio::unit_action(Tape tape, int step, int unit_index) const {
  const PlayerAction& route_action = action(tape, step);
  if (unit_index == 0) return route_action.farmer;
  const int hand = unit_index - 1;
  return hand >= 0 && hand < static_cast<int>(route_action.hands.size())
             ? route_action.hands[hand]
             : detail::Pass();
}

std::array<int64_t, kNumProducts> Portfolio::sell_totals(Tape tape,
                                                         int step) const {
  return SellTotals(action(tape, step));
}

struct Session::Impl {
  explicit Impl(std::shared_ptr<const Portfolio> value)
      : portfolio(std::move(value)) {
    if (!portfolio) {
      throw std::invalid_argument("Mugundh v21 portfolio is null");
    }
  }

  std::shared_ptr<const Portfolio> portfolio;
  std::array<detail::SeatState, 2> seats;
};

Session::Session(std::shared_ptr<const Portfolio> portfolio)
    : impl_(std::make_unique<Impl>(std::move(portfolio))) {}

Session::Session(const Session& other)
    : impl_(std::make_unique<Impl>(*other.impl_)) {}

Session::~Session() = default;
Session::Session(Session&&) noexcept = default;
Session& Session::operator=(Session&&) noexcept = default;

PlayerAction Session::Act(const Engine& engine, int player) {
  try {
    if (player < 0 || player > 1) {
      throw std::invalid_argument("Mugundh v21 player must be 0 or 1");
    }
    detail::SeatState& state = impl_->seats[player];
    const int step = engine.step_index();
    if (step == 0 || step < state.last_step) state = detail::SeatState{};
    state.last_step = step;
    const Tape tape = detail::SelectTape(engine, player, &state);
    PlayerAction action = impl_->portfolio->action(tape, step);
    action = detail::ApplyWeedRepair(*impl_->portfolio, engine, player, tape,
                                     std::move(action), &state.repair);
    action = detail::ApplyRoomEvac(engine, player, std::move(action),
                                   &state.room);
    action = detail::RepayShift(engine, std::move(action), &state.shift);
    action = detail::RankSellSlots(engine, std::move(action));
    action = detail::ApplyPreemptShift(*impl_->portfolio, engine, player, tape,
                                       std::move(action), &state.shift);
    action = detail::ApplyR5Counter(*impl_->portfolio, engine, player,
                                    std::move(action), &state.r5);
    action = detail::ApplyMdCounter(*impl_->portfolio, engine, player,
                                    std::move(action), &state.md);
    action = detail::ApplyRoomGuard(engine, player, std::move(action));
    action = detail::ApplyTerminalLiquidation(engine, player,
                                               std::move(action));
    action = detail::ApplySellDivergenceGuard(engine, player,
                                               std::move(action));
    detail::AlignHands(engine, player, &action);
    const size_t maximum_orders = static_cast<size_t>(
        std::max(1, engine.config().max_market_orders));
    if (action.market.size() > maximum_orders) {
      action.market.resize(maximum_orders);
    }
    return action;
  } catch (...) {
    PlayerAction fallback;
    detail::AlignHands(engine, player == 1 ? 1 : 0, &fallback);
    return fallback;
  }
}

}  // namespace kagg::mugundh
