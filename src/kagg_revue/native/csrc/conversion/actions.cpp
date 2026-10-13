// Shared official Python/native conversion; no strategy or engine bindings.
#include "py_convert.hpp"
#include "conversion/values.hpp"

#include <pybind11/stl.h>

#include <algorithm>
#include <limits>
#include <optional>
#include <string>
#include <unordered_map>

namespace kagg::pyconv {

UnitAction ParseUnitAction(py::handle h) {
  UnitAction ua{UnitOp::kInvalid, -1, 1};
  if (!py::isinstance<py::list>(h)) return ua;
  const auto lst = py::reinterpret_borrow<py::list>(h);
  if (lst.size() == 0) return ua;
  std::string op_name;
  if (!ToString(lst[0], &op_name)) return ua;
  const auto& ops = UnitOpMap();
  const auto it = ops.find(op_name);
  if (it == ops.end()) return ua;
  const UnitOp op = it->second;

  switch (op) {
    case UnitOp::kPickup:
    case UnitOp::kPlace: {
      if (lst.size() < 2) return ua;  // official: silent no-op
      std::string item_name;
      // Unknown items are no-ops in the official engine (shed lookup misses /
      // PLACE falls through with zero inventory).
      if (!ToString(lst[1], &item_name)) return ua;
      const int itm = LookupItem(item_name, kNumItems);
      if (itm < 0) return ua;
      int64_t n = 1;
      if (lst.size() >= 3 && !ToInt64(lst[2], &n)) return ua;  // documented deviation
      ua.op = op;
      ua.arg = itm;
      ua.n = n;
      return ua;
    }
    case UnitOp::kPlant: {
      if (lst.size() < 2) return ua;
      std::string crop_name;
      if (!ToString(lst[1], &crop_name)) return ua;
      const int crop = LookupItem(crop_name, kNumCrops);
      if (crop < 0) return ua;  // unknown crop: no-op either way
      ua.op = op;
      ua.arg = crop;
      return ua;
    }
    default:
      ua.op = op;
      return ua;
  }
}

// `_parse_order`. Malformed orders keep their queue slot as std::nullopt;
// orders with invalid items are also dropped to nullopt, which is
// side-effect-equivalent to the official quote-time abort.
std::optional<MarketOrder> ParseOrder(py::handle h) {
  if (!py::isinstance<py::list>(h)) return std::nullopt;
  const auto lst = py::reinterpret_borrow<py::list>(h);
  if (lst.size() == 0) return std::nullopt;
  std::string op;
  if (!ToString(lst[0], &op)) return std::nullopt;
  if (op == "HIRE") return MarketOrder{OrderKind::kHire, 0, 0};
  if (op == "BUY_LAND") return MarketOrder{OrderKind::kBuyLand, 0, 0};

  OrderKind kind;
  if (op == "BUY_SEED") {
    kind = OrderKind::kBuySeed;
  } else if (op == "BUY_PRODUCT") {
    kind = OrderKind::kBuyProduct;
  } else if (op == "BUY_ANIMAL") {
    kind = OrderKind::kBuyAnimal;
  } else if (op == "SELL") {
    kind = OrderKind::kSell;
  } else {
    return std::nullopt;
  }
  if (lst.size() < 3) return std::nullopt;
  int64_t n = 0;
  if (!ToInt64(lst[2], &n)) return std::nullopt;
  if (n <= 0) return std::nullopt;
  std::string item_name;
  if (!ToString(lst[1], &item_name)) return std::nullopt;
  int itm;
  switch (kind) {
    case OrderKind::kBuySeed:
      itm = LookupItem(item_name, kNumCrops);
      break;
    case OrderKind::kBuyAnimal:
      itm = LookupAnimal(item_name);
      break;
    default:  // SELL / BUY_PRODUCT quote against products only
      itm = LookupItem(item_name, kNumProducts);
      break;
  }
  if (itm < 0) return std::nullopt;
  return MarketOrder{kind, itm, n};
}

PlayerAction ParsePlayerAction(py::handle action, int max_orders) {
  PlayerAction pa;
  pa.farmer = UnitAction{UnitOp::kPass, -1, 1};
  if (!py::isinstance<py::dict>(action)) return pa;
  const auto d = py::reinterpret_borrow<py::dict>(action);
  if (d.contains("farmer")) pa.farmer = ParseUnitAction(d["farmer"]);
  if (d.contains("hands") && py::isinstance<py::list>(d["hands"])) {
    for (py::handle h : py::reinterpret_borrow<py::list>(d["hands"])) {
      pa.hands.push_back(ParseUnitAction(h));
    }
  }
  if (d.contains("market") && py::isinstance<py::list>(d["market"])) {
    const auto m = py::reinterpret_borrow<py::list>(d["market"]);
    const size_t limit = std::min<size_t>(m.size(), static_cast<size_t>(max_orders));
    for (size_t i = 0; i < limit; ++i) pa.market.push_back(ParseOrder(m[i]));
  }
  return pa;
}

namespace {

const char* UnitOpName(UnitOp op) {
  switch (op) {
    case UnitOp::kNorth: return "NORTH";
    case UnitOp::kSouth: return "SOUTH";
    case UnitOp::kEast: return "EAST";
    case UnitOp::kWest: return "WEST";
    case UnitOp::kPickup: return "PICKUP";
    case UnitOp::kDrop: return "DROP";
    case UnitOp::kPlace: return "PLACE";
    case UnitOp::kPlant: return "PLANT";
    case UnitOp::kWater: return "WATER";
    case UnitOp::kHarvest: return "HARVEST";
    case UnitOp::kFertilize: return "FERTILIZE";
    case UnitOp::kDig: return "DIG";
    case UnitOp::kBuildCoop: return "BUILD_COOP";
    case UnitOp::kBuildPasture: return "BUILD_PASTURE";
    case UnitOp::kFeed: return "FEED";
    case UnitOp::kCollectFertilizer: return "COLLECT_FERTILIZER";
    case UnitOp::kCare: return "CARE";
    default: return "PASS";
  }
}

}  // namespace

py::list UnitActionToPy(const UnitAction& ua) {
  py::list out;
  out.append(UnitOpName(ua.op));
  if (ua.op == UnitOp::kPickup || ua.op == UnitOp::kPlace) {
    out.append(kItemNames[ua.arg]);
    out.append(ua.n);
  } else if (ua.op == UnitOp::kPlant) {
    out.append(kItemNames[ua.arg]);
  }
  return out;
}

py::list MarketOrderToPy(const MarketOrder& market_order) {
  py::list order;
  switch (market_order.kind) {
    case OrderKind::kHire:
      order.append("HIRE");
      break;
    case OrderKind::kBuyLand:
      order.append("BUY_LAND");
      break;
    case OrderKind::kBuySeed:
      order.append("BUY_SEED");
      order.append(kItemNames[market_order.item]);
      order.append(market_order.remaining);
      break;
    case OrderKind::kBuyProduct:
      order.append("BUY_PRODUCT");
      order.append(kItemNames[market_order.item]);
      order.append(market_order.remaining);
      break;
    case OrderKind::kBuyAnimal:
      order.append("BUY_ANIMAL");
      order.append(kItemNames[item::kGoose + market_order.item]);
      order.append(market_order.remaining);
      break;
    case OrderKind::kSell:
      order.append("SELL");
      order.append(kItemNames[market_order.item]);
      order.append(market_order.remaining);
      break;
  }
  return order;
}

py::dict PlayerActionToPy(const PlayerAction& action) {
  py::dict d;
  d["farmer"] = UnitActionToPy(action.farmer);
  py::list hands;
  for (const UnitAction& h : action.hands) hands.append(UnitActionToPy(h));
  d["hands"] = hands;
  py::list market;
  for (const auto& slot : action.market) {
    market.append(slot.has_value() ? MarketOrderToPy(*slot) : py::list());
  }
  d["market"] = market;
  return d;
}


}  // namespace kagg::pyconv
