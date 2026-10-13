// Canonical intent-ledger action space and deterministic executor.
#pragma once

#include <array>
#include <cstdint>
#include <optional>
#include <string>
#include <vector>

#include "action_codec.hpp"
#include "engine.hpp"
#include "unit_phase.hpp"

namespace kagg::intents {

inline constexpr int kSpecVersion = 4;
inline constexpr const char* kAbiVersion = "canonical-intent-ledger-v4";
inline constexpr int kCandidateFieldCount = 10;
inline constexpr int kCandidateFeatureCount = 12;
inline constexpr int kLedgerFieldCount = 8;
inline constexpr int kStatusFieldCount = 4;
inline constexpr int kWorkFieldCount = 9;
inline constexpr int kPositionFieldCount = 4;
inline constexpr int kMarketFieldCount = 3;
// Observation-only order kind used for an explicit empty market slot.  The
// engine represents the same value as std::nullopt in PlayerAction::market.
inline constexpr int64_t kMarketSkipKind = 6;

enum class Phase : int64_t {
  kRoot = 0,
  kAssetTarget = 1,
  kAssetProfile = 2,
  kCancelAsset = 3,
  kWorkTarget = 4,
  kWorkProfile = 5,
  kCancelWork = 6,
  kPositionRole = 7,
  kPositionTarget = 8,
  kCancelPosition = 9,
  kStoreItem = 10,
  kStoreQuantity = 11,
  kStorePriority = 12,
  kMarketQuantity = 13,
  kFetchUnit = 14,
  kFetchItem = 15,
  kFetchQuantity = 16,
  kCancelFetch = 17,
  kDirectiveUnit = 18,
  kDirectiveOperation = 19,
  kDirectiveTarget = 20,
  kDirectiveItem = 21,
  kDirectiveQuantity = 22,
  kCancelDirective = 23,
  kDone = 24,
};

enum class ChoiceKind : int64_t {
  kCommit = 0,
  kBeginAsset = 1,
  kBeginCancelAsset = 2,
  kBeginWork = 3,
  kBeginCancelWork = 4,
  kBeginPosition = 5,
  kBeginCancelPosition = 6,
  kBeginStore = 7,
  kSelectTarget = 8,
  kSetAsset = 9,
  kCancelAsset = 10,
  kAddWork = 11,
  kCancelWork = 12,
  kSelectRole = 13,
  kSetPosition = 14,
  kCancelPosition = 15,
  kSelectStoreItem = 16,
  kSelectStoreQuantity = 17,
  kAddStore = 18,
  kMarketSell = 19,
  kMarketBuySeed = 20,
  kMarketBuyProduct = 21,
  kMarketBuyAnimal = 22,
  kMarketHire = 23,
  kMarketBuyLand = 24,
  kSelectMarketQuantity = 25,
  kBeginFetch = 26,
  kBeginCancelFetch = 27,
  kSelectFetchUnit = 28,
  kSelectFetchItem = 29,
  kSetFetch = 30,
  kCancelFetch = 31,
  kBeginDirective = 32,
  kBeginCancelDirective = 33,
  kSelectDirectiveUnit = 34,
  kSelectDirectiveOperation = 35,
  kSelectDirectiveTarget = 36,
  kSelectDirectiveItem = 37,
  kSetDirective = 38,
  kCancelDirective = 39,
  kMarketSkipSlot = 40,
};

enum class AssetKind : int64_t { kNone = 0, kCrop = 1, kAnimal = 2 };

// Absence of a contract is the only UNMANAGED representation.
enum class Maintenance : int64_t {
  kNone = 0,
  kSurvive = 1,
  kYield = 2,
  kCared = 3,
};

enum class ProductCollection : int64_t { kManual = 0, kBeforeCap = 1 };
enum class FertilizerCollection : int64_t { kManual = 0, kDaily = 1 };
enum class Priority : int64_t { kLow = 0, kNormal = 1, kHigh = 2 };

enum class WorkKind : int64_t {
  kHarvest = 0,
  kFertilize = 1,
  kCareOnce = 2,
  kCollectProduct = 3,
  kCollectFertilizer = 4,
  kClear = 5,
  kWaterOnce = 6,
  kFeedOnce = 7,
  kStore = 8,
  kFetch = 9,
  kDirectivePosition = 10,
  kDirectiveWait = 11,
  kDirectivePickup = 12,
  kDirectiveDrop = 13,
  kDirectivePlace = 14,
  kDirectivePlant = 15,
  kDirectiveWater = 16,
  kDirectiveHarvest = 17,
  kDirectiveFertilize = 18,
  kDirectiveDig = 19,
  kDirectiveBuildCoop = 20,
  kDirectiveBuildPasture = 21,
  kDirectiveFeed = 22,
  kDirectiveCollectFertilizer = 23,
  kDirectiveCare = 24,
};

// Values intentionally match policy.tasks.contract.TaskOperation.  They are
// repeated here because the intent ledger is a standalone native ABI.
enum class DirectiveOperation : int64_t {
  kPosition = 1,
  kWait = 2,
  kPickup = 3,
  kDrop = 4,
  kPlace = 5,
  kPlant = 6,
  kWater = 7,
  kHarvest = 8,
  kFertilize = 9,
  kDig = 10,
  kBuildCoop = 11,
  kBuildPasture = 12,
  kFeed = 13,
  kCollectFertilizer = 14,
  kCare = 15,
};

enum class PositionRole : int64_t { kFarmer = 0, kAnyHand = 1 };

enum class Status : int64_t {
  kEmpty = 0,
  kPending = 1,
  kRunning = 2,
  kBlocked = 3,
  kAtRisk = 4,
  kSatisfied = 5,
  kFailed = 6,
};

enum class BlockReason : int64_t {
  kNone = 0,
  kLandLocked = 1,
  kConflictingAsset = 2,
  kSeedShortfall = 3,
  kAnimalShortfall = 4,
  kWheatShortfall = 5,
  kFertilizerShortfall = 6,
  kNoEligibleUnit = 7,
  kShedCapacity = 8,
  kAssetDisappeared = 9,
  kShedItemShortfall = 10,
};

struct AssetContract {
  bool active = false;
  AssetKind kind = AssetKind::kNone;
  int item = -1;  // Crop index, or full item index for an animal.
  Maintenance maintenance = Maintenance::kNone;
  ProductCollection product_collection = ProductCollection::kManual;
  FertilizerCollection fertilizer_collection =
      FertilizerCollection::kManual;
  Priority priority = Priority::kNormal;
  bool bound = false;
  int generation_stamp = -1;
};

struct WorkOrder {
  WorkKind kind = WorkKind::kHarvest;
  int target = -1;
  int item = -1;
  int64_t quantity = 0;
  Priority priority = Priority::kNormal;
  int dispatched_step = -1;
  TileKind expected_tile_kind = TileKind::kEmpty;
  int expected_item = -1;
  int expected_generation = -1;
};

struct PositionIntent {
  bool active = false;
  PositionRole role = PositionRole::kFarmer;
  int target = -1;
  Priority priority = Priority::kNormal;
};

struct FetchIntent {
  bool active = false;
  int unit = -1;
  int item = -1;
  int64_t quantity = 0;
};

struct UnitDirective {
  bool active = false;
  int unit = -1;
  DirectiveOperation operation = DirectiveOperation::kPosition;
  int target = -1;
  int item = -1;
  int64_t quantity = 0;
  int day = -1;
};

struct Candidate {
  ChoiceKind kind = ChoiceKind::kCommit;
  // kind, target, item, maintenance, product collection, fertilizer
  // collection, priority, exact quantity, one-based unit (zero means absent),
  // and explicit unit-directive operation (zero means absent).
  std::array<int64_t, kCandidateFieldCount> fields{};
  std::array<float, kCandidateFeatureCount> features{};
  uint64_t canonical_id = 0;
};

struct Observation {
  Phase phase = Phase::kRoot;
  std::vector<Candidate> candidates;
  std::vector<std::array<int64_t, kLedgerFieldCount>> ledger;
  std::vector<std::array<int64_t, kStatusFieldCount>> status;
  std::vector<std::array<int64_t, static_cast<int>(WorkKind::kStore)>>
      work_priorities;
  std::vector<std::array<int64_t, kWorkFieldCount>> work_orders;
  std::array<std::array<int64_t, kPositionFieldCount>, 2> positions{};
  std::vector<std::array<int64_t, kMarketFieldCount>> market_prefix;
};

struct NumericAction {
  std::vector<int64_t> tokens;
  std::vector<int64_t> quantities;
  int64_t decision_count = 0;
  int64_t unit_count = 1;
};

struct DeviceAuxiliary {
  // Status/reason exposed when a draft asset is inactive.  The normal
  // observation surface cannot recover this after an active contract is
  // cancelled inside a device-resident transaction.
  std::vector<std::array<int64_t, 2>> inactive_status;
  // Whether the current tile is already in the native at-risk condition.
  std::vector<int64_t> asset_risk;
};

class Session {
 public:
  explicit Session(Config config);

