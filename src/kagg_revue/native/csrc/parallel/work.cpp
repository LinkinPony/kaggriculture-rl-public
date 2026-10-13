#include "parallel/work.hpp"

#include <algorithm>
#include <stdexcept>

#include "action_codec.hpp"
#include "unit_phase.hpp"

namespace kagg::parallel {
namespace {

UnitAction Move(int x, int y, int target, int board) {
  if (x < target % board) return {UnitOp::kEast};
  if (x > target % board) return {UnitOp::kWest};
  if (y < target / board) return {UnitOp::kSouth};
  if (y > target / board) return {UnitOp::kNorth};
  return {UnitOp::kPass};
}

PlayerAction ExecuteJobs(const StateView& engine, int player, const int64_t* jobs,
                         int slots, const std::vector<int64_t>& quantities,
                         int elapsed, std::vector<int>* cursors) {
  const auto& config = engine.config();
  Farm farm = engine.farm(player);
  PrivateState priv = engine.priv(player);
  const int day = engine.step_index() / config.turns_per_day;
  PlayerAction action;
  for (int unit = 0; unit < 1 + static_cast<int>(farm.hands.size()); ++unit) {
    int& cursor = (*cursors)[unit];
    UnitAction selected;
    const auto [x, y] = unit == 0 ? std::pair{farm.farmer_x, farm.farmer_y} : farm.hands[unit - 1];
    while (cursor < slots) {
      const auto* job = jobs + (unit * slots + cursor) * 4;
      if (!job[0]) break;
      const int target = job[0] - 1;
      if (x != target % config.board_size || y != target / config.board_size) {
        selected = Move(x, y, target, config.board_size);
        break;
      }
      if (job[1] == 0) { ++cursor; continue; }
      if (elapsed < job[3]) break;
      selected = policy::DecodeUnitToken(job[1], quantities[job[2]]);
      const auto& tile = farm.tiles[target];
      const bool complete =
          (selected.op == UnitOp::kWater && (tile.kind != TileKind::kPlant || tile.watered_today)) ||
          (selected.op == UnitOp::kFeed && (!tile.has_animal || tile.fed_today)) ||
          (selected.op == UnitOp::kCare && (!tile.has_animal || tile.cared_today)) ||
          (selected.op == UnitOp::kCollectFertilizer && (!tile.has_animal || !tile.fertilizer_available)) ||
          (selected.op == UnitOp::kHarvest && tile.yield_units == 0) ||
          (selected.op == UnitOp::kFertilize &&
           (tile.kind != TileKind::kPlant || !priv.inventories[unit].Get(item::kFertilizer))) ||
          (selected.op == UnitOp::kPickup && selected.arg == item::kFertilizer &&
           !priv.shed[item::kFertilizer]) ||
          (selected.op == UnitOp::kPlant && tile.kind == TileKind::kPlant && tile.crop == selected.arg) ||
          (selected.op == UnitOp::kBuildCoop && tile.kind == TileKind::kStructure) ||
          (selected.op == UnitOp::kBuildPasture && tile.kind == TileKind::kStructure);
      if (complete) { ++cursor; selected = {}; continue; }
      break;
    }
    const auto applied = ApplyUnitAction(config, &farm, &priv, unit, selected, day);
    if (cursor < slots) {
      const auto* job = jobs + (unit * slots + cursor) * 4;
      if (job[0] && job[1] && applied.actual.op == policy::DecodeUnitToken(job[1], quantities[job[2]]).op) {
        ++cursor;
      }
    }
    if (unit == 0) action.farmer = applied.actual;
    else action.hands.push_back(applied.actual);
  }
  return action;
}

}  // namespace

int ProgramSize(const Config& config, int units, int capacity) {
  return units * (capacity + 1) * 4 + capacity * config.max_market_orders * 2;
}

void ValidateProgram(const Config& config, const int64_t* plan, int units,
                     int capacity, int quantities) {
  const int work = units * (capacity + 1) * 4;
  for (int i = 0; i < work; i += 4) {
    if (plan[i] < 0 || plan[i] > config.board_size * config.board_size ||
        plan[i + 1] < 0 || plan[i + 1] >= policy::kUnitActionTokens ||
        (plan[i + 1] > 0 && plan[i + 1] < 5) || plan[i + 2] < 0 ||
        plan[i + 2] >= quantities || plan[i + 3] < 0 || plan[i + 3] >= capacity) {
      throw std::invalid_argument("invalid work order");
    }
  }
  for (int i = work; i < ProgramSize(config, units, capacity); i += 2) {
    if (plan[i] < 0 || plan[i] >= policy::kMarketActionTokens ||
        plan[i + 1] < 0 || plan[i + 1] >= quantities) {
      throw std::invalid_argument("invalid market request");
    }
  }
}

PlayerAction ExecuteProgram(const StateView& engine, int player, const int64_t* plan,
                            int capacity, int units, const std::vector<int64_t>& quantities,
                            int elapsed, std::vector<int>* cursors) {
  if (elapsed < 0 || elapsed >= capacity) throw std::invalid_argument("expired work program");
  if (static_cast<int>(engine.farm(player).hands.size()) >= units) {
    throw std::runtime_error("unit capacity exceeded");
  }
  auto action = ExecuteJobs(engine, player, plan, capacity + 1, quantities, elapsed, cursors);
  const auto& config = engine.config();
  const auto* market = plan + units * (capacity + 1) * 4 + elapsed * config.max_market_orders * 2;
  int hands = engine.farm(player).hands.size();
  for (int slot = 0; slot < config.max_market_orders; ++slot) {
    if (!market[2 * slot]) break;
    const auto order = policy::DecodeMarketToken(market[2 * slot] + policy::kUnitActionTokens,
                                                quantities[market[2 * slot + 1]]);
    if (order && order->kind == OrderKind::kHire && hands++ >= units - 1) continue;
    action.market.push_back(order);
  }
  return action;
}

}  // namespace kagg::parallel
