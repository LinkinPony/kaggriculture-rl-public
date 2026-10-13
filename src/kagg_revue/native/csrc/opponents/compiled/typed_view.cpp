#include "opponents/compiled/typed_support.hpp"

#include <algorithm>

namespace kagg::opponents::compiled {
namespace {
Value Integers(const Value& source, bool nonnegative) {
  if (!Is(source, Kind::kDict)) throw typed::Unsupported{};
  Pairs items;
  items.reserve(source.node()->entries.size());
  for (const auto& [key, value] : source.node()->entries) {
    const auto quantity = typed::Integer(value);
    items.emplace_back(key, nonnegative ? std::max(int64_t{0}, quantity) : quantity);
  }
  return Dict(std::move(items));
}
Value OrEmpty(const Value& value, Value empty) { return value ? value : empty; }
}  // namespace

std::optional<Value> TypedView(Context&, const ScopePtr& scope) {
  try {
    using namespace typed;
    Builtins(scope, {"list", "dict", "max", "float", "len", "int", "isinstance"});
    Helper(scope, "_int", Specialization::kInteger);
    Helper(scope, "_get", Specialization::kDictGet);
    const auto self = scope->Local("self"), observation = scope->Local("observation");
    const auto player = Integer(scope->Local("player"));
    if (player < 0 || player > 1 || !Is(self, Kind::kObject)) return std::nullopt;
    const auto& farms = Sequence(Field(observation, "farms"));
    if (farms.size() < 2) return std::nullopt;
    const auto& farm = farms[player];
    const auto private_state = OrEmpty(Maybe(observation, "private"), Dict());
    const auto shed = Integers(OrEmpty(Maybe(private_state, "shed"), Dict()), true);
    const auto seeds = Dictionary(OrEmpty(Maybe(private_state, "seeds"), Dict()));
    Values inventories;
    auto raw_inventories = OrEmpty(Maybe(private_state, "inventories"), List());
    for (const auto& inventory : Sequence(raw_inventories))
      inventories.push_back(Dictionary(OrEmpty(inventory, Dict())));
    const auto market = OrEmpty(Maybe(observation, "market"), Dict());
    const auto prices = Integers(OrEmpty(Maybe(market, "prices"), Dict()), false);
    const auto money = Maybe(farm, "money");
    if (money && !money.numeric()) return std::nullopt;
    const auto tiles = OrEmpty(Maybe(farm, "tiles"), List());
    const int64_t board = Sequence(tiles).empty()
        ? Integer(Field(scope->Local("cfg"), "board_size"))
        : static_cast<int64_t>(Sequence(tiles).size());
    Values positions{Maybe(farm, "farmer")};
    const auto hands = OrEmpty(Maybe(farm, "hands"), List());
    for (const auto& hand : Sequence(hands)) positions.push_back(List(Sequence(hand)));
    const auto hires = Maybe(farm, "hires_today");
    const auto quadrants = OrEmpty(Maybe(farm, "unlocked_quadrants"), List());
    Value attributes = Dict({{"farm", farm}, {"rival", farms[1 - player]}, {"shed", shed},
        {"seeds", seeds}, {"invs", List(std::move(inventories))}, {"prices", prices},
        {"money", money ? money.number() : 0.0}, {"tiles", tiles}, {"board", board},
        {"positions", List(std::move(positions))},
        {"hires_today", hires.none() ? int64_t{0} : Integer(hires)},
        {"quadrants", static_cast<int64_t>(Sequence(quadrants).size())}});
    // Commit only after all guards pass; fallback observes the original object.
    if (self.node()->attributes.none()) self.node()->attributes = Dict();
    Merge(self.node()->attributes, attributes);
    return Value{};
  } catch (const typed::Unsupported&) {
    return std::nullopt;
  }
}

std::optional<Value> TypedClone(Context&, const ScopePtr& scope) {
  try {
    using namespace typed;
    Builtins(scope, {"dict", "list", "isinstance"});
    const auto farm = scope->Local("farm"), private_state = scope->Local("private");
    auto copied = Dictionary(farm), copied_private = Dictionary(private_state);
    Values tiles;
    for (const auto& row : Sequence(Field(farm, "tiles"))) {
      Values line;
      for (const auto& tile : Sequence(row))
        line.push_back(Is(tile, Kind::kDict) ? Dictionary(tile) : tile);
      tiles.push_back(List(std::move(line)));
    }
    Put(copied, "tiles", List(std::move(tiles)));
    Put(copied, "farmer", List(Sequence(Field(farm, "farmer"))));
    Values hands, inventories;
    for (const auto& hand : Sequence(Field(farm, "hands"))) hands.push_back(List(Sequence(hand)));
    Put(copied, "hands", List(std::move(hands)));
    Put(copied, "unlocked_quadrants", List(Sequence(Field(farm, "unlocked_quadrants"))));
    Put(copied_private, "shed", Dictionary(Field(private_state, "shed")));
    Put(copied_private, "seeds", Dictionary(Field(private_state, "seeds")));
    for (const auto& inventory : Sequence(Field(private_state, "inventories")))
      inventories.push_back(Dictionary(inventory));
    Put(copied_private, "inventories", List(std::move(inventories)));
    return Tuple({copied, copied_private});
  } catch (const typed::Unsupported&) {
    return std::nullopt;
  }
}
}  // namespace kagg::opponents::compiled
