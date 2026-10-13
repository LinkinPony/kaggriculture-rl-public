#include "boatlee/runtime.hpp"

#include <algorithm>
#include <array>
#include <cstdint>
#include <memory>
#include <stdexcept>
#include <utility>

#include "action_codec.hpp"
#include "boatlee/detail.hpp"

namespace kagg::boatlee {
namespace {

int TapeIndex(Tape tape) { return static_cast<int>(tape); }

}  // namespace

Portfolio::Portfolio(const int64_t* tokens, const int64_t* quantities,
                     const int64_t* decision_counts,
                     const int64_t* unit_counts, int width,
                     int maximum_market_orders) {
  if (tokens == nullptr || quantities == nullptr ||
      decision_counts == nullptr || unit_counts == nullptr || width < 1 ||
      maximum_market_orders < 1) {
    throw std::invalid_argument("invalid Boatlee v21 portfolio buffers");
  }
  actions_.reserve(static_cast<size_t>(kTapeCount) * kTapeTurns);
  for (int tape = 0; tape < kTapeCount; ++tape) {
    for (int step = 0; step < kTapeTurns; ++step) {
      const size_t row = static_cast<size_t>(tape) * kTapeTurns + step;
      const int64_t decisions = decision_counts[row];
      const int64_t units = unit_counts[row];
      if (decisions < units || decisions > width || units < 1) {
        throw std::invalid_argument(
            "Boatlee v21 route action shape is invalid");
      }
      const size_t offset = row * width;
      actions_.push_back(policy::DecodePlayerAction(
          tokens + offset, quantities + offset,
          static_cast<int>(decisions), static_cast<int>(units),
          maximum_market_orders));
    }
  }
}

size_t Portfolio::index(Tape tape, int step) const {
  const int tape_index = TapeIndex(tape);
  if (tape_index < 0 || tape_index >= kTapeCount) {
    throw std::out_of_range("Boatlee v21 tape is outside the portfolio");
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
  return detail::SellTotals(action(tape, step));
}

struct Session::Impl {
  explicit Impl(std::shared_ptr<const Portfolio> value)
      : portfolio(std::move(value)) {
    if (!portfolio) {
      throw std::invalid_argument("Boatlee v21 portfolio is null");
    }
  }

  std::shared_ptr<const Portfolio> portfolio;
  std::array<detail::OuterState, 2> outer;
  std::array<detail::MoonState, 2> moon;
  std::array<detail::ReplayState, 2> mutoy;
  std::array<detail::ReplayState, 2> munib_base;
  std::array<detail::ReplayState, 2> munib_front;
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
      throw std::invalid_argument("Boatlee v21 player must be 0 or 1");
    }
    const int step = engine.step_index();
    detail::OuterState& outer = impl_->outer[player];
    if (step == 0 || step < outer.last_step) {
      outer = detail::OuterState{};
      impl_->moon[player] = detail::MoonState{};
      impl_->mutoy[player] = detail::ReplayState{};
      impl_->munib_base[player] = detail::ReplayState{};
      impl_->munib_front[player] = detail::ReplayState{};
    }
    outer.last_step = step;
    const Farm& opponent = engine.farm(1 - player);
    const double opponent_money = opponent.money;
    const int opponent_hires = opponent.hires_today;

    if (step == 0) {
      outer.previous_opponent_money = opponent_money;
      outer.has_previous_opponent_money = true;
      PlayerAction moon_action = detail::MoonAct(
          *impl_->portfolio, engine, player, &impl_->moon[player]);
      static_cast<void>(detail::ReplayAct(
          *impl_->portfolio, engine, player, Tape::kMutoy, false,
          &impl_->mutoy[player]));
      static_cast<void>(detail::ReplayAct(
          *impl_->portfolio, engine, player, Tape::kMunib, false,
          &impl_->munib_base[player]));
      static_cast<void>(detail::ReplayAct(
          *impl_->portfolio, engine, player, Tape::kMunib, true,
          &impl_->munib_front[player]));
      return moon_action;
    }

    if (step == 1 && outer.route == detail::Route::kNone &&
        opponent_hires >= 4 && opponent_money <= 20.0) {
      outer.route = detail::Route::kMutoy;
    }
    if (outer.route == detail::Route::kMutoy) {
      outer.previous_opponent_money = opponent_money;
      outer.has_previous_opponent_money = true;
      return detail::ReplayAct(*impl_->portfolio, engine, player,
                               Tape::kMutoy, false,
                               &impl_->mutoy[player]);
    }

    PlayerAction moon_action = detail::MoonAct(
        *impl_->portfolio, engine, player, &impl_->moon[player]);
    PlayerAction munib_base = detail::ReplayAct(
        *impl_->portfolio, engine, player, Tape::kMunib, false,
        &impl_->munib_base[player]);
    PlayerAction munib_front = detail::ReplayAct(
        *impl_->portfolio, engine, player, Tape::kMunib, true,
        &impl_->munib_front[player]);

    if (step == 217 && outer.has_previous_opponent_money &&
        outer.previous_opponent_money - opponent_money >= 100.0) {
      outer.market_overlay = true;
    }
    outer.previous_opponent_money = opponent_money;
    outer.has_previous_opponent_money = true;

    if (outer.route == detail::Route::kNone &&
        !detail::ActionsEqual(moon_action, munib_front)) {
      const auto& shops = engine.town_shops();
      const bool bakery_regime =
          shops.size() >= 3 && shops[0] == 0 && shops[1] == 0 &&
          shops[2] == 0;
      const bool extra_regime =
          shops.size() >= 3 && shops[0] == 4 && shops[1] == 3 &&
          shops[2] == 3;
      outer.route = step < 200 || bakery_regime || extra_regime
                        ? detail::Route::kMunib
                        : detail::Route::kMoon;
    }
    if (outer.route == detail::Route::kMunib) return munib_front;
    if (outer.market_overlay) {
      return detail::ApplyMarketDelta(std::move(moon_action), munib_base,
                                      munib_front);
    }
    return moon_action;
  } catch (...) {
    PlayerAction fallback;
    detail::AlignHands(engine, player == 1 ? 1 : 0, &fallback);
    return fallback;
  }
}

}  // namespace kagg::boatlee