  Observation Observe(const Engine& engine, int player);
  Phase Select(int candidate_index);
  PlayerAction Action(const Engine& engine, int player);
  NumericAction ActionNumeric(const Engine& engine, int player);
  DeviceAuxiliary DeviceStateAuxiliary(const Engine& engine, int player);
  bool DecisionRequired(const Engine& engine, int player);
  void Reset();

  Phase phase() const { return phase_; }
  int candidate_count() const { return static_cast<int>(candidates_.size()); }
  int step() const { return turn_step_; }

 private:
  struct PendingMarket {
    OrderKind kind = OrderKind::kSell;
    int item = 0;
    int64_t upper = 0;
  };

  void BeginTurn(const Engine& engine, int player);
  void Reconcile(const Engine& engine, int player);
  void GenerateCandidates(const Engine& engine, int player);
  void GenerateRootCandidates(const Engine& engine, int player);
  void GenerateAssetProfiles(const Engine& engine, int player);
  void GenerateWorkProfiles(const Engine& engine, int player);
  void GenerateMarketCandidates(const Engine& engine, int player);
  void AddCandidate(const Engine& engine, int player, Candidate candidate);
  void ApplyChoice(const Candidate& candidate);
  PlayerAction CompileAction(const Engine& engine, int player);

  int64_t AssetKey(int target) const;
  int64_t WorkKey(int target, WorkKind kind) const;
  int64_t PositionKey(PositionRole role) const;
  int64_t StoreKey(int item) const;
  int64_t FetchKey(int unit) const;
  int64_t DirectiveKey(int unit) const;
  bool ContractMatches(const AssetContract& contract, const Tile& tile) const;
  int GenerationStamp(const AssetContract& contract, const Tile& tile) const;
  bool ServiceCovers(int target, WorkKind kind, const Tile& tile) const;
  int64_t MarketQuantityUpper(const Engine& engine, int player,
                              OrderKind kind, int item) const;

