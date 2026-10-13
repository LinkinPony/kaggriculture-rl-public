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

py::object TileToPy(const Tile& t) {
  switch (t.kind) {
    case TileKind::kEmpty:
      return py::none();
    case TileKind::kLocked:
      return py::str("LOCKED");
    case TileKind::kWeed: {
      py::dict d;
      d["kind"] = "WEED";
      return d;
    }
    case TileKind::kPlant: {
      py::dict d;
      d["kind"] = "PLANT";
      d["crop"] = kItemNames[t.crop];
      d["planted_day"] = t.planted_day;
      d["watered_today"] = t.watered_today;
      d["consecutive_unwatered"] = t.consecutive_unwatered;
      d["yield_units"] = t.yield_units;
      d["max_lifespan_step"] = t.max_lifespan_step;
      d["fertilized_until_day"] = t.fertilized_until_day;
      return d;
    }
    case TileKind::kStructure: {
      py::dict d;
      d["kind"] = (t.structure == StructureKind::kCoop) ? "COOP" : "PASTURE";
      if (t.has_animal) {
        d["animal"] = kItemNames[item::kGoose + t.animal];
        d["placed_day"] = t.placed_day;
        d["yield_units"] = t.yield_units;
        d["consecutive_unfed"] = t.consecutive_unfed;
        d["fed_today"] = t.fed_today;
        d["cared_today"] = t.cared_today;
        d["fertilizer_available"] = t.fertilizer_available;
        d["pending_care_bonus"] = t.pending_care_bonus;
      }
      return d;
    }
  }
  return py::none();
}

py::dict FarmToPy(const Farm& farm, int board_size) {
  py::dict d;
  d["money"] = farm.money;
  py::list tiles;
  for (int y = 0; y < board_size; ++y) {
    py::list row;
    for (int x = 0; x < board_size; ++x) row.append(TileToPy(farm.tiles[y * board_size + x]));
    tiles.append(row);
  }
  d["tiles"] = tiles;
  py::list farmer;
  farmer.append(farm.farmer_x);
  farmer.append(farm.farmer_y);
  d["farmer"] = farmer;
  py::list hands;
  for (const auto& [hx, hy] : farm.hands) {
    py::list pos;
    pos.append(hx);
    pos.append(hy);
    hands.append(pos);
  }
  d["hands"] = hands;
  py::list quads;
  quads.append(kQuadrantNames[0]);
  for (int i = 0; i < farm.extra_unlocked; ++i) quads.append(kQuadrantNames[kLandOrder[i]]);
  d["unlocked_quadrants"] = quads;
  d["hires_today"] = farm.hires_today;
  return d;
}

py::dict PrivateToPy(const PrivateState& priv) {
  py::dict d;
  py::dict shed;
  for (int i = 0; i < kNumItems; ++i) shed[kItemNames[i]] = priv.shed[i];
  d["shed"] = shed;
  py::dict seeds;
  for (int i = 0; i < kNumCrops; ++i) seeds[kItemNames[i]] = priv.seeds[i];
  d["seeds"] = seeds;
  py::list inventories;
  for (const Inventory& inv : priv.inventories) {
    py::dict inv_d;
    for (const auto& [itm, n] : inv.items) inv_d[kItemNames[itm]] = n;
    inventories.append(inv_d);
  }
  d["inventories"] = inventories;
  return d;
}

Tile ParseTile(py::handle h) {
  if (h.is_none()) return Tile{};
  if (py::isinstance<py::str>(h)) return MakeLocked();  // "LOCKED"
  const auto d = py::reinterpret_borrow<py::dict>(h);
  const auto kind = py::cast<std::string>(d["kind"]);
  if (kind == "WEED") return MakeWeed();
  if (kind == "PLANT") {
    Tile t;
    t.kind = TileKind::kPlant;
    t.crop = LookupItem(py::cast<std::string>(d["crop"]), kNumCrops);
    t.planted_day = py::cast<int>(d["planted_day"]);
    t.watered_today = py::cast<bool>(d["watered_today"]);
    t.consecutive_unwatered = py::cast<int>(d["consecutive_unwatered"]);
    t.yield_units = py::cast<int>(d["yield_units"]);
    t.max_lifespan_step = py::cast<int>(d["max_lifespan_step"]);
    t.fertilized_until_day = py::cast<int>(d["fertilized_until_day"]);
    return t;
  }
  // COOP / PASTURE
  Tile t = MakeBareStructure(kind == "COOP" ? StructureKind::kCoop : StructureKind::kPasture);
  if (d.contains("animal") && !d["animal"].is_none()) {
    t.has_animal = true;
    t.animal = LookupItem(py::cast<std::string>(d["animal"]), kNumItems) - item::kGoose;
    t.placed_day = py::cast<int>(d["placed_day"]);
    t.yield_units = py::cast<int>(d["yield_units"]);
    t.consecutive_unfed = py::cast<int>(d["consecutive_unfed"]);
    t.fed_today = py::cast<bool>(d["fed_today"]);
    t.cared_today = py::cast<bool>(d["cared_today"]);
    t.fertilizer_available = py::cast<bool>(d["fertilizer_available"]);
    t.pending_care_bonus = py::cast<int>(d["pending_care_bonus"]);
  }
  return t;
}

