#include <algorithm>

#include "opponents/compiled/policy.hpp"

namespace kagg::opponents::compiled {
namespace {
int Item(const Value& value, int count) {
  if (!Is(value, Kind::kString)) return -1;
  for (int i = 0; i < count; ++i)
    if (value.string() == kItemNames[i]) return i;
  return -1;
}
UnitAction Unit(const Value& value) {
  UnitAction out{UnitOp::kInvalid, -1, 1};
  if (!Is(value, Kind::kList) || !static_cast<bool>(value)) return out;
  const auto& v = value.node()->sequence;
  if (!Is(v[0], Kind::kString)) return out;
  static const std::vector<std::pair<const char*, UnitOp>> operations = {
      {"NORTH", UnitOp::kNorth},
      {"SOUTH", UnitOp::kSouth},
      {"EAST", UnitOp::kEast},
      {"WEST", UnitOp::kWest},
      {"PASS", UnitOp::kPass},
      {"PICKUP", UnitOp::kPickup},
      {"DROP", UnitOp::kDrop},
      {"PLACE", UnitOp::kPlace},
      {"PLANT", UnitOp::kPlant},
      {"WATER", UnitOp::kWater},
      {"HARVEST", UnitOp::kHarvest},
      {"FERTILIZE", UnitOp::kFertilize},
      {"DIG", UnitOp::kDig},
      {"BUILD_COOP", UnitOp::kBuildCoop},
      {"BUILD_PASTURE", UnitOp::kBuildPasture},
      {"FEED", UnitOp::kFeed},
      {"COLLECT_FERTILIZER", UnitOp::kCollectFertilizer},
      {"CARE", UnitOp::kCare}};
  for (const auto& [name, operation] : operations)
    if (v[0].string() == name) {
      out.op = operation;
      break;
    }
  if (out.op == UnitOp::kPickup || out.op == UnitOp::kPlace ||
      out.op == UnitOp::kPlant) {
    if (v.size() < 2) return {UnitOp::kInvalid, -1, 1};
    out.arg = Item(v[1], out.op == UnitOp::kPlant ? kNumCrops : kNumItems);
    if (out.arg < 0) return {UnitOp::kInvalid, -1, 1};
    if (v.size() > 2 && out.op != UnitOp::kPlant) out.n = v[2].integer_value();
  }
  return out;
}
std::optional<MarketOrder> Order(const Value& value) {
  if (!Is(value, Kind::kList) || !static_cast<bool>(value)) return {};
  const auto& v = value.node()->sequence;
  if (!Is(v[0], Kind::kString)) return {};
  const auto& op = v[0].string();
  if (op == "HIRE") return MarketOrder{OrderKind::kHire, 0, 0};
  if (op == "BUY_LAND") return MarketOrder{OrderKind::kBuyLand, 0, 0};
  if (v.size() < 3 || !v[2].numeric() || v[2].integer_value() <= 0) return {};
  OrderKind kind;
  if (op == "BUY_SEED")
    kind = OrderKind::kBuySeed;
  else if (op == "BUY_PRODUCT")
    kind = OrderKind::kBuyProduct;
  else if (op == "BUY_ANIMAL")
    kind = OrderKind::kBuyAnimal;
  else if (op == "SELL")
    kind = OrderKind::kSell;
  else
    return {};
  int item = Item(v[1], kind == OrderKind::kBuySeed     ? kNumCrops
                        : kind == OrderKind::kBuyAnimal ? kNumItems
                                                        : kNumProducts);
  if (kind == OrderKind::kBuyAnimal) item -= item::kGoose;
  if (item < 0) return {};
  return MarketOrder{kind, item, v[2].integer_value()};
}
}  // namespace
PlayerAction Action(const Value& value, int maximum_orders) {
  PlayerAction out;
  if (!Is(value, Kind::kDict)) return out;
  if (Contains(value, "farmer")) out.farmer = Unit(Get(value, "farmer"));
  auto hands = GetOr(value, "hands");
  if (Is(hands, Kind::kList))
    for (const auto& action : hands.node()->sequence)
      out.hands.push_back(Unit(action));
  auto market = GetOr(value, "market");
  if (Is(market, Kind::kList)) {
    const size_t n = std::min(market.node()->sequence.size(),
                              static_cast<size_t>(maximum_orders));
    for (size_t i = 0; i < n; ++i)
      out.market.push_back(Order(market.node()->sequence[i]));
  }
  return out;
}
}  // namespace kagg::opponents::compiled
