// Internal scalar/string conversions shared by configuration and action parsing.
#pragma once

#include <pybind11/pybind11.h>

#include <string>
#include <unordered_map>

#include "types.hpp"

namespace kagg::pyconv {

const std::unordered_map<std::string, UnitOp>& UnitOpMap();
bool ToInt64(pybind11::handle value, int64_t* output);
bool ToString(pybind11::handle value, std::string* output);
int LookupAnimal(const std::string& name);

}  // namespace kagg::pyconv
