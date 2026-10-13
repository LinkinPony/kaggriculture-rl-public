// Immutable routes and public-state memories extracted from Kaito v39.
#pragma once

#include <array>
#include <cstddef>
#include <cstdint>
#include <vector>

#include "engine.hpp"
#include "types.hpp"

namespace kagg::kaito_v39 {

inline constexpr int kRouteCount = 4;
inline constexpr int kRouteTurns = 719;
inline constexpr int kLayoutWidth = 75;
inline constexpr int kActorWidth = 19;
inline constexpr int kNumericWidth = 56;
inline constexpr int kHistoryCheckpoints = 5;

enum class Route : uint8_t { kV36 = 0, kV37, kWool, kAlt };

struct RouterPart {
  std::array<uint8_t, kLayoutWidth> opponent_layout{};
  std::array<double, 8> opponent_counts{};
  std::array<double, kActorWidth> opponent_actors{};
  int opponent_actor_count = 0;
  double opponent_money = 0.0;
  uint8_t opponent_unlocks = 0;
  std::array<double, 10> own_state{};
  std::array<double, 9> prices{};
  std::array<double, 9> inventory{};
  std::array<uint8_t, kNumShops> shops{};
  uint8_t seat = 0;
};

struct Prototype {
  int part_index = -1;
  std::array<double, 2> margins{};
};

struct HistoryPrototype {
  std::array<int, kHistoryCheckpoints> part_indices{};
  std::array<double, 2> margins{};
};

class Portfolio {
 public:
  Portfolio(
      const int64_t* tokens, const int64_t* quantities,
      const int64_t* decision_counts, const int64_t* unit_counts,
      int action_width, int maximum_market_orders,
      const uint8_t* parts_layout, const double* parts_numeric,
      const uint8_t* parts_actor_lengths, const uint8_t* parts_unlocks,
      const uint8_t* parts_shop_counts, const uint8_t* parts_seats,
      int part_count, const int64_t* nested_indices,
      const double* nested_margins, int nested_count,
      const int64_t* fallback_indices, const double* fallback_margins,
      int fallback_count, const int64_t* stage1_indices,
      const double* stage1_margins, int stage1_count,
      const int64_t* stage2_indices, const double* stage2_margins,
      int stage2_count);

  const PlayerAction& action(Route route, int step) const;
  UnitAction unit_action(Route route, int step, int unit_index) const;
  std::array<int64_t, kNumProducts> sell_totals(Route route, int step) const;

  const RouterPart& part(int index) const;
  const std::vector<Prototype>& nested() const { return nested_; }
  const std::vector<Prototype>& fallback() const { return fallback_; }
  const std::vector<Prototype>& stage1() const { return stage1_; }
  const std::vector<HistoryPrototype>& stage2() const { return stage2_; }

 private:
  size_t action_index(Route route, int step) const;

  std::vector<PlayerAction> actions_;
  std::vector<RouterPart> parts_;
  std::vector<Prototype> nested_;
  std::vector<Prototype> fallback_;
  std::vector<Prototype> stage1_;
  std::vector<HistoryPrototype> stage2_;
};

}  // namespace kagg::kaito_v39