Farm ParseFarm(const py::dict& d, int board_size) {
  Farm farm;
  farm.money = py::cast<double>(d["money"]);
  farm.tiles.assign(static_cast<size_t>(board_size) * board_size, Tile{});
  const auto rows = py::reinterpret_borrow<py::list>(d["tiles"]);
  for (int y = 0; y < board_size; ++y) {
    const auto row = py::reinterpret_borrow<py::list>(rows[y]);
    for (int x = 0; x < board_size; ++x) {
      farm.tiles[static_cast<size_t>(y) * board_size + x] = ParseTile(row[x]);
    }
  }
  const auto farmer = py::reinterpret_borrow<py::list>(d["farmer"]);
  farm.farmer_x = py::cast<int>(farmer[0]);
  farm.farmer_y = py::cast<int>(farmer[1]);
  for (py::handle h : py::reinterpret_borrow<py::list>(d["hands"])) {
    const auto pos = py::reinterpret_borrow<py::list>(h);
    farm.hands.emplace_back(py::cast<int>(pos[0]), py::cast<int>(pos[1]));
  }
  farm.extra_unlocked =
      static_cast<int>(py::len(d["unlocked_quadrants"])) - 1;  // engine unlock order is fixed
  farm.hires_today = py::cast<int>(d["hires_today"]);
  return farm;
}

PrivateState ParsePrivate(const py::dict& d) {
  PrivateState priv;
  const auto shed = py::reinterpret_borrow<py::dict>(d["shed"]);
  for (auto kv : shed) {
    const int it = LookupItem(py::cast<std::string>(kv.first), kNumItems);
    if (it >= 0) priv.shed[it] = py::cast<int64_t>(kv.second);
  }
  const auto seeds = py::reinterpret_borrow<py::dict>(d["seeds"]);
  for (auto kv : seeds) {
    const int c = LookupItem(py::cast<std::string>(kv.first), kNumCrops);
    if (c >= 0) priv.seeds[c] = py::cast<int64_t>(kv.second);
  }
  for (py::handle h : py::reinterpret_borrow<py::list>(d["inventories"])) {
    Inventory inv;
    for (auto kv : py::reinterpret_borrow<py::dict>(h)) {
      const int it = LookupItem(py::cast<std::string>(kv.first), kNumItems);
      if (it >= 0) inv.items.emplace_back(it, py::cast<int64_t>(kv.second));
    }
    priv.inventories.push_back(std::move(inv));
  }
  return priv;
}

py::dict ObservationToPy(const Engine& engine, int player) {
  const Config& cfg = engine.config();
  py::dict obs;
  obs["player"] = player;
  obs["step"] = engine.step_index();
  obs["day"] = engine.step_index() / cfg.turns_per_day;
  obs["hour"] = engine.step_index() % cfg.turns_per_day;
  py::list farms;
  for (int p = 0; p < 2; ++p) farms.append(FarmToPy(engine.farm(p), cfg.board_size));
  obs["farms"] = farms;
  py::dict market;
  py::dict inventory;
  py::dict prices;
  for (int i = 0; i < kNumProducts; ++i) {
    inventory[kItemNames[i]] = engine.market().inventory[i];
    prices[kItemNames[i]] = engine.market().prices[i];
  }
  market["inventory"] = inventory;
  market["prices"] = prices;
  obs["market"] = market;
  py::dict town;
  py::list shops;
  for (const int s : engine.town_shops()) shops.append(kShops[s].name);
  town["unlocked_shops"] = shops;
  obs["town"] = town;
  obs["private"] = PrivateToPy(engine.priv(player));
  return obs;
}


}  // namespace kagg::pyconv
