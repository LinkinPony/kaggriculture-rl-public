#include "intents/session.hpp"

#include <algorithm>
#include <stdexcept>
#include <utility>

namespace kagg::intents {
namespace {

int64_t Owned(const PrivateState& priv, int item_index) {
  int64_t result = priv.shed[item_index];
  for (const Inventory& inventory : priv.inventories) {
    result += inventory.Get(item_index);
  }
  return result;
}

bool IsAnimalItem(int item_index) {
  return item_index >= item::kGoose && item_index < kNumItems;
}

int PriorityValue(Priority priority) {
  return static_cast<int>(priority);
}

std::pair<int, int> UnitPosition(const Farm& farm, int unit) {
  if (unit == 0) return {farm.farmer_x, farm.farmer_y};
  return farm.hands.at(static_cast<size_t>(unit - 1));
}

WorkKind DirectiveKind(DirectiveOperation operation) {
  return static_cast<WorkKind>(9 + static_cast<int>(operation));
}

bool WorkTargetMatches(const WorkOrder& order, const Tile& tile) {
  if (tile.kind != order.expected_tile_kind) return false;
  if (tile.kind == TileKind::kPlant) {
    return tile.crop == order.expected_item &&
           tile.planted_day == order.expected_generation;
  }
  if (tile.kind == TileKind::kStructure && tile.has_animal) {
    return item::kGoose + tile.animal == order.expected_item &&
           tile.placed_day == order.expected_generation;
  }
  if (tile.kind == TileKind::kStructure) {
    return static_cast<int>(tile.structure) == order.expected_item;
  }
  return true;
}

bool WorkEffectReady(const WorkOrder& order, const Tile& tile, int day) {
  switch (order.kind) {
    case WorkKind::kHarvest:
      return tile.kind == TileKind::kPlant && tile.yield_units > 0 &&
             day - tile.planted_day >= kCrops[tile.crop].first_yield_day;
    case WorkKind::kCollectProduct:
      return tile.kind == TileKind::kStructure && tile.has_animal &&
             tile.yield_units > 0;
    case WorkKind::kFertilize:
      return tile.kind == TileKind::kPlant;
    case WorkKind::kCareOnce:
      return tile.kind == TileKind::kStructure && tile.has_animal &&
             !tile.cared_today;
    case WorkKind::kCollectFertilizer:
      return tile.kind == TileKind::kStructure && tile.has_animal &&
             tile.fertilizer_available;
    case WorkKind::kClear:
      return tile.kind != TileKind::kEmpty && tile.kind != TileKind::kLocked &&
             !(tile.kind == TileKind::kStructure && tile.has_animal);
    case WorkKind::kWaterOnce:
      return tile.kind == TileKind::kPlant && !tile.watered_today;
    case WorkKind::kFeedOnce:
      return tile.kind == TileKind::kStructure && tile.has_animal &&
             !tile.fed_today;
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
      return true;
  }
  return false;
}

}  // namespace

Session::Session(Config config) : config_(std::move(config)) {
  if (config_.board_size < 1) {
    throw std::invalid_argument("intent ledger board size must be positive");
  }
  config_.max_market_orders = std::max(1, config_.max_market_orders);
  config_.turns_per_day = std::max(1, config_.turns_per_day);
  const size_t cells =
      static_cast<size_t>(config_.board_size * config_.board_size);
  assets_.resize(cells);
  terminal_asset_status_.assign(cells, Status::kEmpty);
  terminal_asset_reason_.assign(cells, BlockReason::kNone);
  terminal_asset_step_.assign(cells, -1);
}

void Session::Reset() {
  assets_.assign(static_cast<size_t>(config_.board_size * config_.board_size),
                 AssetContract{});
  work_.clear();
  positions_ = {};
  fetches_.clear();
  directives_.clear();
  terminal_asset_status_.assign(assets_.size(), Status::kEmpty);
  terminal_asset_reason_.assign(assets_.size(), BlockReason::kNone);
  terminal_asset_step_.assign(assets_.size(), -1);
  draft_assets_.clear();
  draft_work_.clear();
  draft_positions_ = {};
  draft_fetches_.clear();
  draft_directives_.clear();
  market_prefix_.clear();
  candidates_.clear();
  phase_ = Phase::kRoot;
  pending_kind_ = ChoiceKind::kCommit;
  pending_target_ = -1;
  pending_role_ = PositionRole::kFarmer;
  pending_unit_ = -1;
  pending_directive_operation_ = DirectiveOperation::kPosition;
  pending_item_ = -1;
  pending_quantity_ = 0;
  pending_work_tile_kind_ = TileKind::kEmpty;
  pending_work_item_ = -1;
  pending_work_generation_ = -1;
  pending_market_ = {};
  last_ledger_key_ = -1;
  market_phase_ = false;
  committed_ = false;
  turn_step_ = -1;
  player_ = -1;
  last_action_step_ = -1;
  cached_action_ = {};
}

bool Session::ContractMatches(const AssetContract& contract,
                              const Tile& tile) const {
  if (!contract.active) return false;
  if (contract.kind == AssetKind::kCrop) {
    return tile.kind == TileKind::kPlant && tile.crop == contract.item;
  }
  if (contract.kind == AssetKind::kAnimal && IsAnimalItem(contract.item)) {
    return tile.kind == TileKind::kStructure && tile.has_animal &&
           tile.animal == contract.item - item::kGoose;
  }
  return false;
}

int Session::GenerationStamp(const AssetContract& contract,
                             const Tile& tile) const {
  if (contract.kind == AssetKind::kCrop) {
    return tile.planted_day * 16 + tile.crop;
  }
  if (contract.kind == AssetKind::kAnimal) {
    return tile.placed_day * 16 + tile.animal;
  }
  return -1;
}

bool Session::ServiceCovers(int target, WorkKind kind, const Tile& tile) const {
  if (target < 0 || target >= static_cast<int>(draft_assets_.size())) {
    return false;
  }
  const AssetContract& contract = draft_assets_[target];
  if (!ContractMatches(contract, tile)) return false;
  if (kind == WorkKind::kWaterOnce) {
    return contract.kind == AssetKind::kCrop &&
           contract.maintenance == Maintenance::kYield;
  }
  if (kind == WorkKind::kFeedOnce || kind == WorkKind::kCareOnce) {
    return contract.kind == AssetKind::kAnimal &&
           contract.maintenance == Maintenance::kCared;
  }
  if (kind == WorkKind::kCollectFertilizer) {
    return contract.kind == AssetKind::kAnimal &&
           contract.fertilizer_collection == FertilizerCollection::kDaily;
  }
  return false;
}

void Session::Reconcile(const Engine& engine, int player) {
  const Farm& farm = engine.farm(player);
  for (int target = 0; target < static_cast<int>(assets_.size()); ++target) {
    if (terminal_asset_step_[target] < engine.step_index()) {
      terminal_asset_status_[target] = Status::kEmpty;
      terminal_asset_reason_[target] = BlockReason::kNone;
    }
  }
  const PrivateState& priv = engine.priv(player);
  fetches_.resize(priv.inventories.size());
  for (int unit = 0; unit < static_cast<int>(fetches_.size()); ++unit) {
    FetchIntent& fetch = fetches_[unit];
    if (!fetch.active) continue;
    if (fetch.unit != unit || fetch.item < 0 || fetch.item >= kNumItems ||
        fetch.quantity <= 0 ||
        priv.inventories[unit].Get(fetch.item) >= fetch.quantity) {
      fetch = FetchIntent{};
    }
  }
  directives_.resize(priv.inventories.size());
  const int day = engine.step_index() / config_.turns_per_day;
  const int hour = engine.step_index() % config_.turns_per_day;
  for (int unit = 0; unit < static_cast<int>(directives_.size()); ++unit) {
    UnitDirective& directive = directives_[unit];
    if (!directive.active) continue;
    if (directive.unit != unit || directive.day != day) {
      directive = UnitDirective{};
      continue;
    }
    if (directive.operation == DirectiveOperation::kWait) {
      if (hour >= directive.quantity) directive = UnitDirective{};
      continue;
    }
    if (directive.operation != DirectiveOperation::kPosition) continue;
    const auto [x, y] = UnitPosition(farm, unit);
    const int target_x = directive.target % config_.board_size;
    const int target_y = directive.target / config_.board_size;
    if (x == target_x && y == target_y) directive = UnitDirective{};
  }
  work_.erase(std::remove_if(work_.begin(), work_.end(), [&](const WorkOrder& order) {
                if (order.dispatched_step >= 0 &&
                    engine.step_index() > order.dispatched_step) {
                  return true;
                }
                if (order.kind == WorkKind::kStore) {
                  return order.quantity <= 0 ||
                         (turn_step_ >= 0 && engine.step_index() > turn_step_ &&
                          Owned(priv, order.item) <= priv.shed[order.item]);
                }
                return order.target < 0 ||
                       order.target >= static_cast<int>(farm.tiles.size()) ||
                       !WorkTargetMatches(order, farm.tiles[order.target]);
              }),
              work_.end());

  for (int target = 0; target < static_cast<int>(assets_.size()); ++target) {
    AssetContract& contract = assets_[target];
    if (!contract.active) continue;
    const Tile& tile = farm.tiles[target];
    if (contract.bound) {
      if (!ContractMatches(contract, tile) ||
          GenerationStamp(contract, tile) != contract.generation_stamp) {
        terminal_asset_status_[target] = Status::kFailed;
        terminal_asset_reason_[target] = BlockReason::kAssetDisappeared;
        terminal_asset_step_[target] = engine.step_index();
        contract = AssetContract{};
      }
      continue;
    }
    if (ContractMatches(contract, tile)) {
      contract.bound = true;
      contract.generation_stamp = GenerationStamp(contract, tile);
    }
  }

  for (int role = 0; role < 2; ++role) {
    PositionIntent& position = positions_[role];
    if (!position.active) continue;
    const int x = position.target % config_.board_size;
    const int y = position.target / config_.board_size;
    bool reached = role == static_cast<int>(PositionRole::kFarmer)
                       ? farm.farmer_x == x && farm.farmer_y == y
                       : std::any_of(farm.hands.begin(), farm.hands.end(),
                                     [&](const auto& hand) {
                                       return hand.first == x && hand.second == y;
                                     });
    if (reached) position = PositionIntent{};
  }
}

void Session::BeginTurn(const Engine& engine, int player) {
  if (player < 0 || player > 1) {
    throw std::invalid_argument("intent ledger player must be 0 or 1");
  }
  if (engine.config().board_size != config_.board_size ||
      engine.config().turns_per_day != config_.turns_per_day ||
      engine.config().episode_steps != config_.episode_steps ||
      engine.config().max_market_orders != config_.max_market_orders ||
      engine.config().shed_capacity != config_.shed_capacity) {
    throw std::invalid_argument("intent ledger session and engine configurations differ");
  }
  const int step = engine.step_index();
  if ((turn_step_ >= 0 && step < turn_step_) ||
      (player_ >= 0 && player != player_)) {
    Reset();
  }
  if (step == turn_step_ && player == player_) return;

  Reconcile(engine, player);
  draft_assets_ = assets_;
  draft_work_ = work_;
  draft_positions_ = positions_;
  draft_fetches_ = fetches_;
  draft_directives_ = directives_;
  market_prefix_.clear();
  candidates_.clear();
  phase_ = Phase::kRoot;
  pending_kind_ = ChoiceKind::kCommit;
  pending_target_ = -1;
  pending_unit_ = -1;
  pending_directive_operation_ = DirectiveOperation::kPosition;
  pending_item_ = -1;
  pending_quantity_ = 0;
  pending_work_tile_kind_ = TileKind::kEmpty;
  pending_work_item_ = -1;
  pending_work_generation_ = -1;
  pending_market_ = {};
  last_ledger_key_ = -1;
  market_phase_ = false;
  committed_ = false;
  turn_step_ = step;
  player_ = player;
  last_action_step_ = -1;
  cached_action_ = {};
}

Observation Session::Observe(const Engine& engine, int player) {
  BeginTurn(engine, player);
  GenerateCandidates(engine, player);

  Observation observation;
  observation.phase = phase_;
  observation.candidates = candidates_;
  observation.market_prefix.reserve(market_prefix_.size());
  for (const std::optional<MarketOrder>& order : market_prefix_) {
    observation.market_prefix.push_back(
        order ? std::array<int64_t, kMarketFieldCount>{
                    static_cast<int64_t>(order->kind), order->item,
                    order->remaining}
              : std::array<int64_t, kMarketFieldCount>{kMarketSkipKind, -1, 0});
  }

  const Farm& farm = engine.farm(player);
  const PrivateState& priv = engine.priv(player);
  const int end_of_day =
      (engine.step_index() / std::max(1, config_.turns_per_day) + 1) *
          std::max(1, config_.turns_per_day) -
      1;
  observation.ledger.resize(draft_assets_.size());
  observation.status.resize(draft_assets_.size());
  observation.work_priorities.resize(draft_assets_.size());
  for (int target = 0; target < static_cast<int>(draft_assets_.size()); ++target) {
    const AssetContract& contract = draft_assets_[target];
    observation.ledger[target] = {
        contract.active ? 1 : 0,
        static_cast<int64_t>(contract.kind),
        contract.item + 1,
        static_cast<int64_t>(contract.maintenance),
        static_cast<int64_t>(contract.product_collection),
        static_cast<int64_t>(contract.fertilizer_collection),
        static_cast<int64_t>(contract.priority),
        contract.bound ? 1 : 0,
    };
    observation.work_priorities[target].fill(-1);

    Status status = terminal_asset_status_[target];
    BlockReason reason = terminal_asset_reason_[target];
    int shortfall_item = -1;
    if (contract.active) {
      const Tile& tile = farm.tiles[target];
      if (ContractMatches(contract, tile)) {
        const bool at_risk =
            (tile.kind == TileKind::kPlant && !tile.watered_today &&
             tile.consecutive_unwatered >= 1) ||
            (tile.kind == TileKind::kStructure && tile.has_animal &&
             !tile.fed_today && tile.consecutive_unfed >= 1);
        status = at_risk ? Status::kAtRisk : Status::kSatisfied;
        if (at_risk && contract.kind == AssetKind::kAnimal &&
            Owned(priv, item::kWheat) <= 0) {
          reason = BlockReason::kWheatShortfall;
          shortfall_item = item::kWheat;
        }
      } else if (tile.kind == TileKind::kLocked) {
        status = Status::kBlocked;
        reason = BlockReason::kLandLocked;
      } else if (contract.kind == AssetKind::kCrop &&
                 tile.kind == TileKind::kEmpty &&
                 priv.seeds[contract.item] <= 0) {
        status = Status::kBlocked;
        reason = BlockReason::kSeedShortfall;
        shortfall_item = contract.item;
      } else if (contract.kind == AssetKind::kAnimal &&
                 tile.kind == TileKind::kStructure && !tile.has_animal &&
                 Owned(priv, contract.item) <= 0) {
        status = Status::kBlocked;
        reason = BlockReason::kAnimalShortfall;
        shortfall_item = contract.item;
      } else if (tile.kind == TileKind::kEmpty || tile.kind == TileKind::kWeed ||
                 (tile.kind == TileKind::kStructure && !tile.has_animal)) {
        status = Status::kRunning;
      } else {
        status = Status::kBlocked;
        reason = BlockReason::kConflictingAsset;
      }
    }
    observation.status[target] = {
        static_cast<int64_t>(status), static_cast<int64_t>(reason),
        shortfall_item + 1, end_of_day - engine.step_index()};
  }
  for (const WorkOrder& order : draft_work_) {
    Status work_status = Status::kRunning;
    BlockReason reason = BlockReason::kNone;
    if (order.kind == WorkKind::kStore) {
      if (ShedTotal(priv) >= config_.shed_capacity) {
        work_status = Status::kBlocked;
        reason = BlockReason::kShedCapacity;
      }
    } else if (order.kind == WorkKind::kFeedOnce &&
               Owned(priv, item::kWheat) <= 0) {
      work_status = Status::kBlocked;
      reason = BlockReason::kWheatShortfall;
    } else if (order.kind == WorkKind::kFertilize &&
               Owned(priv, item::kFertilizer) <= 0) {
      work_status = Status::kBlocked;
      reason = BlockReason::kFertilizerShortfall;
    } else if (!WorkEffectReady(order, farm.tiles[order.target],
                                engine.step_index() / config_.turns_per_day)) {
      work_status = Status::kPending;
    }
    observation.work_orders.push_back(
        {static_cast<int64_t>(order.kind), order.target, order.item + 1,
         order.quantity, static_cast<int64_t>(order.priority),
         static_cast<int64_t>(work_status), static_cast<int64_t>(reason),
         config_.episode_steps - engine.step_index(), 0});
    if (order.kind == WorkKind::kStore || order.target < 0 ||
        order.target >= static_cast<int>(observation.work_priorities.size())) {
      continue;
    }
    observation.work_priorities[order.target][static_cast<int>(order.kind)] =
        PriorityValue(order.priority);
  }
  for (const FetchIntent& fetch : draft_fetches_) {
    if (!fetch.active) continue;
    Status fetch_status = Status::kRunning;
    BlockReason reason = BlockReason::kNone;
    if (fetch.unit < 0 ||
        fetch.unit >= static_cast<int>(priv.inventories.size())) {
      fetch_status = Status::kBlocked;
      reason = BlockReason::kNoEligibleUnit;
    } else if (fetch.item < 0 || fetch.item >= kNumItems ||
               priv.shed[fetch.item] <= 0) {
      fetch_status = Status::kBlocked;
      reason = BlockReason::kShedItemShortfall;
    }
    observation.work_orders.push_back(
        {static_cast<int64_t>(WorkKind::kFetch), -1, fetch.item + 1,
         fetch.quantity, static_cast<int64_t>(Priority::kHigh),
         static_cast<int64_t>(fetch_status), static_cast<int64_t>(reason),
         config_.episode_steps - engine.step_index(), fetch.unit + 1});
  }
  for (const UnitDirective& directive : draft_directives_) {
    if (!directive.active) continue;
    observation.work_orders.push_back(
        {static_cast<int64_t>(DirectiveKind(directive.operation)),
         directive.target, directive.item + 1, directive.quantity,
         static_cast<int64_t>(Priority::kHigh),
         static_cast<int64_t>(Status::kRunning),
         static_cast<int64_t>(BlockReason::kNone),
         config_.turns_per_day -
             engine.step_index() % config_.turns_per_day,
         directive.unit + 1});
  }
  std::stable_sort(
      observation.work_orders.begin(), observation.work_orders.end(),
      [&](const auto& left, const auto& right) {
        const auto key = [&](const auto& row) {
          const WorkKind kind = static_cast<WorkKind>(row[0]);
          if (kind == WorkKind::kStore) return StoreKey(row[2] - 1);
          if (kind == WorkKind::kFetch) return FetchKey(row[8] - 1);
          if (kind >= WorkKind::kDirectivePosition) {
            return DirectiveKey(row[8] - 1);
          }
          return WorkKey(row[1], kind);
        };
        return key(left) < key(right);
      });
  for (int role = 0; role < 2; ++role) {
    const PositionIntent& position = draft_positions_[role];
    observation.positions[role] = {
        position.active ? 1 : 0, position.target,
        static_cast<int64_t>(position.priority), role};
  }
  return observation;
}

DeviceAuxiliary Session::DeviceStateAuxiliary(const Engine& engine,
                                              int player) {
  BeginTurn(engine, player);
  const Farm& farm = engine.farm(player);
  DeviceAuxiliary result;
  result.inactive_status.resize(assets_.size());
  result.asset_risk.resize(assets_.size());
  for (int target = 0; target < static_cast<int>(assets_.size()); ++target) {
    const Tile& tile = farm.tiles[target];
    result.inactive_status[target] = {
        static_cast<int64_t>(terminal_asset_status_[target]),
        static_cast<int64_t>(terminal_asset_reason_[target]),
    };
    result.asset_risk[target] =
        (tile.kind == TileKind::kPlant && !tile.watered_today &&
         tile.consecutive_unwatered >= 1) ||
                (tile.kind == TileKind::kStructure && tile.has_animal &&
                 !tile.fed_today && tile.consecutive_unfed >= 1)
            ? 1
            : 0;
  }
  return result;
}

Phase Session::Select(int candidate_index) {
  if (phase_ == Phase::kDone || committed_) {
    throw std::logic_error("intent transaction is already committed");
  }
  if (candidate_index < 0 || candidate_index >= static_cast<int>(candidates_.size())) {
    throw std::out_of_range("intent candidate index is invalid");
  }
  ApplyChoice(candidates_[candidate_index]);
  candidates_.clear();
  return phase_;
}

bool Session::DecisionRequired(const Engine& engine, int player) {
  BeginTurn(engine, player);
  return !committed_;
}

PlayerAction Session::Action(const Engine& engine, int player) {
  BeginTurn(engine, player);
  if (!committed_) {
    throw std::logic_error("intent action requires COMMIT");
  }
  if (last_action_step_ != engine.step_index()) {
    cached_action_ = CompileAction(engine, player);
    last_action_step_ = engine.step_index();
  }
  return cached_action_;
}

NumericAction Session::ActionNumeric(const Engine& engine, int player) {
  const PlayerAction action = Action(engine, player);
  NumericAction result;
  result.unit_count = 1 + static_cast<int64_t>(engine.farm(player).hands.size());
  result.tokens.resize(static_cast<size_t>(result.unit_count) + action.market.size());
  result.quantities.resize(result.tokens.size());
  result.decision_count = policy::EncodePlayerAction(
      action, static_cast<int>(result.unit_count), result.tokens.data(),
      result.quantities.data(), static_cast<int>(result.tokens.size()));
  return result;
}

int64_t Session::AssetKey(int target) const {
  return static_cast<int64_t>(target) * 16;
}

int64_t Session::WorkKey(int target, WorkKind kind) const {
  return static_cast<int64_t>(target) * 16 + 1 + static_cast<int64_t>(kind);
}

int64_t Session::PositionKey(PositionRole role) const {
  return static_cast<int64_t>(config_.board_size * config_.board_size) * 16 +
         static_cast<int64_t>(role);
}

int64_t Session::StoreKey(int item_index) const {
  return static_cast<int64_t>(config_.board_size * config_.board_size) * 16 + 2 +
         item_index;
}

int64_t Session::FetchKey(int unit) const {
  return static_cast<int64_t>(config_.board_size * config_.board_size) * 16 + 2 +
         kNumItems + unit;
}

int64_t Session::DirectiveKey(int unit) const {
  return static_cast<int64_t>(config_.board_size * config_.board_size) * 16 +
         2 + kNumItems + 256 + unit;
}

const char* PhaseName(Phase phase) {
  switch (phase) {
    case Phase::kRoot: return "ROOT";
    case Phase::kAssetTarget: return "ASSET_TARGET";
    case Phase::kAssetProfile: return "ASSET_PROFILE";
    case Phase::kCancelAsset: return "CANCEL_ASSET";
    case Phase::kWorkTarget: return "WORK_TARGET";
    case Phase::kWorkProfile: return "WORK_PROFILE";
    case Phase::kCancelWork: return "CANCEL_WORK";
    case Phase::kPositionRole: return "POSITION_ROLE";
    case Phase::kPositionTarget: return "POSITION_TARGET";
    case Phase::kCancelPosition: return "CANCEL_POSITION";
    case Phase::kStoreItem: return "STORE_ITEM";
    case Phase::kStoreQuantity: return "STORE_QUANTITY";
    case Phase::kStorePriority: return "STORE_PRIORITY";
    case Phase::kMarketQuantity: return "MARKET_QUANTITY";
    case Phase::kFetchUnit: return "FETCH_UNIT";
    case Phase::kFetchItem: return "FETCH_ITEM";
    case Phase::kFetchQuantity: return "FETCH_QUANTITY";
    case Phase::kCancelFetch: return "CANCEL_FETCH";
    case Phase::kDirectiveUnit: return "DIRECTIVE_UNIT";
    case Phase::kDirectiveOperation: return "DIRECTIVE_OPERATION";
    case Phase::kDirectiveTarget: return "DIRECTIVE_TARGET";
    case Phase::kDirectiveItem: return "DIRECTIVE_ITEM";
    case Phase::kDirectiveQuantity: return "DIRECTIVE_QUANTITY";
    case Phase::kCancelDirective: return "CANCEL_DIRECTIVE";
    case Phase::kDone: return "DONE";
  }
  return "DONE";
}

const char* ChoiceKindName(ChoiceKind kind) {
  switch (kind) {
    case ChoiceKind::kCommit: return "COMMIT";
    case ChoiceKind::kBeginAsset: return "BEGIN_ASSET";
    case ChoiceKind::kBeginCancelAsset: return "BEGIN_CANCEL_ASSET";
    case ChoiceKind::kBeginWork: return "BEGIN_WORK";
    case ChoiceKind::kBeginCancelWork: return "BEGIN_CANCEL_WORK";
    case ChoiceKind::kBeginPosition: return "BEGIN_POSITION";
    case ChoiceKind::kBeginCancelPosition: return "BEGIN_CANCEL_POSITION";
    case ChoiceKind::kBeginStore: return "BEGIN_STORE";
    case ChoiceKind::kSelectTarget: return "SELECT_TARGET";
    case ChoiceKind::kSetAsset: return "SET_ASSET";
    case ChoiceKind::kCancelAsset: return "CANCEL_ASSET";
    case ChoiceKind::kAddWork: return "ADD_WORK";
    case ChoiceKind::kCancelWork: return "CANCEL_WORK";
    case ChoiceKind::kSelectRole: return "SELECT_ROLE";
    case ChoiceKind::kSetPosition: return "SET_POSITION";
    case ChoiceKind::kCancelPosition: return "CANCEL_POSITION";
    case ChoiceKind::kSelectStoreItem: return "SELECT_STORE_ITEM";
    case ChoiceKind::kSelectStoreQuantity: return "SELECT_STORE_QUANTITY";
    case ChoiceKind::kAddStore: return "ADD_STORE";
    case ChoiceKind::kMarketSell: return "MARKET_SELL";
    case ChoiceKind::kMarketBuySeed: return "MARKET_BUY_SEED";
    case ChoiceKind::kMarketBuyProduct: return "MARKET_BUY_PRODUCT";
    case ChoiceKind::kMarketBuyAnimal: return "MARKET_BUY_ANIMAL";
    case ChoiceKind::kMarketHire: return "MARKET_HIRE";
    case ChoiceKind::kMarketBuyLand: return "MARKET_BUY_LAND";
    case ChoiceKind::kSelectMarketQuantity: return "SELECT_MARKET_QUANTITY";
    case ChoiceKind::kBeginFetch: return "BEGIN_FETCH";
    case ChoiceKind::kBeginCancelFetch: return "BEGIN_CANCEL_FETCH";
    case ChoiceKind::kSelectFetchUnit: return "SELECT_FETCH_UNIT";
    case ChoiceKind::kSelectFetchItem: return "SELECT_FETCH_ITEM";
    case ChoiceKind::kSetFetch: return "SET_FETCH";
    case ChoiceKind::kCancelFetch: return "CANCEL_FETCH";
    case ChoiceKind::kBeginDirective: return "BEGIN_DIRECTIVE";
    case ChoiceKind::kBeginCancelDirective: return "BEGIN_CANCEL_DIRECTIVE";
    case ChoiceKind::kSelectDirectiveUnit: return "SELECT_DIRECTIVE_UNIT";
    case ChoiceKind::kSelectDirectiveOperation:
      return "SELECT_DIRECTIVE_OPERATION";
    case ChoiceKind::kSelectDirectiveTarget: return "SELECT_DIRECTIVE_TARGET";
    case ChoiceKind::kSelectDirectiveItem: return "SELECT_DIRECTIVE_ITEM";
    case ChoiceKind::kSetDirective: return "SET_DIRECTIVE";
    case ChoiceKind::kCancelDirective: return "CANCEL_DIRECTIVE";
    case ChoiceKind::kMarketSkipSlot: return "MARKET_SKIP_SLOT";
  }
  return "COMMIT";
}

const char* WorkKindName(WorkKind kind) {
  switch (kind) {
    case WorkKind::kHarvest: return "HARVEST";
    case WorkKind::kFertilize: return "FERTILIZE";
    case WorkKind::kCareOnce: return "CARE_ONCE";
    case WorkKind::kCollectProduct: return "COLLECT_PRODUCT";
    case WorkKind::kCollectFertilizer: return "COLLECT_FERTILIZER";
    case WorkKind::kClear: return "CLEAR";
    case WorkKind::kWaterOnce: return "WATER_ONCE";
    case WorkKind::kFeedOnce: return "FEED_ONCE";
    case WorkKind::kStore: return "STORE";
    case WorkKind::kFetch: return "FETCH";
    case WorkKind::kDirectivePosition: return "DIRECTIVE_POSITION";
    case WorkKind::kDirectiveWait: return "DIRECTIVE_WAIT";
    case WorkKind::kDirectivePickup: return "DIRECTIVE_PICKUP";
    case WorkKind::kDirectiveDrop: return "DIRECTIVE_DROP";
    case WorkKind::kDirectivePlace: return "DIRECTIVE_PLACE";
    case WorkKind::kDirectivePlant: return "DIRECTIVE_PLANT";
    case WorkKind::kDirectiveWater: return "DIRECTIVE_WATER";
    case WorkKind::kDirectiveHarvest: return "DIRECTIVE_HARVEST";
    case WorkKind::kDirectiveFertilize: return "DIRECTIVE_FERTILIZE";
    case WorkKind::kDirectiveDig: return "DIRECTIVE_DIG";
    case WorkKind::kDirectiveBuildCoop: return "DIRECTIVE_BUILD_COOP";
    case WorkKind::kDirectiveBuildPasture: return "DIRECTIVE_BUILD_PASTURE";
    case WorkKind::kDirectiveFeed: return "DIRECTIVE_FEED";
    case WorkKind::kDirectiveCollectFertilizer:
      return "DIRECTIVE_COLLECT_FERTILIZER";
    case WorkKind::kDirectiveCare: return "DIRECTIVE_CARE";
  }
  return "HARVEST";
}

const char* StatusName(Status status) {
  switch (status) {
    case Status::kEmpty: return "EMPTY";
    case Status::kPending: return "PENDING";
    case Status::kRunning: return "RUNNING";
    case Status::kBlocked: return "BLOCKED";
    case Status::kAtRisk: return "AT_RISK";
    case Status::kSatisfied: return "SATISFIED";
    case Status::kFailed: return "FAILED";
  }
  return "EMPTY";
}

const char* BlockReasonName(BlockReason reason) {
  switch (reason) {
    case BlockReason::kNone: return "NONE";
    case BlockReason::kLandLocked: return "LAND_LOCKED";
    case BlockReason::kConflictingAsset: return "CONFLICTING_ASSET";
    case BlockReason::kSeedShortfall: return "SEED_SHORTFALL";
    case BlockReason::kAnimalShortfall: return "ANIMAL_SHORTFALL";
    case BlockReason::kWheatShortfall: return "WHEAT_SHORTFALL";
    case BlockReason::kFertilizerShortfall: return "FERTILIZER_SHORTFALL";
    case BlockReason::kNoEligibleUnit: return "NO_ELIGIBLE_UNIT";
    case BlockReason::kShedCapacity: return "SHED_CAPACITY";
    case BlockReason::kAssetDisappeared: return "ASSET_DISAPPEARED";
    case BlockReason::kShedItemShortfall: return "SHED_ITEM_SHORTFALL";
  }
  return "NONE";
}

std::vector<std::string> CandidateFeatureNames() {
  return {"choice_kind",       "phase",          "is_ledger",
          "is_market",        "target_x",       "target_y",
          "quantity_scale",   "item_scale",     "price_over_base",
          "owned_scale",      "contract_active", "market_prefix_fill"};
}

}  // namespace kagg::intents
