#include "action_codec.hpp"

#include <algorithm>
#include <optional>
#include <stdexcept>

namespace kagg::policy {
namespace {

constexpr int kPickupFirst = 5;
constexpr int kDrop = 17;
constexpr int kPlaceFirst = 18;
constexpr int kPlantFirst = 30;

UnitAction Pass() { return UnitAction{UnitOp::kPass, -1, 1}; }

std::optional<MarketOrder> DecodeMarketTokenImpl(int token, int64_t quantity) {
  const int market = token - kUnitActionTokens;
  if (market == 1) return std::nullopt;
  if (market >= 2 && market <= 10) {
    return MarketOrder{OrderKind::kSell, market - 2, quantity};
  }
  if (market >= 11 && market <= 15) {
    return MarketOrder{OrderKind::kBuySeed, market - 11, quantity};
  }
  if (market == 16) {
    return MarketOrder{OrderKind::kBuyProduct, item::kWheat, quantity};
  }
  if (market == 17) {
    return MarketOrder{OrderKind::kBuyProduct, item::kFertilizer, quantity};
  }
  if (market >= 18 && market <= 20) {
    return MarketOrder{OrderKind::kBuyAnimal, market - 18, quantity};
  }
  if (market == 21) return MarketOrder{OrderKind::kHire, 0, 0};
  if (market == 22) return MarketOrder{OrderKind::kBuyLand, 0, 0};
  throw std::invalid_argument("invalid market action token");
}

int EncodeUnitToken(const UnitAction& action) {
  switch (action.op) {
    case UnitOp::kNorth:
      return 1;
    case UnitOp::kSouth:
      return 2;
    case UnitOp::kEast:
      return 3;
    case UnitOp::kWest:
      return 4;
    case UnitOp::kPickup:
      return action.arg >= 0 && action.arg < kNumItems ? 5 + action.arg : 0;
    case UnitOp::kDrop:
      return 17;
    case UnitOp::kPlace:
      return action.arg >= 0 && action.arg < kNumItems ? 18 + action.arg : 0;
    case UnitOp::kPlant:
      return action.arg >= 0 && action.arg < kNumCrops ? 30 + action.arg : 0;
    case UnitOp::kWater:
      return 35;
    case UnitOp::kHarvest:
      return 36;
    case UnitOp::kFertilize:
      return 37;
    case UnitOp::kDig:
      return 38;
    case UnitOp::kBuildCoop:
      return 39;
    case UnitOp::kBuildPasture:
      return 40;
    case UnitOp::kFeed:
      return 41;
    case UnitOp::kCollectFertilizer:
      return 42;
    case UnitOp::kCare:
      return 43;
    case UnitOp::kPass:
    case UnitOp::kInvalid:
      return 0;
  }
  return 0;
}

int EncodeMarketToken(const std::optional<MarketOrder>& order) {
  if (!order) return kUnitActionTokens + 1;
  switch (order->kind) {
    case OrderKind::kSell:
      return order->item >= 0 && order->item < kNumProducts
                 ? kUnitActionTokens + 2 + order->item
                 : kUnitActionTokens + 1;
    case OrderKind::kBuySeed:
      return order->item >= 0 && order->item < kNumCrops
                 ? kUnitActionTokens + 11 + order->item
                 : kUnitActionTokens + 1;
    case OrderKind::kBuyProduct:
      if (order->item == item::kWheat) return kUnitActionTokens + 16;
      if (order->item == item::kFertilizer) return kUnitActionTokens + 17;
      return kUnitActionTokens + 1;
    case OrderKind::kBuyAnimal:
      return order->item >= 0 && order->item < kNumAnimals
                 ? kUnitActionTokens + 18 + order->item
                 : kUnitActionTokens + 1;
    case OrderKind::kHire:
      return kUnitActionTokens + 21;
    case OrderKind::kBuyLand:
      return kUnitActionTokens + 22;
  }
  return kUnitActionTokens + 1;
}

void AddItemKeys(std::vector<std::string>* keys, const char* prefix) {
  for (const char* item_name : kItemNames) {
    keys->push_back(std::string(prefix) + ":" + item_name);
  }
}

}  // namespace

bool IsUnitToken(int token) { return token >= 0 && token < kUnitActionTokens; }

bool IsMarketToken(int token) {
  return token >= kUnitActionTokens && token < kActionTokens;
}

bool TokenHasQuantity(int token) {
  if (token >= kPickupFirst && token < kDrop) return true;
  if (token >= kPlaceFirst && token < kPlantFirst) return true;
  const int market = token - kUnitActionTokens;
  return market >= 2 && market <= 20;
}

UnitAction DecodeUnitToken(int token, int64_t quantity) {
  switch (token) {
    case 0:
      return Pass();
    case 1:
      return UnitAction{UnitOp::kNorth, -1, 1};
    case 2:
      return UnitAction{UnitOp::kSouth, -1, 1};
    case 3:
      return UnitAction{UnitOp::kEast, -1, 1};
    case 4:
      return UnitAction{UnitOp::kWest, -1, 1};
    default:
      break;
  }
  if (token >= kPickupFirst && token < kDrop) {
    return UnitAction{UnitOp::kPickup, token - kPickupFirst, quantity};
  }
  if (token == kDrop) return UnitAction{UnitOp::kDrop, -1, 1};
  if (token >= kPlaceFirst && token < kPlantFirst) {
    return UnitAction{UnitOp::kPlace, token - kPlaceFirst, quantity};
  }
  if (token >= kPlantFirst && token < kPlantFirst + kNumCrops) {
    return UnitAction{UnitOp::kPlant, token - kPlantFirst, 1};
  }
  switch (token) {
    case 35:
      return UnitAction{UnitOp::kWater, -1, 1};
    case 36:
      return UnitAction{UnitOp::kHarvest, -1, 1};
    case 37:
      return UnitAction{UnitOp::kFertilize, -1, 1};
    case 38:
      return UnitAction{UnitOp::kDig, -1, 1};
    case 39:
      return UnitAction{UnitOp::kBuildCoop, -1, 1};
    case 40:
      return UnitAction{UnitOp::kBuildPasture, -1, 1};
    case 41:
      return UnitAction{UnitOp::kFeed, -1, 1};
    case 42:
      return UnitAction{UnitOp::kCollectFertilizer, -1, 1};
    case 43:
      return UnitAction{UnitOp::kCare, -1, 1};
    default:
      return UnitAction{UnitOp::kInvalid, -1, 1};
  }
}

std::optional<MarketOrder> DecodeMarketToken(int token, int64_t quantity) {
  if (!IsMarketToken(token) || token == kMarketStopToken) return std::nullopt;
  return DecodeMarketTokenImpl(token, quantity);
}

PlayerAction DecodePlayerAction(const int64_t* tokens, const int64_t* quantities,
                                int decision_count, int unit_count,
                                int max_market_orders) {
  if (decision_count < 0 || unit_count < 1 || max_market_orders < 1) {
    throw std::invalid_argument("invalid numeric action shape");
  }
  PlayerAction action;
  action.farmer = Pass();
  action.hands.assign(static_cast<size_t>(unit_count - 1), Pass());
  const int unit_stop = std::min(decision_count, unit_count);
  for (int index = 0; index < unit_stop; ++index) {
    const UnitAction decoded = DecodeUnitToken(tokens[index], quantities[index]);
    if (index == 0) {
      action.farmer = decoded;
    } else {
      action.hands[index - 1] = decoded;
    }
  }
  for (int index = unit_count;
       index < decision_count &&
       static_cast<int>(action.market.size()) < max_market_orders;
       ++index) {
    const int token = static_cast<int>(tokens[index]);
    if (token == kMarketStopToken) break;
    if (!IsMarketToken(token)) {
      action.market.push_back(std::nullopt);
      continue;
    }
    action.market.push_back(DecodeMarketTokenImpl(token, quantities[index]));
  }
  return action;
}

int EncodePlayerAction(const PlayerAction& action, int unit_count,
                       int64_t* tokens, int64_t* quantities, int capacity) {
  if (unit_count < 1 || tokens == nullptr || quantities == nullptr ||
      capacity < unit_count ||
      static_cast<size_t>(capacity - unit_count) < action.market.size()) {
    throw std::invalid_argument("numeric action output buffer is too small");
  }
  const auto write_unit = [&](int index, const UnitAction& unit) {
    tokens[index] = EncodeUnitToken(unit);
    quantities[index] = TokenHasQuantity(tokens[index]) ? unit.n : 0;
  };
  write_unit(0, action.farmer);
  for (int index = 1; index < unit_count; ++index) {
    write_unit(index,
               index - 1 < static_cast<int>(action.hands.size())
                   ? action.hands[index - 1]
                   : Pass());
  }
  int decision_count = unit_count;
  for (const std::optional<MarketOrder>& order : action.market) {
    const int token = EncodeMarketToken(order);
    tokens[decision_count] = token;
    quantities[decision_count] =
        order && TokenHasQuantity(token) ? order->remaining : 0;
    ++decision_count;
  }
  return decision_count;
}

std::vector<std::string> ActionTokenKeys() {
  std::vector<std::string> keys = {
      "UNIT:PASS", "UNIT:NORTH", "UNIT:SOUTH", "UNIT:EAST", "UNIT:WEST"};
  AddItemKeys(&keys, "UNIT:PICKUP");
  keys.push_back("UNIT:DROP");
  AddItemKeys(&keys, "UNIT:PLACE");
  for (int crop = 0; crop < kNumCrops; ++crop) {
    keys.push_back(std::string("UNIT:PLANT:") + kItemNames[crop]);
  }
  const std::array<const char*, 9> unit_tail = {
      "UNIT:WATER",       "UNIT:HARVEST", "UNIT:FERTILIZE",
      "UNIT:DIG",         "UNIT:BUILD_COOP", "UNIT:BUILD_PASTURE",
      "UNIT:FEED",        "UNIT:COLLECT_FERTILIZER", "UNIT:CARE"};
  keys.insert(keys.end(), unit_tail.begin(), unit_tail.end());

  keys.push_back("MARKET:STOP");
  keys.push_back("MARKET:SKIP_SLOT");
  for (int product = 0; product < kNumProducts; ++product) {
    keys.push_back(std::string("MARKET:SELL:") + kItemNames[product]);
  }
  for (int crop = 0; crop < kNumCrops; ++crop) {
    keys.push_back(std::string("MARKET:BUY_SEED:") + kItemNames[crop]);
  }
  keys.push_back("MARKET:BUY_PRODUCT:WHEAT");
  keys.push_back("MARKET:BUY_PRODUCT:FERTILIZER");
  for (int animal = 0; animal < kNumAnimals; ++animal) {
    keys.push_back(std::string("MARKET:BUY_ANIMAL:") +
                   kItemNames[item::kGoose + animal]);
  }
  keys.push_back("MARKET:HIRE");
  keys.push_back("MARKET:BUY_LAND");
  if (static_cast<int>(keys.size()) != kActionTokens) {
    throw std::logic_error("numeric action vocabulary has the wrong size");
  }
  return keys;
}

}  // namespace kagg::policy
