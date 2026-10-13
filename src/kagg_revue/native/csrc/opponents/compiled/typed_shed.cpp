#include "opponents/compiled/typed_support.hpp"

#include <algorithm>
#include <array>

#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
namespace {
struct Stock {
  std::array<Value, 64> keys;
  std::array<int64_t, 64> amounts{};
  size_t size = 0;
  int Find(const Value& item) const {
    if (!Is(item, Kind::kString)) throw typed::Unsupported{};
    for (size_t i = 0; i < size; ++i)
      if (keys[i].string() == item.string()) return static_cast<int>(i);
    return -1;
  }
  int Add(const Value& item, int64_t initial = 0) {
    const int old = Find(item);
    if (old >= 0) return old;
    if (size == keys.size()) throw typed::Unsupported{};
    keys[size] = item;
    amounts[size] = initial;
    return static_cast<int>(size++);
  }
  Value Mapping() const {
    Pairs rows;
    rows.reserve(size);
    for (size_t i = 0; i < size; ++i) rows.emplace_back(keys[i], amounts[i]);
    return Dict(std::move(rows));
  }
};
int64_t Quantity(const Values& action) {
  return std::max(int64_t{0}, action.size() >= 3 ? typed::Integer(action[2]) : 1);
}
}  // namespace

std::optional<Value> TypedShed(Context&, const ScopePtr& scope) {
  try {
    using namespace typed;
    Builtins(scope, {"list", "sum", "min", "max", "len", "int", "isinstance"});
    Helper(scope, "_int", Specialization::kInteger);
    Helper(scope, "_get", Specialization::kDictGet);
    const auto adjacent = scope->Global("_shed_adjacent");
    if (!Is(adjacent, Kind::kFunction) ||
        adjacent.node()->function->code != &Code_e7ddba6e5f99eff1bd95)
      return std::nullopt;
    const auto self = scope->Local("self"), action = scope->Local("action");
    const auto view = scope->Local("view");
    const auto inv_method = Attribute(view, "inv");
    if (!Is(inv_method, Kind::kFunction) ||
        inv_method.node()->function->code != &Code_5f08dea41056bb7f41f8 ||
        !Identical(inv_method.node()->function->bound, view)) return std::nullopt;
    const int64_t cap = Integer(Field(Member(self, "cfg"), "shed_capacity"));
    const auto& shed = Member(view, "shed");
    if (!Is(shed, Kind::kDict)) return std::nullopt;
    Stock stock;
    const auto products = scope->Global("PRODUCTS");
    for (const auto& item : Sequence(products))
      stock.amounts[stock.Add(item)] = Integer(GetOr(shed, item, 0));
    for (const auto& [item, quantity] : shed.node()->entries)
      if (stock.Find(item) < 0) stock.Add(item, Integer(quantity));
    int64_t total = 0;
    for (size_t i = 0; i < stock.size; ++i) total += stock.amounts[i];
    const auto& positions = Sequence(Member(view, "positions"));
    const auto& inventories = Sequence(Member(view, "invs"));
    const int64_t board = Integer(Member(view, "board"));
    if (board <= 0) return std::nullopt;
    const int64_t half = board / 2;
    Values units{Maybe(action, "farmer")};
    const auto& hands = Maybe(action, "hands");
    if (hands) {
      const auto& rows = Sequence(hands);
      units.insert(units.end(), rows.begin(), rows.end());
    }
    const auto animals = scope->Global("ANIMAL_STRUCTURE");
    if (!Is(animals, Kind::kDict)) return std::nullopt;
    for (size_t i = 0; i < std::min(units.size(), positions.size()); ++i) {
      const auto& position = positions[i];
      if (!Is(position, Kind::kList) && !Is(position, Kind::kTuple)) continue;
      const auto& xy = Sequence(position);
      if (xy.size() < 2) continue;
      const int64_t x = Integer(xy[0]), y = Integer(xy[1]);
      if ((x != half - 1 && x != half) || (y != half - 1 && y != half)) continue;
      const Value inventory = i < inventories.size() ? inventories[i] : Dict();
      if (!Is(inventory, Kind::kDict)) return std::nullopt;
      if (!units[i]) continue;
      const auto& commands = Sequence(units[i]);
      if (commands.empty() || !Is(commands[0], Kind::kString)) return std::nullopt;
      const auto& operation = commands[0].string();
      if (operation == "PICKUP" && commands.size() >= 2) {
        const int index = stock.Find(commands[1]);
        if (index >= 0) {
          const int64_t take = std::min(stock.amounts[index], Quantity(commands));
          stock.amounts[index] -= take;
          total -= take;
        }
      } else if (operation == "DROP") {
        for (const auto& [item, held] : inventory.node()->entries) {
          const int64_t take = std::min(std::max(int64_t{0}, Integer(held)),
                                        std::max(int64_t{0}, cap - total));
          if (take > 0) {
            stock.amounts[stock.Add(item)] += take;
            total += take;
          }
        }
      } else if (operation == "PLACE" && commands.size() >= 2 &&
                 !Contains(animals, commands[1])) {
        const auto& item = commands[1];
        const int64_t take = std::min({Quantity(commands),
            std::max(int64_t{0}, Integer(GetOr(inventory, item, 0))),
            std::max(int64_t{0}, cap - total)});
        if (take > 0) {
          stock.amounts[stock.Add(item)] += take;
          total += take;
        }
      }
    }
    return stock.Mapping();
  } catch (const typed::Unsupported&) {
    return std::nullopt;
  }
}
}  // namespace kagg::opponents::compiled
