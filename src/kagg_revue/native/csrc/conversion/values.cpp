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

const std::unordered_map<std::string, UnitOp>& UnitOpMap() {
  static const auto* map = new std::unordered_map<std::string, UnitOp>{
      {"NORTH", UnitOp::kNorth},
      {"SOUTH", UnitOp::kSouth},
      {"EAST", UnitOp::kEast},
      {"WEST", UnitOp::kWest},
      {"PASS", UnitOp::kPass},
      {"PICKUP", UnitOp::kPickup},
      {"DROP", UnitOp::kDrop},
      {"PLACE", UnitOp::kPlace},
      {"PLANT", UnitOp::kPlant},
      {"WATER", UnitOp::kWater},
      {"HARVEST", UnitOp::kHarvest},
      {"FERTILIZE", UnitOp::kFertilize},
      {"DIG", UnitOp::kDig},
      {"BUILD_COOP", UnitOp::kBuildCoop},
      {"BUILD_PASTURE", UnitOp::kBuildPasture},
      {"FEED", UnitOp::kFeed},
      {"COLLECT_FERTILIZER", UnitOp::kCollectFertilizer},
      {"CARE", UnitOp::kCare},
  };
  return *map;
}

const std::unordered_map<std::string, int>& ItemMap() {
  static const auto* map = [] {
    auto* m = new std::unordered_map<std::string, int>;
    for (int i = 0; i < kNumItems; ++i) (*m)[kItemNames[i]] = i;
    return m;
  }();
  return *map;
}

int LookupItem(const std::string& name, int limit) {
  const auto& m = ItemMap();
  const auto it = m.find(name);
  if (it == m.end() || it->second >= limit) return -1;
  return it->second;
}

int LookupAnimal(const std::string& name) {
  const int idx = LookupItem(name, kNumItems);
  return (idx >= item::kGoose) ? idx - item::kGoose : -1;
}

// --- Parsing ----------------------------------------------------------------

// `int(x)` semantics; false on TypeError/ValueError.
bool ToInt64(py::handle h, int64_t* out) {
  PyObject* num = PyNumber_Long(h.ptr());
  if (num == nullptr) {
    PyErr_Clear();
    return false;
  }
  int overflow = 0;
  const int64_t value = PyLong_AsLongLongAndOverflow(num, &overflow);
  if (value == -1 && PyErr_Occurred()) {
    PyErr_Clear();
    Py_DECREF(num);
    return false;
  }
  Py_DECREF(num);
  if (overflow > 0) {
    *out = std::numeric_limits<int64_t>::max();
  } else if (overflow < 0) {
    *out = std::numeric_limits<int64_t>::min();
  } else {
    *out = value;
  }
  return true;
}

bool ToString(py::handle h, std::string* out) {
  if (!py::isinstance<py::str>(h)) return false;
  *out = py::cast<std::string>(h);
  return true;
}


}  // namespace kagg::pyconv
