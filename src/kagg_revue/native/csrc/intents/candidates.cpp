#include "intents/session.hpp"

#include <algorithm>
#include <array>
#include <cstdint>
#include <limits>
#include <stdexcept>
#include <tuple>

namespace kagg::intents {
namespace {

constexpr uint64_t kFnvOffset = 1469598103934665603ULL;
constexpr uint64_t kFnvPrime = 1099511628211ULL;

void HashWord(uint64_t value, uint64_t* hash) {
  for (int byte = 0; byte < 8; ++byte) {
    *hash ^= (value >> (byte * 8)) & 0xffULL;
    *hash *= kFnvPrime;
  }
}

Candidate MakeCandidate(ChoiceKind kind) {
  Candidate candidate;
  candidate.kind = kind;
  candidate.fields[0] = static_cast<int64_t>(kind);
  candidate.fields[1] = -1;
  return candidate;
}

int64_t Carried(const PrivateState& priv, int item_index) {
  int64_t result = 0;
  for (const Inventory& inventory : priv.inventories) {
    result += inventory.Get(item_index);
  }
  return result;
}

int64_t Owned(const PrivateState& priv, int item_index) {
  return priv.shed[item_index] + Carried(priv, item_index);
}

bool SameContract(const AssetContract& left, const AssetContract& right) {
  return left.active == right.active && left.kind == right.kind &&
         left.item == right.item && left.maintenance == right.maintenance &&
         left.product_collection == right.product_collection &&
         left.fertilizer_collection == right.fertilizer_collection &&
         left.priority == right.priority;
}

bool WorkApplies(WorkKind kind, const Tile& tile) {
  switch (kind) {
    case WorkKind::kHarvest:
      return tile.kind == TileKind::kPlant ||
             (tile.kind == TileKind::kStructure && tile.has_animal);
    case WorkKind::kFertilize:
    case WorkKind::kWaterOnce:
      return tile.kind == TileKind::kPlant;
    case WorkKind::kCareOnce:
    case WorkKind::kCollectProduct:
    case WorkKind::kCollectFertilizer:
    case WorkKind::kFeedOnce:
      return tile.kind == TileKind::kStructure && tile.has_animal;
    case WorkKind::kClear:
      return tile.kind == TileKind::kWeed || tile.kind == TileKind::kPlant ||
             (tile.kind == TileKind::kStructure && !tile.has_animal);
    case WorkKind::kStore:
    case WorkKind::kFetch:
    case WorkKind::kDirectivePosition:
    case WorkKind::kDirectiveWait:
    case WorkKind::kDirectivePickup:
    case WorkKind::kDirectiveDrop:
    case WorkKind::kDirectivePlace:
    case WorkKind::kDirectivePlant:
    case WorkKind::kDirectiveWater:
    case WorkKind::kDirectiveHarvest:
    case WorkKind::kDirectiveFertilize:
    case WorkKind::kDirectiveDig:
    case WorkKind::kDirectiveBuildCoop:
    case WorkKind::kDirectiveBuildPasture:
    case WorkKind::kDirectiveFeed:
    case WorkKind::kDirectiveCollectFertilizer:
    case WorkKind::kDirectiveCare:
      return false;
  }
  return false;
}

bool DirectiveNeedsItem(DirectiveOperation operation) {
  return operation == DirectiveOperation::kPickup ||
         operation == DirectiveOperation::kPlace ||
         operation == DirectiveOperation::kPlant;
}

bool DirectiveNeedsQuantity(DirectiveOperation operation) {
  return operation == DirectiveOperation::kPickup ||
         operation == DirectiveOperation::kPlace;
}

OrderKind OrderForChoice(ChoiceKind kind) {
  switch (kind) {
    case ChoiceKind::kMarketSell: return OrderKind::kSell;
    case ChoiceKind::kMarketBuySeed: return OrderKind::kBuySeed;
    case ChoiceKind::kMarketBuyProduct: return OrderKind::kBuyProduct;
    case ChoiceKind::kMarketBuyAnimal: return OrderKind::kBuyAnimal;
    case ChoiceKind::kMarketHire: return OrderKind::kHire;
    case ChoiceKind::kMarketBuyLand: return OrderKind::kBuyLand;
    default: return OrderKind::kSell;
  }
}

}  // namespace

void Session::AddCandidate(const Engine& engine, int player,
                           Candidate candidate) {
  const int board_size = config_.board_size;
  const int target = static_cast<int>(candidate.fields[1]);
  const int item_index = static_cast<int>(candidate.fields[2]) - 1;
  const int unit = static_cast<int>(candidate.fields[8]) - 1;
  const int64_t quantity = candidate.fields[7];
  const bool market =
      (candidate.kind >= ChoiceKind::kMarketSell &&
       candidate.kind <= ChoiceKind::kSelectMarketQuantity) ||
      candidate.kind == ChoiceKind::kMarketSkipSlot;
  const bool unit_bound = candidate.kind >= ChoiceKind::kBeginFetch;
  const bool ledger = candidate.kind != ChoiceKind::kCommit && !market;
  candidate.features[0] = static_cast<float>(candidate.kind) / 40.0F;
  candidate.features[1] = static_cast<float>(phase_) /
                          static_cast<float>(Phase::kDone);
  candidate.features[2] = ledger ? 1.0F : 0.0F;
  candidate.features[3] = market ? 1.0F : 0.0F;
  if (unit_bound && unit >= 0 &&
      unit < static_cast<int>(engine.priv(player).inventories.size())) {
    const Farm& farm = engine.farm(player);
    const int x = unit == 0 ? farm.farmer_x : farm.hands[unit - 1].first;
    const int y = unit == 0 ? farm.farmer_y : farm.hands[unit - 1].second;
    candidate.features[4] = static_cast<float>(x) /
                            std::max(1, board_size - 1);
    candidate.features[5] = static_cast<float>(y) /
                            std::max(1, board_size - 1);
  } else if (target >= 0 && target < board_size * board_size) {
    candidate.features[4] = static_cast<float>(target % board_size) /
                            std::max(1, board_size - 1);
    candidate.features[5] = static_cast<float>(target / board_size) /
                            std::max(1, board_size - 1);
    candidate.features[10] = draft_assets_[target].active ? 1.0F : 0.0F;
  }
  candidate.features[6] = static_cast<float>(quantity) /
                          std::max<int64_t>(1, config_.shed_capacity);
  if (item_index >= 0 && item_index < kNumItems) {
    candidate.features[7] = static_cast<float>(item_index + 1) / kNumItems;
    const PrivateState& priv = engine.priv(player);
    candidate.features[9] = static_cast<float>(Owned(priv, item_index)) /
                            std::max<int64_t>(1, config_.shed_capacity);
    if (item_index < kNumProducts) {
      const double base = engine.config().market_params[item_index].base;
      candidate.features[8] = static_cast<float>(
          engine.market().prices[item_index] / std::max(1.0, base));
    }
  }
  candidate.features[11] = static_cast<float>(market_prefix_.size()) /
                           std::max(1, config_.max_market_orders);

  uint64_t hash = kFnvOffset;
  HashWord(kSpecVersion, &hash);
  HashWord(static_cast<uint64_t>(phase_), &hash);
  HashWord(static_cast<uint64_t>(last_ledger_key_), &hash);
  HashWord(market_phase_ ? 1 : 0, &hash);
  for (const std::optional<MarketOrder>& order : market_prefix_) {
    if (order) {
      HashWord(static_cast<uint64_t>(order->kind), &hash);
      HashWord(static_cast<uint64_t>(order->item), &hash);
      HashWord(static_cast<uint64_t>(order->remaining), &hash);
    } else {
      HashWord(kMarketSkipKind, &hash);
      HashWord(static_cast<uint64_t>(-1), &hash);
      HashWord(0, &hash);
    }
  }
  for (int64_t field : candidate.fields) {
    HashWord(static_cast<uint64_t>(field), &hash);
  }
  candidate.canonical_id = hash == 0 ? 1 : hash;
  candidates_.push_back(std::move(candidate));
}

void Session::GenerateRootCandidates(const Engine& engine, int player) {
  AddCandidate(engine, player, MakeCandidate(ChoiceKind::kCommit));
  if (!market_phase_) {
    const int cells = config_.board_size * config_.board_size;
    if (AssetKey(cells - 1) > last_ledger_key_) {
      AddCandidate(engine, player, MakeCandidate(ChoiceKind::kBeginAsset));
    }
    if (std::any_of(draft_assets_.begin(), draft_assets_.end(),
                    [&](const AssetContract& contract) {
                      const int target = static_cast<int>(&contract - draft_assets_.data());
                      return contract.active && AssetKey(target) > last_ledger_key_;
                    })) {
      AddCandidate(engine, player,
                   MakeCandidate(ChoiceKind::kBeginCancelAsset));
    }
    const Farm& farm = engine.farm(player);
    bool can_add_work = false;
    for (int target = 0; target < cells && !can_add_work; ++target) {
      for (int kind = 0; kind < static_cast<int>(WorkKind::kStore); ++kind) {
        const WorkKind work_kind = static_cast<WorkKind>(kind);
        if (WorkKey(target, work_kind) > last_ledger_key_ &&
            WorkApplies(work_kind, farm.tiles[target]) &&
            !ServiceCovers(target, work_kind, farm.tiles[target])) {
          can_add_work = true;
          break;
        }
      }
    }
    if (can_add_work) {
      AddCandidate(engine, player, MakeCandidate(ChoiceKind::kBeginWork));
    }
    if (std::any_of(draft_work_.begin(), draft_work_.end(),
                    [&](const WorkOrder& order) {
                      const int64_t key = order.kind == WorkKind::kStore
                                              ? StoreKey(order.item)
                                              : WorkKey(order.target, order.kind);
                      return key > last_ledger_key_;
                    })) {
      AddCandidate(engine, player,
                   MakeCandidate(ChoiceKind::kBeginCancelWork));
    }
    if (PositionKey(PositionRole::kAnyHand) > last_ledger_key_) {
      AddCandidate(engine, player, MakeCandidate(ChoiceKind::kBeginPosition));
    }
    if (std::any_of(draft_positions_.begin(), draft_positions_.end(),
                    [&](const PositionIntent& position) {
                      return position.active &&
                             PositionKey(position.role) > last_ledger_key_;
                    })) {
      AddCandidate(engine, player,
                   MakeCandidate(ChoiceKind::kBeginCancelPosition));
    }
    const PrivateState& priv = engine.priv(player);
    bool can_store = false;
    for (int item_index = 0; item_index < kNumItems; ++item_index) {
      if (Carried(priv, item_index) > 0 &&
          StoreKey(item_index) > last_ledger_key_) {
        can_store = true;
        break;
      }
    }
    if (can_store) {
      AddCandidate(engine, player, MakeCandidate(ChoiceKind::kBeginStore));
    }
    bool can_fetch = false;
    for (int unit = 0;
         unit < static_cast<int>(priv.inventories.size()) && !can_fetch;
         ++unit) {
      if (FetchKey(unit) <= last_ledger_key_) continue;
      for (int item_index = 0; item_index < kNumItems; ++item_index) {
        if (priv.shed[item_index] > 0 &&
            priv.inventories[unit].Get(item_index) < config_.shed_capacity) {
          can_fetch = true;
          break;
        }
      }
    }
    if (can_fetch) {
      AddCandidate(engine, player, MakeCandidate(ChoiceKind::kBeginFetch));
    }
    if (std::any_of(draft_fetches_.begin(), draft_fetches_.end(),
                    [&](const FetchIntent& fetch) {
                      return fetch.active &&
                             FetchKey(fetch.unit) > last_ledger_key_;
                    })) {
      AddCandidate(engine, player,
                   MakeCandidate(ChoiceKind::kBeginCancelFetch));
    }
    bool can_direct = false;
    for (int unit = 0;
         unit < static_cast<int>(priv.inventories.size()); ++unit) {
      if (DirectiveKey(unit) > last_ledger_key_) {
        can_direct = true;
        break;
      }
    }
    if (can_direct) {
      AddCandidate(engine, player,
                   MakeCandidate(ChoiceKind::kBeginDirective));
    }
    if (std::any_of(draft_directives_.begin(), draft_directives_.end(),
                    [&](const UnitDirective& directive) {
                      return directive.active &&
                             DirectiveKey(directive.unit) > last_ledger_key_;
                    })) {
      AddCandidate(engine, player,
                   MakeCandidate(ChoiceKind::kBeginCancelDirective));
    }
  }
  GenerateMarketCandidates(engine, player);
}

void Session::GenerateAssetProfiles(const Engine& engine, int player) {
  const AssetContract& current = draft_assets_[pending_target_];
  for (int crop = 0; crop < kNumCrops; ++crop) {
    for (Maintenance maintenance : {Maintenance::kNone, Maintenance::kSurvive,
                                    Maintenance::kYield}) {
      for (int priority = 0; priority < 3; ++priority) {
        AssetContract proposed;
        proposed.active = true;
        proposed.kind = AssetKind::kCrop;
        proposed.item = crop;
        proposed.maintenance = maintenance;
        proposed.priority = static_cast<Priority>(priority);
        if (SameContract(current, proposed)) continue;
        Candidate candidate = MakeCandidate(ChoiceKind::kSetAsset);
        candidate.fields = {
            static_cast<int64_t>(candidate.kind), pending_target_, crop + 1,
            static_cast<int64_t>(maintenance),
            static_cast<int64_t>(ProductCollection::kManual),
            static_cast<int64_t>(FertilizerCollection::kManual), priority, 0};
        AddCandidate(engine, player, std::move(candidate));
      }
    }
  }
  for (int animal = 0; animal < kNumAnimals; ++animal) {
    for (Maintenance maintenance : {Maintenance::kNone,
                                    Maintenance::kSurvive,
                                    Maintenance::kCared}) {
      for (int product = 0; product < 2; ++product) {
        for (int fertilizer = 0; fertilizer < 2; ++fertilizer) {
          for (int priority = 0; priority < 3; ++priority) {
            AssetContract proposed;
            proposed.active = true;
            proposed.kind = AssetKind::kAnimal;
            proposed.item = item::kGoose + animal;
            proposed.maintenance = maintenance;
            proposed.product_collection =
                static_cast<ProductCollection>(product);
            proposed.fertilizer_collection =
                static_cast<FertilizerCollection>(fertilizer);
            proposed.priority = static_cast<Priority>(priority);
            if (SameContract(current, proposed)) continue;
            Candidate candidate = MakeCandidate(ChoiceKind::kSetAsset);
            candidate.fields = {
                static_cast<int64_t>(candidate.kind), pending_target_,
                item::kGoose + animal + 1, static_cast<int64_t>(maintenance),
                product, fertilizer, priority, 0};
            AddCandidate(engine, player, std::move(candidate));
          }
        }
      }
    }
  }
}

void Session::GenerateWorkProfiles(const Engine& engine, int player) {
  const Tile& tile = engine.farm(player).tiles[pending_target_];
  pending_work_tile_kind_ = tile.kind;
  pending_work_item_ = tile.kind == TileKind::kPlant
                           ? tile.crop
                           : (tile.kind == TileKind::kStructure && tile.has_animal
                                  ? item::kGoose + tile.animal
                                  : static_cast<int>(tile.structure));
  pending_work_generation_ =
      tile.kind == TileKind::kPlant
          ? tile.planted_day
          : (tile.kind == TileKind::kStructure && tile.has_animal
                 ? tile.placed_day
                 : -1);
  for (int kind = 0; kind < static_cast<int>(WorkKind::kStore); ++kind) {
    const WorkKind work_kind = static_cast<WorkKind>(kind);
    if (!WorkApplies(work_kind, tile) ||
        ServiceCovers(pending_target_, work_kind, tile) ||
        WorkKey(pending_target_, work_kind) <= last_ledger_key_) {
      continue;
    }
    for (int priority = 0; priority < 3; ++priority) {
      const auto existing = std::find_if(
          draft_work_.begin(), draft_work_.end(), [&](const WorkOrder& order) {
            return order.target == pending_target_ && order.kind == work_kind;
          });
      if (existing != draft_work_.end() &&
          existing->priority == static_cast<Priority>(priority)) {
        continue;
      }
      Candidate candidate = MakeCandidate(ChoiceKind::kAddWork);
      candidate.fields[1] = pending_target_;
      candidate.fields[2] = kind + 1;
      candidate.fields[6] = priority;
      AddCandidate(engine, player, std::move(candidate));
    }
  }
}

int64_t Session::MarketQuantityUpper(const Engine& engine, int player,
                                     OrderKind kind, int item_index) const {
  const int cells = config_.board_size * config_.board_size;
  if (kind == OrderKind::kBuySeed || kind == OrderKind::kBuyAnimal) {
    return cells;
  }
  if (kind == OrderKind::kBuyProduct) {
    return std::max<int64_t>(1, config_.shed_capacity);
  }
  if (kind != OrderKind::kSell || item_index < 0 ||
      item_index >= kNumProducts) {
    return 0;
  }
  int64_t available = Owned(engine.priv(player), item_index);
  for (const std::optional<MarketOrder>& order : market_prefix_) {
    if (!order || order->item != item_index) continue;
    if (order->kind == OrderKind::kSell) available -= order->remaining;
    if (order->kind == OrderKind::kBuyProduct) available += order->remaining;
  }
  return std::max<int64_t>(0, available);
}

void Session::GenerateMarketCandidates(const Engine& engine, int player) {
  if (static_cast<int>(market_prefix_.size()) >= config_.max_market_orders) {
    return;
  }
  for (int product = 0; product < kNumProducts; ++product) {
    const int64_t upper =
        MarketQuantityUpper(engine, player, OrderKind::kSell, product);
    if (upper <= 0) continue;
    Candidate candidate = MakeCandidate(ChoiceKind::kMarketSell);
    candidate.fields[2] = product + 1;
    candidate.fields[7] = upper;
    AddCandidate(engine, player, std::move(candidate));
  }
  for (int crop = 0; crop < kNumCrops; ++crop) {
    Candidate candidate = MakeCandidate(ChoiceKind::kMarketBuySeed);
    candidate.fields[2] = crop + 1;
    candidate.fields[7] =
        MarketQuantityUpper(engine, player, OrderKind::kBuySeed, crop);
    AddCandidate(engine, player, std::move(candidate));
  }
  for (int product : {item::kWheat, item::kFertilizer}) {
    Candidate candidate = MakeCandidate(ChoiceKind::kMarketBuyProduct);
    candidate.fields[2] = product + 1;
    candidate.fields[7] =
        MarketQuantityUpper(engine, player, OrderKind::kBuyProduct, product);
    AddCandidate(engine, player, std::move(candidate));
  }
  for (int animal = 0; animal < kNumAnimals; ++animal) {
    Candidate candidate = MakeCandidate(ChoiceKind::kMarketBuyAnimal);
    candidate.fields[2] = animal + 1;
    candidate.fields[7] =
        MarketQuantityUpper(engine, player, OrderKind::kBuyAnimal, animal);
    AddCandidate(engine, player, std::move(candidate));
  }
  AddCandidate(engine, player, MakeCandidate(ChoiceKind::kMarketHire));
  int land_orders = 0;
  for (const std::optional<MarketOrder>& order : market_prefix_) {
    if (order && order->kind == OrderKind::kBuyLand) ++land_orders;
  }
  if (engine.farm(player).extra_unlocked + land_orders < 3) {
    AddCandidate(engine, player, MakeCandidate(ChoiceKind::kMarketBuyLand));
  }
  AddCandidate(engine, player, MakeCandidate(ChoiceKind::kMarketSkipSlot));
}

void Session::GenerateCandidates(const Engine& engine, int player) {
  if (!candidates_.empty() || phase_ == Phase::kDone) return;
  const int cells = config_.board_size * config_.board_size;
  switch (phase_) {
    case Phase::kRoot:
      GenerateRootCandidates(engine, player);
      break;
    case Phase::kAssetTarget:
      for (int target = 0; target < cells; ++target) {
        if (AssetKey(target) <= last_ledger_key_) continue;
        Candidate candidate = MakeCandidate(ChoiceKind::kSelectTarget);
        candidate.fields[1] = target;
        AddCandidate(engine, player, std::move(candidate));
      }
      break;
    case Phase::kAssetProfile:
      GenerateAssetProfiles(engine, player);
      break;
    case Phase::kCancelAsset:
      for (int target = 0; target < cells; ++target) {
        if (!draft_assets_[target].active ||
            AssetKey(target) <= last_ledger_key_) {
          continue;
        }
        Candidate candidate = MakeCandidate(ChoiceKind::kCancelAsset);
        candidate.fields[1] = target;
        AddCandidate(engine, player, std::move(candidate));
      }
      break;
    case Phase::kWorkTarget:
      for (int target = 0; target < cells; ++target) {
        bool available = false;
        for (int kind = 0; kind < static_cast<int>(WorkKind::kStore); ++kind) {
          const WorkKind work_kind = static_cast<WorkKind>(kind);
          if (WorkKey(target, work_kind) > last_ledger_key_ &&
              WorkApplies(work_kind, engine.farm(player).tiles[target]) &&
              !ServiceCovers(target, work_kind,
                             engine.farm(player).tiles[target])) {
            available = true;
            break;
          }
        }
        if (!available) continue;
        Candidate candidate = MakeCandidate(ChoiceKind::kSelectTarget);
        candidate.fields[1] = target;
        AddCandidate(engine, player, std::move(candidate));
      }
      break;
    case Phase::kWorkProfile:
      GenerateWorkProfiles(engine, player);
      break;
    case Phase::kCancelWork:
      {
      std::vector<const WorkOrder*> orders;
      orders.reserve(draft_work_.size());
      for (const WorkOrder& order : draft_work_) orders.push_back(&order);
      std::stable_sort(orders.begin(), orders.end(), [&](const auto* left,
                                                        const auto* right) {
        const auto key = [&](const WorkOrder* order) {
          return order->kind == WorkKind::kStore
                     ? StoreKey(order->item)
                     : WorkKey(order->target, order->kind);
        };
        return key(left) < key(right);
      });
      for (const WorkOrder* raw_order : orders) {
        const WorkOrder& order = *raw_order;
        const int64_t key = order.kind == WorkKind::kStore
                                ? StoreKey(order.item)
                                : WorkKey(order.target, order.kind);
        if (key <= last_ledger_key_) continue;
        Candidate candidate = MakeCandidate(ChoiceKind::kCancelWork);
        candidate.fields[1] = order.target;
        candidate.fields[2] = static_cast<int64_t>(order.kind) + 1;
        candidate.fields[3] = order.item + 1;
        AddCandidate(engine, player, std::move(candidate));
      }
      }
      break;
    case Phase::kPositionRole:
      for (int role = 0; role < 2; ++role) {
        const PositionRole position_role = static_cast<PositionRole>(role);
        if (PositionKey(position_role) <= last_ledger_key_) continue;
        Candidate candidate = MakeCandidate(ChoiceKind::kSelectRole);
        candidate.fields[2] = role + 1;
        AddCandidate(engine, player, std::move(candidate));
      }
      break;
    case Phase::kPositionTarget:
      for (int target = 0; target < cells; ++target) {
        for (int priority = 0; priority < 3; ++priority) {
          const PositionIntent& current =
              draft_positions_[static_cast<int>(pending_role_)];
          if (current.active && current.target == target &&
              current.priority == static_cast<Priority>(priority)) {
            continue;
          }
          Candidate candidate = MakeCandidate(ChoiceKind::kSetPosition);
          candidate.fields[1] = target;
          candidate.fields[2] = static_cast<int64_t>(pending_role_) + 1;
          candidate.fields[6] = priority;
          AddCandidate(engine, player, std::move(candidate));
        }
      }
      break;
    case Phase::kCancelPosition:
      for (int role = 0; role < 2; ++role) {
        const PositionIntent& current = draft_positions_[role];
        if (!current.active || PositionKey(current.role) <= last_ledger_key_) {
          continue;
        }
        Candidate candidate = MakeCandidate(ChoiceKind::kCancelPosition);
        candidate.fields[2] = role + 1;
        AddCandidate(engine, player, std::move(candidate));
      }
      break;
    case Phase::kStoreItem:
      for (int item_index = 0; item_index < kNumItems; ++item_index) {
        if (Carried(engine.priv(player), item_index) <= 0 ||
            StoreKey(item_index) <= last_ledger_key_) {
          continue;
        }
        Candidate candidate = MakeCandidate(ChoiceKind::kSelectStoreItem);
        candidate.fields[2] = item_index + 1;
        AddCandidate(engine, player, std::move(candidate));
      }
      break;
    case Phase::kStoreQuantity: {
      const int64_t upper = Carried(engine.priv(player), pending_item_);
      for (int64_t quantity = 1; quantity <= upper; ++quantity) {
        Candidate candidate = MakeCandidate(ChoiceKind::kSelectStoreQuantity);
        candidate.fields[2] = pending_item_ + 1;
        candidate.fields[7] = quantity;
        AddCandidate(engine, player, std::move(candidate));
      }
      break;
    }
    case Phase::kStorePriority:
      for (int priority = 0; priority < 3; ++priority) {
        const auto existing = std::find_if(
            draft_work_.begin(), draft_work_.end(), [&](const WorkOrder& order) {
              return order.kind == WorkKind::kStore &&
                     order.item == pending_item_;
            });
        if (existing != draft_work_.end() &&
            existing->quantity == pending_quantity_ &&
            existing->priority == static_cast<Priority>(priority)) {
          continue;
        }
        Candidate candidate = MakeCandidate(ChoiceKind::kAddStore);
        candidate.fields[2] = pending_item_ + 1;
        candidate.fields[6] = priority;
        candidate.fields[7] = pending_quantity_;
        AddCandidate(engine, player, std::move(candidate));
      }
      break;
    case Phase::kMarketQuantity:
      for (int64_t quantity = 1; quantity <= pending_market_.upper; ++quantity) {
        Candidate candidate = MakeCandidate(ChoiceKind::kSelectMarketQuantity);
        candidate.fields[2] = pending_market_.item + 1;
        candidate.fields[7] = quantity;
        AddCandidate(engine, player, std::move(candidate));
      }
      break;
    case Phase::kFetchUnit: {
      const PrivateState& priv = engine.priv(player);
      for (int unit = 0;
           unit < static_cast<int>(priv.inventories.size()); ++unit) {
        bool available = false;
        for (int item_index = 0; item_index < kNumItems; ++item_index) {
          if (priv.shed[item_index] > 0 &&
              priv.inventories[unit].Get(item_index) < config_.shed_capacity) {
            available = true;
            break;
          }
        }
        if (!available || FetchKey(unit) <= last_ledger_key_) continue;
        Candidate candidate = MakeCandidate(ChoiceKind::kSelectFetchUnit);
        candidate.fields[8] = unit + 1;
        AddCandidate(engine, player, std::move(candidate));
      }
      break;
    }
    case Phase::kFetchItem: {
      const PrivateState& priv = engine.priv(player);
      for (int item_index = 0; item_index < kNumItems; ++item_index) {
        const int64_t carried =
            priv.inventories[pending_unit_].Get(item_index);
        if (priv.shed[item_index] <= 0 ||
            carried >= config_.shed_capacity) {
          continue;
        }
        Candidate candidate = MakeCandidate(ChoiceKind::kSelectFetchItem);
        candidate.fields[2] = item_index + 1;
        candidate.fields[8] = pending_unit_ + 1;
        AddCandidate(engine, player, std::move(candidate));
      }
      break;
    }
    case Phase::kFetchQuantity: {
      const PrivateState& priv = engine.priv(player);
      const int64_t carried =
          priv.inventories[pending_unit_].Get(pending_item_);
      const int64_t upper = std::min<int64_t>(
          config_.shed_capacity, carried + priv.shed[pending_item_]);
      for (int64_t quantity = carried + 1; quantity <= upper; ++quantity) {
        Candidate candidate = MakeCandidate(ChoiceKind::kSetFetch);
        candidate.fields[2] = pending_item_ + 1;
        candidate.fields[6] = static_cast<int64_t>(Priority::kHigh);
        candidate.fields[7] = quantity;
        candidate.fields[8] = pending_unit_ + 1;
        AddCandidate(engine, player, std::move(candidate));
      }
      break;
    }
    case Phase::kCancelFetch:
      for (const FetchIntent& fetch : draft_fetches_) {
        if (!fetch.active || FetchKey(fetch.unit) <= last_ledger_key_) {
          continue;
        }
        Candidate candidate = MakeCandidate(ChoiceKind::kCancelFetch);
        candidate.fields[2] = fetch.item + 1;
        candidate.fields[6] = static_cast<int64_t>(Priority::kHigh);
        candidate.fields[7] = fetch.quantity;
        candidate.fields[8] = fetch.unit + 1;
        AddCandidate(engine, player, std::move(candidate));
      }
      break;
    case Phase::kDirectiveUnit:
      for (int unit = 0;
           unit < static_cast<int>(engine.priv(player).inventories.size());
           ++unit) {
        if (DirectiveKey(unit) <= last_ledger_key_) continue;
        Candidate candidate =
            MakeCandidate(ChoiceKind::kSelectDirectiveUnit);
        candidate.fields[8] = unit + 1;
        AddCandidate(engine, player, std::move(candidate));
      }
      break;
    case Phase::kDirectiveOperation:
      for (int operation = static_cast<int>(DirectiveOperation::kPosition);
           operation <= static_cast<int>(DirectiveOperation::kCare);
           ++operation) {
        Candidate candidate =
            MakeCandidate(ChoiceKind::kSelectDirectiveOperation);
        candidate.fields[8] = pending_unit_ + 1;
        candidate.fields[9] = operation;
        AddCandidate(engine, player, std::move(candidate));
      }
      break;
    case Phase::kDirectiveTarget:
      for (int target = 0; target < cells; ++target) {
        const bool needs_item =
            DirectiveNeedsItem(pending_directive_operation_);
        Candidate candidate = MakeCandidate(
            needs_item ? ChoiceKind::kSelectDirectiveTarget
                       : ChoiceKind::kSetDirective);
        candidate.fields[1] = target;
        candidate.fields[6] = static_cast<int64_t>(Priority::kHigh);
        candidate.fields[8] = pending_unit_ + 1;
        candidate.fields[9] =
            static_cast<int64_t>(pending_directive_operation_);
        AddCandidate(engine, player, std::move(candidate));
      }
      break;
    case Phase::kDirectiveItem: {
      const int item_count =
          pending_directive_operation_ == DirectiveOperation::kPlant
              ? kNumCrops
              : kNumItems;
      for (int item_index = 0; item_index < item_count; ++item_index) {
        const bool needs_quantity =
            DirectiveNeedsQuantity(pending_directive_operation_);
        Candidate candidate = MakeCandidate(
            needs_quantity ? ChoiceKind::kSelectDirectiveItem
                           : ChoiceKind::kSetDirective);
        candidate.fields[1] = pending_target_;
        candidate.fields[2] = item_index + 1;
        candidate.fields[6] = static_cast<int64_t>(Priority::kHigh);
        candidate.fields[8] = pending_unit_ + 1;
        candidate.fields[9] =
            static_cast<int64_t>(pending_directive_operation_);
        AddCandidate(engine, player, std::move(candidate));
      }
      break;
    }
    case Phase::kDirectiveQuantity: {
      const bool wait =
          pending_directive_operation_ == DirectiveOperation::kWait;
      const int64_t lower =
          wait ? engine.step_index() % config_.turns_per_day + 1 : 1;
      const int64_t upper =
          wait ? config_.turns_per_day : config_.shed_capacity;
      for (int64_t quantity = lower; quantity <= upper; ++quantity) {
        Candidate candidate = MakeCandidate(ChoiceKind::kSetDirective);
        candidate.fields[1] = pending_target_;
        candidate.fields[2] = pending_item_ + 1;
        candidate.fields[6] = static_cast<int64_t>(Priority::kHigh);
        candidate.fields[7] = quantity;
        candidate.fields[8] = pending_unit_ + 1;
        candidate.fields[9] =
            static_cast<int64_t>(pending_directive_operation_);
        AddCandidate(engine, player, std::move(candidate));
      }
      break;
    }
    case Phase::kCancelDirective:
      for (const UnitDirective& directive : draft_directives_) {
        if (!directive.active ||
            DirectiveKey(directive.unit) <= last_ledger_key_) {
          continue;
        }
        Candidate candidate =
            MakeCandidate(ChoiceKind::kCancelDirective);
        candidate.fields[1] = directive.target;
        candidate.fields[2] = directive.item + 1;
        candidate.fields[6] = static_cast<int64_t>(Priority::kHigh);
        candidate.fields[7] = directive.quantity;
        candidate.fields[8] = directive.unit + 1;
        candidate.fields[9] = static_cast<int64_t>(directive.operation);
        AddCandidate(engine, player, std::move(candidate));
      }
      break;
    case Phase::kDone:
      break;
  }
  if (candidates_.empty() && phase_ != Phase::kDone) {
    throw std::logic_error("intent editor entered a phase without successors");
  }
}

void Session::ApplyChoice(const Candidate& candidate) {
  switch (candidate.kind) {
    case ChoiceKind::kCommit:
      assets_ = draft_assets_;
      work_ = draft_work_;
      positions_ = draft_positions_;
      fetches_ = draft_fetches_;
      directives_ = draft_directives_;
      committed_ = true;
      phase_ = Phase::kDone;
      return;
    case ChoiceKind::kBeginAsset:
      pending_kind_ = candidate.kind;
      phase_ = Phase::kAssetTarget;
      return;
    case ChoiceKind::kBeginCancelAsset:
      phase_ = Phase::kCancelAsset;
      return;
    case ChoiceKind::kBeginWork:
      pending_kind_ = candidate.kind;
      phase_ = Phase::kWorkTarget;
      return;
    case ChoiceKind::kBeginCancelWork:
      phase_ = Phase::kCancelWork;
      return;
    case ChoiceKind::kBeginPosition:
      phase_ = Phase::kPositionRole;
      return;
    case ChoiceKind::kBeginCancelPosition:
      phase_ = Phase::kCancelPosition;
      return;
    case ChoiceKind::kBeginStore:
      phase_ = Phase::kStoreItem;
      return;
    case ChoiceKind::kBeginFetch:
      phase_ = Phase::kFetchUnit;
      return;
    case ChoiceKind::kBeginCancelFetch:
      phase_ = Phase::kCancelFetch;
      return;
    case ChoiceKind::kBeginDirective:
      phase_ = Phase::kDirectiveUnit;
      return;
    case ChoiceKind::kBeginCancelDirective:
      phase_ = Phase::kCancelDirective;
      return;
    case ChoiceKind::kSelectTarget:
      pending_target_ = static_cast<int>(candidate.fields[1]);
      phase_ = pending_kind_ == ChoiceKind::kBeginAsset
                   ? Phase::kAssetProfile
                   : Phase::kWorkProfile;
      return;
    case ChoiceKind::kSetAsset: {
      const int item_index = static_cast<int>(candidate.fields[2]) - 1;
      AssetContract contract;
      contract.active = true;
      contract.kind = item_index < kNumCrops ? AssetKind::kCrop
                                             : AssetKind::kAnimal;
      contract.item = item_index;
      contract.maintenance = static_cast<Maintenance>(candidate.fields[3]);
      contract.product_collection =
          static_cast<ProductCollection>(candidate.fields[4]);
      contract.fertilizer_collection =
          static_cast<FertilizerCollection>(candidate.fields[5]);
      contract.priority = static_cast<Priority>(candidate.fields[6]);
      draft_assets_[pending_target_] = contract;
      last_ledger_key_ = AssetKey(pending_target_);
      phase_ = Phase::kRoot;
      return;
    }
    case ChoiceKind::kCancelAsset: {
      const int target = static_cast<int>(candidate.fields[1]);
      draft_assets_[target] = AssetContract{};
      last_ledger_key_ = AssetKey(target);
      phase_ = Phase::kRoot;
      return;
    }
    case ChoiceKind::kAddWork: {
      WorkOrder order;
      order.target = static_cast<int>(candidate.fields[1]);
      order.kind = static_cast<WorkKind>(candidate.fields[2] - 1);
      order.priority = static_cast<Priority>(candidate.fields[6]);
      order.expected_tile_kind = pending_work_tile_kind_;
      order.expected_item = pending_work_item_;
      order.expected_generation = pending_work_generation_;
      draft_work_.erase(
          std::remove_if(draft_work_.begin(), draft_work_.end(),
                         [&](const WorkOrder& current) {
                           return current.target == order.target &&
                                  current.kind == order.kind;
                         }),
          draft_work_.end());
      draft_work_.push_back(order);
      last_ledger_key_ = WorkKey(order.target, order.kind);
      phase_ = Phase::kRoot;
      return;
    }
    case ChoiceKind::kCancelWork: {
      const int target = static_cast<int>(candidate.fields[1]);
      const WorkKind kind = static_cast<WorkKind>(candidate.fields[2] - 1);
      const int store_item = static_cast<int>(candidate.fields[3]) - 1;
      draft_work_.erase(
          std::remove_if(draft_work_.begin(), draft_work_.end(),
                         [&](const WorkOrder& order) {
                           return order.kind == kind &&
                                  (kind == WorkKind::kStore
                                       ? order.item == store_item
                                       : order.target == target);
                         }),
          draft_work_.end());
      last_ledger_key_ = kind == WorkKind::kStore
                             ? StoreKey(store_item)
                             : WorkKey(target, kind);
      phase_ = Phase::kRoot;
      return;
    }
    case ChoiceKind::kSelectRole:
      pending_role_ = static_cast<PositionRole>(candidate.fields[2] - 1);
      phase_ = Phase::kPositionTarget;
      return;
    case ChoiceKind::kSetPosition: {
      const PositionRole role =
          static_cast<PositionRole>(candidate.fields[2] - 1);
      PositionIntent position;
      position.active = true;
      position.role = role;
      position.target = static_cast<int>(candidate.fields[1]);
      position.priority = static_cast<Priority>(candidate.fields[6]);
      draft_positions_[static_cast<int>(role)] = position;
      last_ledger_key_ = PositionKey(role);
      phase_ = Phase::kRoot;
      return;
    }
    case ChoiceKind::kCancelPosition: {
      const PositionRole role =
          static_cast<PositionRole>(candidate.fields[2] - 1);
      draft_positions_[static_cast<int>(role)] = PositionIntent{};
      last_ledger_key_ = PositionKey(role);
      phase_ = Phase::kRoot;
      return;
    }
    case ChoiceKind::kSelectStoreItem:
      pending_item_ = static_cast<int>(candidate.fields[2]) - 1;
      phase_ = Phase::kStoreQuantity;
      return;
    case ChoiceKind::kSelectStoreQuantity:
      pending_quantity_ = candidate.fields[7];
      phase_ = Phase::kStorePriority;
      return;
    case ChoiceKind::kAddStore: {
      WorkOrder order;
      order.kind = WorkKind::kStore;
      order.item = static_cast<int>(candidate.fields[2]) - 1;
      order.quantity = candidate.fields[7];
      order.priority = static_cast<Priority>(candidate.fields[6]);
      draft_work_.erase(
          std::remove_if(draft_work_.begin(), draft_work_.end(),
                         [&](const WorkOrder& current) {
                           return current.kind == WorkKind::kStore &&
                                  current.item == order.item;
                         }),
          draft_work_.end());
      draft_work_.push_back(order);
      last_ledger_key_ = StoreKey(order.item);
      phase_ = Phase::kRoot;
      return;
    }
    case ChoiceKind::kSelectFetchUnit:
      pending_unit_ = static_cast<int>(candidate.fields[8]) - 1;
      phase_ = Phase::kFetchItem;
      return;
    case ChoiceKind::kSelectFetchItem:
      pending_item_ = static_cast<int>(candidate.fields[2]) - 1;
      phase_ = Phase::kFetchQuantity;
      return;
    case ChoiceKind::kSetFetch: {
      FetchIntent fetch;
      fetch.active = true;
      fetch.unit = static_cast<int>(candidate.fields[8]) - 1;
      fetch.item = static_cast<int>(candidate.fields[2]) - 1;
      fetch.quantity = candidate.fields[7];
      if (fetch.unit < 0 ||
          fetch.unit >= static_cast<int>(draft_fetches_.size())) {
        throw std::logic_error("fetch intent selected an unavailable unit");
      }
      draft_fetches_[fetch.unit] = fetch;
      last_ledger_key_ = FetchKey(fetch.unit);
      phase_ = Phase::kRoot;
      return;
    }
    case ChoiceKind::kCancelFetch: {
      const int unit = static_cast<int>(candidate.fields[8]) - 1;
      if (unit < 0 || unit >= static_cast<int>(draft_fetches_.size())) {
        throw std::logic_error("fetch cancellation selected an unavailable unit");
      }
      draft_fetches_[unit] = FetchIntent{};
      last_ledger_key_ = FetchKey(unit);
      phase_ = Phase::kRoot;
      return;
    }
    case ChoiceKind::kSelectDirectiveUnit:
      pending_unit_ = static_cast<int>(candidate.fields[8]) - 1;
      phase_ = Phase::kDirectiveOperation;
      return;
    case ChoiceKind::kSelectDirectiveOperation:
      pending_directive_operation_ =
          static_cast<DirectiveOperation>(candidate.fields[9]);
      pending_target_ = -1;
      pending_item_ = -1;
      pending_quantity_ = 0;
      phase_ = pending_directive_operation_ == DirectiveOperation::kWait
                   ? Phase::kDirectiveQuantity
                   : Phase::kDirectiveTarget;
      return;
    case ChoiceKind::kSelectDirectiveTarget:
      pending_target_ = static_cast<int>(candidate.fields[1]);
      phase_ = Phase::kDirectiveItem;
      return;
    case ChoiceKind::kSelectDirectiveItem:
      pending_item_ = static_cast<int>(candidate.fields[2]) - 1;
      phase_ = Phase::kDirectiveQuantity;
      return;
    case ChoiceKind::kSetDirective: {
      UnitDirective directive;
      directive.active = true;
      directive.unit = static_cast<int>(candidate.fields[8]) - 1;
      directive.operation =
          static_cast<DirectiveOperation>(candidate.fields[9]);
      directive.target = static_cast<int>(candidate.fields[1]);
      directive.item = static_cast<int>(candidate.fields[2]) - 1;
      directive.quantity = candidate.fields[7];
      directive.day = turn_step_ / config_.turns_per_day;
      if (directive.unit < 0 ||
          directive.unit >= static_cast<int>(draft_directives_.size())) {
        throw std::logic_error(
            "unit directive selected an unavailable unit");
      }
      draft_directives_[directive.unit] = directive;
      last_ledger_key_ = DirectiveKey(directive.unit);
      phase_ = Phase::kRoot;
      return;
    }
    case ChoiceKind::kCancelDirective: {
      const int unit = static_cast<int>(candidate.fields[8]) - 1;
      if (unit < 0 || unit >= static_cast<int>(draft_directives_.size())) {
        throw std::logic_error(
            "unit directive cancellation selected an unavailable unit");
      }
      draft_directives_[unit] = UnitDirective{};
      last_ledger_key_ = DirectiveKey(unit);
      phase_ = Phase::kRoot;
      return;
    }
    case ChoiceKind::kMarketHire:
      market_phase_ = true;
      market_prefix_.push_back(MarketOrder{OrderKind::kHire, 0, 0});
      phase_ = Phase::kRoot;
      return;
    case ChoiceKind::kMarketBuyLand:
      market_phase_ = true;
      market_prefix_.push_back(MarketOrder{OrderKind::kBuyLand, 0, 0});
      phase_ = Phase::kRoot;
      return;
    case ChoiceKind::kMarketSkipSlot:
      market_phase_ = true;
      market_prefix_.push_back(std::nullopt);
      phase_ = Phase::kRoot;
      return;
    case ChoiceKind::kMarketSell:
    case ChoiceKind::kMarketBuySeed:
    case ChoiceKind::kMarketBuyProduct:
    case ChoiceKind::kMarketBuyAnimal:
      market_phase_ = true;
      pending_market_.kind = OrderForChoice(candidate.kind);
      pending_market_.item = static_cast<int>(candidate.fields[2]) - 1;
      pending_market_.upper = candidate.fields[7];
      phase_ = Phase::kMarketQuantity;
      return;
    case ChoiceKind::kSelectMarketQuantity:
      market_prefix_.push_back(MarketOrder{pending_market_.kind,
                                           pending_market_.item,
                                           candidate.fields[7]});
      phase_ = Phase::kRoot;
      return;
  }
}

}  // namespace kagg::intents
