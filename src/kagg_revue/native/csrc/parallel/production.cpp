#include "parallel/production.hpp"

#include <algorithm>
#include <limits>
#include <stdexcept>
#include <vector>

#include "unit_phase.hpp"

namespace kagg::parallel {
namespace {

using Point = std::pair<int, int>;
struct Work {
  int cell;
  UnitAction action;
  int required = -1;
  int priority = 0;
};

int Distance(Point first, Point second) {
  return std::abs(first.first - second.first) + std::abs(first.second - second.second);
}

Point Position(const Farm& farm, int unit) {
  return unit == 0 ? Point{farm.farmer_x, farm.farmer_y} : farm.hands[unit - 1];
}

Point Shed(Point position, int board) {
  auto cells = ShedAccessTiles(board);
  return *std::min_element(cells.begin(), cells.end(), [&](Point a, Point b) {
    return Distance(position, a) < Distance(position, b);
  });
}

UnitAction Move(Point position, Point target) {
  if (position.first < target.first) return {UnitOp::kEast};
  if (position.first > target.first) return {UnitOp::kWest};
  if (position.second < target.second) return {UnitOp::kSouth};
  if (position.second > target.second) return {UnitOp::kNorth};
  return {UnitOp::kPass};
}

int64_t Held(const PrivateState& priv, int item) {
  int64_t count = priv.shed[item];
  for (const auto& inventory : priv.inventories) count += inventory.Get(item);
  return count;
}

std::vector<Work> Tasks(const Config& config, const Farm& farm, const PrivateState& priv,
                        int step, const int64_t* plan) {
  std::vector<Work> work;
  const int day = step / config.turns_per_day;
  for (int cell = 0; cell < config.board_size * config.board_size; ++cell) {
    const auto& tile = farm.tiles[cell];
    const auto* fields = plan + cell * kCellFields;
    const int target = fields[0], upkeep = fields[1], harvest = fields[2];
    const int priority = fields[3];
    auto add = [&](UnitOp op, int arg = -1, int item = -1, int urgency = 0) {
      work.push_back({cell, {op, arg, 1}, item, priority + urgency});
    };
    if (tile.kind == TileKind::kLocked) continue;
    // Retiring a line finishes its existing crop; clearing is an explicit request.
    if (target == 9) {
      if (tile.kind != TileKind::kEmpty &&
          !(tile.kind == TileKind::kStructure && tile.has_animal)) add(UnitOp::kDig);
      continue;
    }
    if (tile.kind == TileKind::kWeed) {
      if (target) add(UnitOp::kDig);
    } else if (tile.kind == TileKind::kEmpty) {
      if (target >= 1 && target <= 5 && priv.seeds[target - 1]) {
        add(UnitOp::kPlant, target - 1);
      } else if (target >= 6 && target <= 8) {
        add(target == 6 ? UnitOp::kBuildCoop : UnitOp::kBuildPasture);
      }
    } else if (tile.kind == TileKind::kPlant) {
      const auto& crop = kCrops[tile.crop];
      const int age = day - tile.planted_day;
      const bool ready = tile.yield_units > 0 && age >= crop.first_yield_day;
      const bool collect = harvest == 1 || crop.ongoing ||
          (harvest == 2 && (age >= crop.max_yield_day || tile.yield_units >= crop.max_yield)) ||
          (harvest == 3 && step + config.turns_per_day >= tile.max_lifespan_step);
      if (harvest && ready && collect) add(UnitOp::kHarvest, -1, -1, 2);
      else if (upkeep && !tile.watered_today) add(UnitOp::kWater, -1, -1, 1);
      else if (upkeep == 3 && tile.fertilized_until_day < day && Held(priv, item::kFertilizer)) {
        add(UnitOp::kFertilize, -1, item::kFertilizer);
      }
    } else if (tile.has_animal) {
      if (upkeep && !tile.fed_today) add(UnitOp::kFeed, -1, item::kWheat, 1);
      else if (upkeep >= 2 && !tile.cared_today) add(UnitOp::kCare);
      else if (upkeep >= 2 && tile.fertilizer_available) add(UnitOp::kCollectFertilizer);
      else if (harvest && tile.yield_units > 0 &&
               (harvest == 1 || tile.yield_units >= kAnimals[tile.animal].max_held ||
                harvest == 2)) add(UnitOp::kHarvest, -1, -1, 2);
    } else if (target >= 6 && target <= 8) {
      const int animal = target - 6;
      if (tile.structure != kAnimals[animal].structure) add(UnitOp::kDig);
      else if (Held(priv, item::kGoose + animal)) {
        add(UnitOp::kPlace, item::kGoose + animal, item::kGoose + animal);
      }
    }
  }
  return work;
}

void Market(const StateView& engine, int player, const Farm& farm, const PrivateState& priv,
             const int64_t* plan, int units, PlayerAction* action) {
  const auto& config = engine.config();
  const int area = config.board_size * config.board_size;
  const auto* control = plan + area * kCellFields;
  const auto* products = control + kControlFields;
  double cash = std::max(0.0, farm.money - kCashReserves[control[2]]);
  auto append = [&](OrderKind kind, int item, int64_t count, double cost = 0) {
    if (static_cast<int>(action->market.size()) >= config.max_market_orders) return;
    if (cost > 0) count = std::min(count, static_cast<int64_t>(cash / cost));
    if (count <= 0) return;
    action->market.push_back(MarketOrder{kind, item, count});
    cash -= count * cost;
  };
  for (int item = 0; item < kNumProducts; ++item) {
    const int64_t reserve = kReserveValues[products[2 * item]];
    if (engine.market().prices[item] >=
        config.market_params[item].base * kPriceRatios[products[2 * item + 1]]) {
      append(OrderKind::kSell, item, std::max<int64_t>(0, priv.shed[item] - reserve));
    }
  }
  // Explicit workforce and land targets bound expansion. Purchases implement the
  // requested production bundle, using current cash only (sales are not assumed).
  int64_t first = 1, second = 1;
  for (int i = 0; i < farm.hires_today; ++i) {
    const int64_t next = std::min<int64_t>(first + second, 1000000000);
    first = second; second = next;
  }
  int hands = farm.hands.size();
  while (hands < std::min<int>(units - 1, control[0]) &&
         static_cast<int>(action->market.size()) < config.max_market_orders) {
    const double cost = static_cast<double>(first) * config.farm_hand_cost_mult;
    if (cash < cost) break;
    append(OrderKind::kHire, 0, 1, cost);
    ++hands;
    const int64_t next = std::min<int64_t>(first + second, 1000000000);
    first = second; second = next;
  }
  for (int land = farm.extra_unlocked; land < control[1]; ++land) {
    if (cash < kLandPrices[land]) break;
    append(OrderKind::kBuyLand, 0, 1, kLandPrices[land]);
  }
  std::array<int64_t, kNumCrops> seeds{};
  std::array<int64_t, kNumAnimals> animals{};
  int hungry = 0;
  for (int cell = 0; cell < area; ++cell) {
    const auto& tile = farm.tiles[cell];
    if (tile.kind == TileKind::kLocked) continue;
    const int target = plan[cell * kCellFields];
    if ((tile.kind == TileKind::kEmpty || tile.kind == TileKind::kWeed) &&
        target >= 1 && target <= 5) ++seeds[target - 1];
    if (target >= 6 && target <= 8 &&
        !(tile.kind == TileKind::kStructure && tile.has_animal)) ++animals[target - 6];
    if (tile.has_animal && !tile.fed_today && plan[cell * kCellFields + 1]) ++hungry;
  }
  const int64_t wheat = std::max<int64_t>(hungry, kReserveValues[products[0]]) - Held(priv, item::kWheat);
  append(OrderKind::kBuyProduct, item::kWheat, wheat, config.market_params[item::kWheat].base);
  for (int crop = 0; crop < kNumCrops; ++crop) {
    append(OrderKind::kBuySeed, crop, seeds[crop] - priv.seeds[crop], kCrops[crop].seed_cost);
  }
  for (int animal = 0; animal < kNumAnimals; ++animal) {
    append(OrderKind::kBuyAnimal, animal, animals[animal] - Held(priv, item::kGoose + animal),
           kAnimals[animal].cost);
  }
}

}  // namespace

int ContractSize(const Config& config) {
  return config.board_size * config.board_size * kCellFields + kControlFields +
         kNumProducts * kProductFields;
}

void ValidateContract(const Config& config, const int64_t* contract, int units) {
  const int area = config.board_size * config.board_size;
  const int cardinalities[] = {10, 4, 4, 4};
  for (int i = 0; i < area * kCellFields; ++i) {
    if (contract[i] < 0 || contract[i] >= cardinalities[i % kCellFields]) {
      throw std::invalid_argument("invalid production cell contract");
    }
  }
  const int global[] = {units, 4, 16, 16, 16};
  for (int i = 0; i < kControlFields; ++i) {
    const int64_t value = contract[area * kCellFields + i];
    if (value < 0 || value >= global[i]) throw std::invalid_argument("invalid production control");
  }
  for (int i = area * kCellFields + kControlFields; i < ContractSize(config); ++i) {
    if (contract[i] < 0 || contract[i] >= 16) throw std::invalid_argument("invalid sale contract");
  }
}

PlayerAction ExecuteContract(const StateView& engine, int player, const int64_t* plan, int units) {
  const auto& config = engine.config();
  Farm farm = engine.farm(player);
  PrivateState priv = engine.priv(player);
  const int day = engine.step_index() / config.turns_per_day;
  const int board = config.board_size;
  const auto* control = plan + board * board * kCellFields;
  auto tasks = Tasks(config, farm, priv, engine.step_index(), plan);
  std::vector<bool> reserved(board * board, false);
  PlayerAction action;
  const int count = 1 + farm.hands.size();
  for (int unit = 0; unit < count; ++unit) {
    const Point position = Position(farm, unit);
    UnitAction selected;
    const auto& inventory = priv.inventories[unit];
    int64_t carried = 0;
    for (const auto& [item, quantity] : inventory.items) {
      if (item < item::kGoose) carried += quantity;
    }
    const int64_t bank_load = kReserveValues[control[3]];
    if (bank_load && carried >= bank_load) {
      const Point shed = Shed(position, board);
      selected = position == shed ? UnitAction{UnitOp::kDrop} : Move(position, shed);
    } else {
      int best = -1;
      int best_cost = std::numeric_limits<int>::max();
      Point destination = position;
      bool pickup = false;
      for (int i = 0; i < static_cast<int>(tasks.size()); ++i) {
        const auto& task = tasks[i];
        if (reserved[task.cell]) continue;
        Point target{task.cell % board, task.cell / board};
        const bool supply = task.required >= 0 && inventory.Get(task.required) == 0;
        int cost = Distance(position, target);
        Point next = target;
        if (supply) {
          if (!priv.shed[task.required]) continue;
          next = Shed(position, board);
          cost = Distance(position, next) + 1 + Distance(next, target);
        }
        // A deterministic travel/deadline assignment; no predicted prices or return model.
        cost = cost * 4 - task.priority * 3;
        if (cost < best_cost) { best = i; best_cost = cost; destination = next; pickup = supply; }
      }
      if (best >= 0) {
        const auto& task = tasks[best];
        reserved[task.cell] = true;
        if (position != destination) selected = Move(position, destination);
        else if (pickup) {
          selected = {UnitOp::kPickup, task.required,
                      std::max<int64_t>(1, kReserveValues[control[4]])};
        } else selected = task.action;
      }
    }
    // Shared execution reserves seeds/inventory in official unit order. No second
    // rules implementation or future opponent information enters the actor boundary.
    const auto applied = ApplyUnitAction(config, &farm, &priv, unit, selected, day);
    if (unit == 0) action.farmer = applied.actual;
    else action.hands.push_back(applied.actual);
  }
  Market(engine, player, farm, priv, plan, units, &action);
  return action;
}

}  // namespace kagg::parallel
