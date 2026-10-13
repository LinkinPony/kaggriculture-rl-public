// One-parse numeric action compiler for the official Kaggle boundary.
#pragma once

#include <pybind11/numpy.h>
#include <pybind11/pybind11.h>

#include <cstdint>
#include <vector>

namespace kagg {

class Engine;

// Create the same numeric policy session directly from an in-memory engine.
// The returned Python object owns its copied turn state and does not retain an
// Engine pointer.
pybind11::object MakeEnginePolicySession(const Engine& engine, int player,
                                         int unit_limit);

// Build copied per-seat sessions in parallel and return one owning batch.
pybind11::object MakeEnginePolicySessionBatch(
    const std::vector<const Engine*>& engines, const std::vector<int>& players,
    int unit_limit, int workers);

// Fuse copied session construction, actor encoding, unit counts, and compact
// GPU state export into one GIL-free parallel pass.
pybind11::object MakeEnginePolicyTurnInputs(
    const std::vector<const Engine*>& engines, const std::vector<int>& players,
    int unit_limit, int workers);

// Write the fused turn inputs directly into caller-owned contiguous buffers.
// This permits persistent pinned host allocations at the PyTorch boundary.
void WriteEnginePolicyTurnInputs(
    const std::vector<const Engine*>& engines, const std::vector<int>& players,
    int unit_limit, int workers,
    pybind11::array_t<float, pybind11::array::c_style> board,
    pybind11::array_t<float, pybind11::array::c_style> units,
    pybind11::array_t<float, pybind11::array::c_style> global,
    pybind11::array_t<int64_t, pybind11::array::c_style> unit_counts,
    pybind11::array_t<int64_t, pybind11::array::c_style> state);

// Write bounded board/unit observations as float16, cash/market globals as
// float32, and lossless session state as int32 for the high-throughput rollout
// path. The legacy float32/int64 ABI above remains available to general callers
// and parity diagnostics.
void WriteCompactEnginePolicyTurnInputs(
    const std::vector<const Engine*>& engines,
    const std::vector<int>& players, int unit_limit, int workers,
    pybind11::array board, pybind11::array units,
    pybind11::array_t<float, pybind11::array::c_style> global,
    pybind11::array_t<int64_t, pybind11::array::c_style> unit_counts,
    pybind11::array_t<int32_t, pybind11::array::c_style> state);

void BindPolicySession(pybind11::module_& module);

}  // namespace kagg
