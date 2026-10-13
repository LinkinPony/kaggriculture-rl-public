// Shared immutable action tapes for authenticated public notebook strategies.
#pragma once

#include <array>
#include <memory>
#include <string>
#include <vector>

#include "engine.hpp"
#include "types.hpp"

namespace kagg::opponents {

namespace compiled { struct Program; }

using Stock = std::array<int64_t, kNumItems>;
using Products = std::array<int64_t, kNumProducts>;

struct Node {
  int feature;
  int yes;
  int no;
  int route;
  double cut;
};

struct ShopStage {
  int step;
  int feature;
  double threshold;
  int left;
  int right;
};

struct Portfolio {
  std::shared_ptr<const compiled::Program> compiled_program;
  std::string kind;
  std::vector<std::vector<PlayerAction>> routes;
  std::vector<std::vector<Products>> suffix_sells;
  std::vector<std::vector<Node>> trees;
  std::vector<std::vector<int>> prefixes;
  std::vector<ShopStage> shop_stages;
  void Prepare();
  const PlayerAction& Action(int route, int step) const;
  UnitAction Unit(int route, int step, int unit) const;
  int64_t FutureSells(int route, int step, int item) const;
};

using SharedPortfolio = std::shared_ptr<const Portfolio>;

struct Repair {
  int start = -100;
  UnitAction intended;
};

struct RepairState {
  int last = -1;
  std::vector<Repair> units;
};

UnitAction& Unit(PlayerAction& action, int index);
const UnitAction& Unit(const PlayerAction& action, int index);
const Tile& UnitTile(const Engine& engine, int player, int unit);
std::pair<int, int> Position(const Farm& farm, int unit);
Products SellTotals(const PlayerAction& action);
int64_t PickupReserve(const PlayerAction& action, int item);
int64_t Total(const Stock& stock);
int64_t Carried(const PrivateState& state, int item);
int64_t Fibonacci(int index);
int ShopDemand(const std::vector<int>& shops, int item);
int Demand(const std::vector<int>& shops, int item, int step,
           int shop_interval = 4, int center_interval = 24);
void Align(const Engine& engine, int player, PlayerAction* action);
void WeedRepair(const Portfolio& portfolio, int route, const Engine& engine,
                int player, PlayerAction* action, RepairState* state);
bool MergeSale(PlayerAction* action, int item, int64_t quantity,
               bool front = false);
Stock ProjectShed(const Engine& engine, int player, const PlayerAction& action,
                  bool pickups, bool animal_place, int64_t capacity = 100,
                  int64_t minimum_quantity = 1);

}  // namespace kagg::opponents
