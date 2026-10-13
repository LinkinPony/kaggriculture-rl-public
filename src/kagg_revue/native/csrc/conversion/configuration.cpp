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

Shape ParseShape(const std::string& name) {
  if (name == "linear") return Shape::kLinear;
  if (name == "sq") return Shape::kSq;
  if (name == "sqrt") return Shape::kSqrt;
  if (name == "log") return Shape::kLog;
  if (name == "log10") return Shape::kLog10;
  if (name == "hinge") return Shape::kHinge;
  return Shape::kLinear;  // official `_shape` falls through to `return x`
}

bool GetKey(const py::dict& d, const char* key, py::object* out) {
  if (!d.contains(key)) return false;
  py::object v = d[key];
  if (v.is_none()) return false;
  *out = v;
  return true;
}

int64_t GetInt(const py::dict& d, const char* key, int64_t fallback) {
  py::object v;
  if (!GetKey(d, key, &v)) return fallback;
  int64_t value = fallback;
  if (!ToInt64(v, &value)) throw py::value_error(std::string("invalid integer for ") + key);
  return value;
}

double GetFloat(const py::dict& d, const char* key, double fallback) {
  py::object v;
  if (!GetKey(d, key, &v)) return fallback;
  return py::cast<double>(py::float_(v));
}

Config ParseConfig(py::object configuration) {
  Config cfg;
  if (configuration.is_none()) return cfg;
  if (!py::isinstance<py::dict>(configuration)) {
    throw py::type_error("configuration must be a dict or None");
  }
  const auto d = py::reinterpret_borrow<py::dict>(configuration);
  cfg.episode_steps = static_cast<int>(GetInt(d, "episodeSteps", cfg.episode_steps));
  cfg.board_size = static_cast<int>(GetInt(d, "boardSize", cfg.board_size));
  cfg.starting_money = GetInt(d, "startingMoney", cfg.starting_money);
  cfg.max_market_orders =
      static_cast<int>(GetInt(d, "maxMarketOrdersPerTurn", cfg.max_market_orders));
  cfg.turns_per_day = static_cast<int>(GetInt(d, "turnsPerDay", cfg.turns_per_day));
  cfg.shed_capacity = GetInt(d, "shedCapacity", cfg.shed_capacity);
  cfg.weed_spawn_chance = GetFloat(d, "weedSpawnChance", cfg.weed_spawn_chance);
  cfg.shop_unlock_interval =
      static_cast<int>(GetInt(d, "townShopUnlockInterval", cfg.shop_unlock_interval));
  cfg.shop_sell_interval =
      static_cast<int>(GetInt(d, "townShopSellInterval", cfg.shop_sell_interval));
  cfg.center_sell_interval =
      static_cast<int>(GetInt(d, "townCenterSellInterval", cfg.center_sell_interval));
  cfg.farm_hand_cost_mult = GetInt(d, "farmHandCostMult", cfg.farm_hand_cost_mult);

  py::object overrides;
  if (GetKey(d, "marketParams", &overrides) && py::isinstance<py::dict>(overrides)) {
    for (auto kv : py::reinterpret_borrow<py::dict>(overrides)) {
      std::string name;
      if (!ToString(kv.first, &name)) continue;
      const int itm = LookupItem(name, kNumProducts);
      if (itm < 0 || !py::isinstance<py::dict>(kv.second)) continue;
      const auto patch = py::reinterpret_borrow<py::dict>(kv.second);
      MarketParams& p = cfg.market_params[itm];
      p.base = GetFloat(patch, "base", p.base);
      p.i0 = GetInt(patch, "I0", p.i0);
      p.t = GetFloat(patch, "T", p.t);
      py::object fn;
      std::string fn_name;
      if (GetKey(patch, "below_func", &fn) && ToString(fn, &fn_name)) {
        p.below_func = ParseShape(fn_name);
      }
      if (GetKey(patch, "above_func", &fn) && ToString(fn, &fn_name)) {
        p.above_func = ParseShape(fn_name);
      }
      p.below_target = GetFloat(patch, "below_target", p.below_target);
      p.above_target = GetFloat(patch, "above_target", p.above_target);
    }
  }
  return cfg;
}

const char* ShapeName(Shape shape) {
  switch (shape) {
    case Shape::kLinear: return "linear";
    case Shape::kSq: return "sq";
    case Shape::kSqrt: return "sqrt";
    case Shape::kLog: return "log";
    case Shape::kLog10: return "log10";
    case Shape::kHinge: return "hinge";
  }
  return "linear";
}

py::dict ConfigToPy(const Config& config) {
  py::dict out;
  out["episodeSteps"] = config.episode_steps;
  out["boardSize"] = config.board_size;
  out["startingMoney"] = config.starting_money;
  out["maxMarketOrdersPerTurn"] = config.max_market_orders;
  out["turnsPerDay"] = config.turns_per_day;
  out["shedCapacity"] = config.shed_capacity;
  out["weedSpawnChance"] = config.weed_spawn_chance;
  out["townShopUnlockInterval"] = config.shop_unlock_interval;
  out["townShopSellInterval"] = config.shop_sell_interval;
  out["townCenterSellInterval"] = config.center_sell_interval;
  out["farmHandCostMult"] = config.farm_hand_cost_mult;
  py::dict market_params;
  for (int i = 0; i < kNumProducts; ++i) {
    const MarketParams& params = config.market_params[i];
    py::dict item;
    item["base"] = params.base;
    item["I0"] = params.i0;
    item["T"] = params.t;
    item["below_func"] = ShapeName(params.below_func);
    item["below_target"] = params.below_target;
    item["above_func"] = ShapeName(params.above_func);
    item["above_target"] = params.above_target;
    market_params[kItemNames[i]] = item;
  }
  out["marketParams"] = market_params;
  return out;
}


}  // namespace kagg::pyconv
