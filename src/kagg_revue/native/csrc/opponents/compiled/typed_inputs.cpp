// Four-day input forecast with direct board indexing and small integer state.
#include "opponents/compiled/typed_support.hpp"

#include <algorithm>
#include <array>
#include <bitset>

namespace kagg::opponents::compiled {
namespace {
using Position = std::array<int64_t, 2>;
struct Target {
  Value crop;
  int64_t birth, yield, until, first, last, cap;
  Value watered;
  int64_t harvest = -1;
  Values water;
};
Position Coordinates(const Value& value) {
  const auto& position = typed::Sequence(value);
  if (position.size() != 2) throw typed::Unsupported{};
  return {typed::Integer(position[0]), typed::Integer(position[1])};
}
}  // namespace

std::optional<Value> TypedInputs(Context&, const ScopePtr& scope) {
  try {
    using namespace typed;
    Builtins(scope, {"int", "list", "range", "min", "max", "enumerate", "tuple",
                     "isinstance", "len", "set", "sum"});
    const auto observation = scope->Local("obs");
    const int64_t step = Integer(Field(observation, "step"));
    const int64_t player = Integer(Field(observation, "player"));
    if (step < 0 || step > 719 || player < 0 || player > 1) return std::nullopt;
    const auto& farms = Sequence(Field(observation, "farms"));
    if (farms.size() < 2) return std::nullopt;
    const auto& farm = farms[player];
    std::vector<Position> positions{Coordinates(Field(farm, "farmer"))};
    const auto& hands = Sequence(Field(farm, "hands"));
    const int64_t expected = Integer(scope->Local("expected"));
    const int64_t hand_count = std::clamp(expected < 0 ? static_cast<int64_t>(hands.size()) + expected : expected,
                                         int64_t{0}, static_cast<int64_t>(hands.size()));
    for (int64_t i = 0; i < hand_count; ++i) positions.push_back(Coordinates(hands[i]));
    const int64_t day = step / 24;
    const auto crops = scope->Global("_R51_INPUT_CROPS");
    if (!Is(crops, Kind::kDict)) return std::nullopt;
    std::array<std::optional<Target>, 100> targets;
    const auto& rows = Sequence(Field(farm, "tiles"));
    if (rows.size() > 10) return std::nullopt;
    for (size_t y = 0; y < rows.size(); ++y) {
      const auto& row = Sequence(rows[y]);
      if (row.size() > 10) return std::nullopt;
      for (size_t x = 0; x < row.size(); ++x) {
        const auto& tile = row[x];
        if (!Is(tile, Kind::kDict)) continue;
        const auto& crop = Maybe(tile, "crop");
        if (!Contains(crops, crop)) continue;
        const auto specification = Get(crops, crop);
        const auto& spec = Sequence(specification);
        if (spec.size() != 3) return std::nullopt;
        const int64_t birth = Integer(Field(tile, "planted_day"));
        const int64_t first = Integer(spec[0]), last = Integer(spec[1]);
        if (1 <= day - birth && day - birth < last) {
          targets[y * 10 + x] = Target{crop, birth, Integer(Field(tile, "yield_units")),
              Integer(GetOr(tile, "fertilized_until_day", -1)), first, last, Integer(spec[2]),
              GetOr(tile, "watered_today", false), -1, {}};
        }
      }
    }
    constexpr std::array<Position, 4> access = {{{4, 4}, {5, 4}, {4, 5}, {5, 5}}};
    std::array<std::bitset<100>, 4> seen;
    const auto routes = Member(Member(scope->Global("_IMPL"), "chassis"), "routes");
    const auto route = scope->Local("route"), moves = scope->Global("MOVES");
    if (!Is(routes, Kind::kDict) || !Is(moves, Kind::kDict)) return std::nullopt;
    for (int64_t turn = step; turn < std::min(int64_t{712}, (day + 4) * 24); ++turn) {
      const auto tape = Get(routes, turn >= 648 ? Value(2) : route);
      const auto& actions = Sequence(tape);
      if (turn >= static_cast<int64_t>(actions.size())) return std::nullopt;
      const auto& action = actions[turn];
      Values units{Maybe(action, "farmer")};
      const auto& workers = Maybe(action, "hands");
      if (workers) {
        const auto& values = Sequence(workers);
        units.insert(units.end(), values.begin(), values.end());
      }
      for (size_t actor = 0; actor < std::min(units.size(), positions.size()); ++actor) {
        if (!units[actor]) continue;
        const auto& command = Sequence(units[actor]);
        if (command.empty()) continue;
        const auto& operation = command[0];
        if (!Is(operation, Kind::kString)) return std::nullopt;
        auto& position = positions[actor];
        const auto [x, y] = position;
        if (0 <= x && x < 10 && 0 <= y && y < 10) {
          const int cell = static_cast<int>(y * 10 + x);
          auto& target = targets[cell];
          if (target && target->harvest < 0) {
            const int offset = static_cast<int>(turn / 24 - day);
            if (operation.string() == "WATER" && !seen[offset][cell]) {
              seen[offset].set(cell);
              const int64_t age = turn / 24 - target->birth;
              if (!(turn / 24 == day && target->watered) && target->first <= age && age <= target->last)
                target->water.emplace_back(turn);
            }
            if (operation.string() == "HARVEST") target->harvest = turn;
          }
        }
        if (Contains(moves, operation)) {
          const auto delta = Coordinates(Get(moves, operation));
          position = {std::clamp(x + delta[0], int64_t{0}, int64_t{9}),
                      std::clamp(y + delta[1], int64_t{0}, int64_t{9})};
        }
      }
      const auto market = GetOr(action, "market", List());
      for (const auto& order : Sequence(market)) {
        if (!order) continue;
        const auto& parts = Sequence(order);
        if (parts.empty() || !Equal(parts[0], "HIRE")) continue;
        std::array<int, 4> occupancy{};
        for (const auto& position : positions)
          for (size_t i = 0; i < access.size(); ++i) occupancy[i] += position == access[i];
        positions.push_back(access[std::min_element(occupancy.begin(), occupancy.end()) - occupancy.begin()]);
      }
      if ((turn + 1) % 24 == 0) positions = {{4, 4}};
    }
    Value result = Dict();
    for (size_t cell = 0; cell < targets.size(); ++cell) {
      if (!targets[cell]) continue;
      auto& target = *targets[cell];
      Put(result, Tuple({static_cast<int>(cell % 10), static_cast<int>(cell / 10)}),
          Dict({{"crop", target.crop}, {"birth", target.birth}, {"yield", target.yield},
                {"until", target.until}, {"watered", target.watered},
                {"water", List(std::move(target.water))},
                {"harvest", target.harvest < 0 ? Value{} : Value(target.harvest)},
                {"first", target.first}, {"last", target.last}, {"cap", target.cap}}));
    }
    return result;
  } catch (const typed::Unsupported&) {
    return std::nullopt;
  }
}
}  // namespace kagg::opponents::compiled
