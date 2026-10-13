#include "kaito_v39/portfolio.hpp"

#include <algorithm>
#include <array>
#include <cstdint>
#include <stdexcept>
#include <vector>

#include "action_codec.hpp"

namespace kagg::kaito_v39 {
namespace {

int RouteIndex(Route route) { return static_cast<int>(route); }

UnitAction Pass() { return UnitAction{UnitOp::kPass, -1, 1}; }

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

void LoadPopulation(const int64_t* indices, const double* margins, int count,
                    int part_count, std::vector<Prototype>* output) {
  if (indices == nullptr || margins == nullptr || count < 1) {
    throw std::invalid_argument("Kaito v39 prototype population is empty");
  }
  output->reserve(static_cast<size_t>(count));
  for (int row = 0; row < count; ++row) {
    const int64_t part = indices[row];
    if (part < 0 || part >= part_count) {
      throw std::invalid_argument("Kaito v39 prototype part index is invalid");
    }
    output->push_back(Prototype{
        static_cast<int>(part),
        {margins[static_cast<size_t>(row) * 2],
         margins[static_cast<size_t>(row) * 2 + 1]},
    });
  }
}

}  // namespace

Portfolio::Portfolio(
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
    int stage2_count) {
  if (tokens == nullptr || quantities == nullptr || decision_counts == nullptr ||
      unit_counts == nullptr || action_width < 1 ||
      maximum_market_orders < 1 || parts_layout == nullptr ||
      parts_numeric == nullptr || parts_actor_lengths == nullptr ||
      parts_unlocks == nullptr || parts_shop_counts == nullptr ||
      parts_seats == nullptr || part_count < 1) {
    throw std::invalid_argument("invalid Kaito v39 portfolio buffers");
  }

  actions_.reserve(static_cast<size_t>(kRouteCount) * kRouteTurns);
  for (int route = 0; route < kRouteCount; ++route) {
    for (int step = 0; step < kRouteTurns; ++step) {
      const size_t row = static_cast<size_t>(route) * kRouteTurns + step;
      const int64_t decisions = decision_counts[row];
      const int64_t units = unit_counts[row];
      if (decisions < units || decisions > action_width || units < 1) {
        throw std::invalid_argument("Kaito v39 route action shape is invalid");
      }
      const size_t offset = row * static_cast<size_t>(action_width);
      actions_.push_back(policy::DecodePlayerAction(
          tokens + offset, quantities + offset, static_cast<int>(decisions),
          static_cast<int>(units), maximum_market_orders));
    }
  }

  parts_.reserve(static_cast<size_t>(part_count));
  for (int row = 0; row < part_count; ++row) {
    RouterPart part;
    const size_t layout_offset = static_cast<size_t>(row) * kLayoutWidth;
    std::copy_n(parts_layout + layout_offset, kLayoutWidth,
                part.opponent_layout.begin());
    const size_t numeric_offset = static_cast<size_t>(row) * kNumericWidth;
    std::copy_n(parts_numeric + numeric_offset, 8,
                part.opponent_counts.begin());
    std::copy_n(parts_numeric + numeric_offset + 8, kActorWidth,
                part.opponent_actors.begin());
    part.opponent_actor_count = parts_actor_lengths[row];
    if (part.opponent_actor_count < 1 ||
        part.opponent_actor_count > kActorWidth) {
      throw std::invalid_argument("Kaito v39 actor feature width is invalid");
    }
    part.opponent_money = parts_numeric[numeric_offset + 27];
    part.opponent_unlocks = parts_unlocks[row];
    std::copy_n(parts_numeric + numeric_offset + 28, 10,
                part.own_state.begin());
    std::copy_n(parts_numeric + numeric_offset + 38, 9,
                part.prices.begin());
    std::copy_n(parts_numeric + numeric_offset + 47, 9,
                part.inventory.begin());
    const size_t shop_offset = static_cast<size_t>(row) * kNumShops;
    std::copy_n(parts_shop_counts + shop_offset, kNumShops,
                part.shops.begin());
    part.seat = parts_seats[row];
    if (part.seat > 1) {
      throw std::invalid_argument("Kaito v39 prototype seat is invalid");
    }
    parts_.push_back(part);
  }

  LoadPopulation(nested_indices, nested_margins, nested_count, part_count,
                 &nested_);
  LoadPopulation(fallback_indices, fallback_margins, fallback_count, part_count,
                 &fallback_);
  LoadPopulation(stage1_indices, stage1_margins, stage1_count, part_count,
                 &stage1_);

  if (stage2_indices == nullptr || stage2_margins == nullptr ||
      stage2_count < 1) {
    throw std::invalid_argument("Kaito v39 history population is empty");
  }
  stage2_.reserve(static_cast<size_t>(stage2_count));
  for (int row = 0; row < stage2_count; ++row) {
    HistoryPrototype prototype;
    for (int checkpoint = 0; checkpoint < kHistoryCheckpoints; ++checkpoint) {
      const int64_t part =
          stage2_indices[static_cast<size_t>(row) * kHistoryCheckpoints +
                         checkpoint];
      if (part < -1 || part >= part_count) {
        throw std::invalid_argument(
            "Kaito v39 history prototype part index is invalid");
      }
      prototype.part_indices[checkpoint] = static_cast<int>(part);
    }
    if (prototype.part_indices[kHistoryCheckpoints - 1] < 0) {
      throw std::invalid_argument("Kaito v39 history lacks step 144");
    }
    prototype.margins = {
        stage2_margins[static_cast<size_t>(row) * 2],
        stage2_margins[static_cast<size_t>(row) * 2 + 1],
    };
    stage2_.push_back(prototype);
  }
}

size_t Portfolio::action_index(Route route, int step) const {
  const int route_index = RouteIndex(route);
  if (route_index < 0 || route_index >= kRouteCount) {
    throw std::out_of_range("Kaito v39 route is outside the portfolio");
  }
  const int bounded = std::clamp(step, 0, kRouteTurns - 1);
  return static_cast<size_t>(route_index) * kRouteTurns + bounded;
}

const PlayerAction& Portfolio::action(Route route, int step) const {
  return actions_[action_index(route, step)];
}

UnitAction Portfolio::unit_action(Route route, int step, int unit_index) const {
  const PlayerAction& route_action = action(route, step);
  if (unit_index == 0) return route_action.farmer;
  const int hand = unit_index - 1;
  return hand >= 0 && hand < static_cast<int>(route_action.hands.size())
             ? route_action.hands[hand]
             : Pass();
}

std::array<int64_t, kNumProducts> Portfolio::sell_totals(Route route,
                                                         int step) const {
  return SellTotals(action(route, step));
}

const RouterPart& Portfolio::part(int index) const {
  if (index < 0 || index >= static_cast<int>(parts_.size())) {
    throw std::out_of_range("Kaito v39 prototype part is outside the asset");
  }
  return parts_[index];
}

}  // namespace kagg::kaito_v39
