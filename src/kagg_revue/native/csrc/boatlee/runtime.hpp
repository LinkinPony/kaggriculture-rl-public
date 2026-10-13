// Source-authenticated native hot path for the frozen Boatlee v21 notebook.
#pragma once

#include <array>
#include <cstdint>
#include <memory>
#include <vector>

#include "engine.hpp"
#include "types.hpp"

namespace pybind11 {
class module_;
}

namespace kagg::boatlee {

inline constexpr int kTapeCount = 14;
inline constexpr int kTapeTurns = 720;
inline constexpr int kMoonTurns = 719;

enum class Tape : uint8_t {
  kMoonCurrent10C4S = 0,
  kMoonCurrent8C6S,
  kMoonCurrent6C8S,
  kMoonCurrentFirstYarn,
  kMoonCurrentSecondYarn,
  kMoonLegacy10C4S,
  kMoonLegacy8C6S,
  kMoonLegacy6C8S,
  kMoonLegacyFirstYarn,
  kMoonLegacySecondYarn,
  kMoonR5Market,
  kMoonMdMarket,
  kMutoy,
  kMunib,
};

class Portfolio {
 public:
  Portfolio(const int64_t* tokens, const int64_t* quantities,
            const int64_t* decision_counts, const int64_t* unit_counts,
            int width, int maximum_market_orders);

  const PlayerAction& action(Tape tape, int step) const;
  UnitAction unit_action(Tape tape, int step, int unit_index) const;
  std::array<int64_t, kNumProducts> sell_totals(Tape tape, int step) const;

 private:
  size_t index(Tape tape, int step) const;

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

 private:
  struct Impl;
  std::unique_ptr<Impl> impl_;
};

void Bind(pybind11::module_& module);

}  // namespace kagg::boatlee
