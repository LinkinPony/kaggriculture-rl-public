#pragma once

#include <pybind11/pybind11.h>

namespace kagg::parallel {
void BindObservation(pybind11::module_& module);
}  // namespace kagg::parallel