  Config config_;
  std::vector<AssetContract> assets_;
  std::vector<WorkOrder> work_;
  std::array<PositionIntent, 2> positions_{};
  std::vector<FetchIntent> fetches_;
  std::vector<UnitDirective> directives_;
  std::vector<Status> terminal_asset_status_;
  std::vector<BlockReason> terminal_asset_reason_;
  std::vector<int> terminal_asset_step_;

  std::vector<AssetContract> draft_assets_;
  std::vector<WorkOrder> draft_work_;
  std::array<PositionIntent, 2> draft_positions_{};
  std::vector<FetchIntent> draft_fetches_;
  std::vector<UnitDirective> draft_directives_;
  std::vector<std::optional<MarketOrder>> market_prefix_;
  std::vector<Candidate> candidates_;

  Phase phase_ = Phase::kRoot;
  ChoiceKind pending_kind_ = ChoiceKind::kCommit;
  int pending_target_ = -1;
  PositionRole pending_role_ = PositionRole::kFarmer;
  int pending_unit_ = -1;
  DirectiveOperation pending_directive_operation_ =
      DirectiveOperation::kPosition;
  int pending_item_ = -1;
  int64_t pending_quantity_ = 0;
  TileKind pending_work_tile_kind_ = TileKind::kEmpty;
  int pending_work_item_ = -1;
  int pending_work_generation_ = -1;
  PendingMarket pending_market_;
  int64_t last_ledger_key_ = -1;
  bool market_phase_ = false;
  bool committed_ = false;
  int turn_step_ = -1;
  int player_ = -1;
  int last_action_step_ = -1;
  PlayerAction cached_action_;
};

const char* PhaseName(Phase phase);
const char* ChoiceKindName(ChoiceKind kind);
const char* WorkKindName(WorkKind kind);
const char* StatusName(Status status);
const char* BlockReasonName(BlockReason reason);
std::vector<std::string> CandidateFeatureNames();

}  // namespace kagg::intents
