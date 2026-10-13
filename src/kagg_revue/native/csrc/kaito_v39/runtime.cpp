#include "kaito_v39/runtime.hpp"

#include <array>
#include <memory>
#include <optional>
#include <stdexcept>
#include <utility>

#include "kaito_v39/policy.hpp"
#include "kaito_v39/strategy.hpp"
#include "kaito_v48_support.hpp"

namespace kagg::kaito_v39 {
namespace {

constexpr std::array<int, kHistoryCheckpoints> kCheckpoints = {
    96, 120, 122, 132, 144,
};

struct SeatState {
  int last_step = -1;
  bool stage1_selected = false;
  bool wool = false;
  std::optional<Route> base_route;
  std::optional<Route> final_route;
  bool delayed_compatible = true;
  std::array<std::optional<RouterPart>, kHistoryCheckpoints> history;
  std::array<RouteState, kRouteCount> routes;
};

int RouteIndex(Route route) { return static_cast<int>(route); }

void CaptureHistory(const Engine& engine, int player, SeatState* state) {
  const int step = engine.step_index();
  for (int index = 0; index < kHistoryCheckpoints; ++index) {
    if (step == kCheckpoints[index]) {
      state->history[index] = ExtractRouterPart(engine, player);
      return;
    }
  }
}

PlayerAction ActRoute(const Portfolio& portfolio, const Engine& engine,
                      int player, Route route, SeatState* state) {
  return ApplyRoute(portfolio, engine, player, route,
                    &state->routes[RouteIndex(route)]);
}

}  // namespace

struct Session::Impl {
  explicit Impl(std::shared_ptr<const Portfolio> value)
      : portfolio(std::move(value)) {
    if (!portfolio) throw std::invalid_argument("Kaito v39 portfolio is null");
  }

  std::shared_ptr<const Portfolio> portfolio;
  std::array<SeatState, 2> seats;
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
      throw std::invalid_argument("Kaito v39 player must be 0 or 1");
    }
    SeatState& seat = impl_->seats[player];
    const int step = engine.step_index();
    if (step == 0 || step < seat.last_step) seat = SeatState{};
    seat.last_step = step;
    CaptureHistory(engine, player, &seat);

    if (step < 96) {
      ActRoute(*impl_->portfolio, engine, player, Route::kV36, &seat);
      PlayerAction v37 =
          ActRoute(*impl_->portfolio, engine, player, Route::kV37, &seat);
      ActRoute(*impl_->portfolio, engine, player, Route::kWool, &seat);
      ActRoute(*impl_->portfolio, engine, player, Route::kAlt, &seat);
      return v37;
    }

    if (!seat.stage1_selected) {
      const RouterPart current = ExtractRouterPart(engine, player);
      seat.wool = SelectStage1Wool(*impl_->portfolio, current);
      seat.stage1_selected = true;
      if (seat.wool) {
        seat.final_route = Route::kWool;
      } else {
        seat.base_route = SelectNestedRoute(*impl_->portfolio, current);
      }
    }
    if (seat.wool) {
      return ActRoute(*impl_->portfolio, engine, player, Route::kWool, &seat);
    }
    if (!seat.base_route.has_value()) {
      seat.base_route = SelectNestedRoute(
          *impl_->portfolio, ExtractRouterPart(engine, player));
    }

    if (step < 144) {
      PlayerAction base = ActRoute(*impl_->portfolio, engine, player,
                                   *seat.base_route, &seat);
      PlayerAction alt =
          ActRoute(*impl_->portfolio, engine, player, Route::kAlt, &seat);
      if (seat.delayed_compatible && !ActionsEqual(base, alt)) {
        seat.delayed_compatible = false;
      }
      return base;
    }

    if (!seat.final_route.has_value()) {
      seat.final_route =
          seat.delayed_compatible &&
                  SelectStage2Alt(*impl_->portfolio, seat.history)
              ? Route::kAlt
              : *seat.base_route;
    }
    return ActRoute(*impl_->portfolio, engine, player, *seat.final_route,
                    &seat);
  } catch (...) {
    PlayerAction fallback;
    kaito::AlignHands(engine, player == 1 ? 1 : 0, &fallback);
    return fallback;
  }
}

}  // namespace kagg::kaito_v39
