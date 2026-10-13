// Canonical official-request control for one actor seat.
#pragma once

#include <pybind11/pybind11.h>

namespace kagg::control {

inline constexpr const char* kOfficialActionControlSpecVersion =
    "official-request-control-v3";
inline constexpr const char* kCandidateBasis = "canonical-request-syntax";
inline constexpr const char* kLocalMarketProjection = "no-opponent-orders";
inline constexpr const char* kProjectionRole = "diagnostic-only";

void BindOfficialActionControl(pybind11::module_& module);

}  // namespace kagg::control
