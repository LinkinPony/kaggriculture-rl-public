// Source-authenticated native hot path for the frozen Kaito v48 notebook.
#pragma once

#include <cstdint>
#include <memory>
#include <vector>

#include "engine.hpp"
#include "types.hpp"

namespace pybind11 {
class module_;
}

namespace kagg::kaito {

inline constexpr int kRouteCount = 6;
inline constexpr int kRouteTurns = 719;

enum class Route : uint8_t {
  kDefault = 0,
  kYarnFast,
  kFarmFast,
  kYarnSecond,
  kYarnThird,
  kBakeryCapital,
};

Route ProposedRoute(const Engine& engine, int player, Route selected);

class Portfolio {
 public:
  Portfolio(const int64_t* tokens, const int64_t* quantities,
            const int64_t* decision_counts, const int64_t* unit_counts,
            int width, int maximum_market_orders);

  const PlayerAction& action(Route route, int step) const;
  UnitAction unit_action(Route route, int step, int unit_index) const;
  std::array<int64_t, kNumProducts> sell_totals(Route route, int step) const;

 private:
  size_t index(Route route, int step) const;

  std::vector<PlayerAction> actions_;
};

class Session {
 public:
  explicit Session(std::shared_ptr<const Portfolio> portfolio);
  ~Session();
  Session(Session&&) noexcept;
  Session& operator=(Session&&) noexcept;
  Session(const Session& other);
  Session& operator=(const Session&) = delete;

  PlayerAction Act(const Engine& engine, int player);
  PlayerAction ActRoute(const Engine& engine, int player, Route route);

 private:
  struct Impl;
  std::unique_ptr<Impl> impl_;
};

void Bind(pybind11::module_& module);

}  // namespace kagg::kaito
