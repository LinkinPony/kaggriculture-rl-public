// Python conversion is restricted to authenticated initialization and
// diagnostics.
#pragma once
#include <pybind11/pybind11.h>

#include "opponents/compiled/value.hpp"
namespace kagg::opponents::compiled {
Value FromPython(pybind11::handle value);
pybind11::object ToPython(const Value& value);
}  // namespace kagg::opponents::compiled
