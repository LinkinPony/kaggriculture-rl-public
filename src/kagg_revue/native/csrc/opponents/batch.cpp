// Numeric candidate stepping with native opponents, without Python callbacks.
#include <exception>
#include <mutex>
#include <unordered_set>

#include "core/engine.hpp"
#include "opponents/runtime.hpp"

namespace kagg::opponents {
namespace py = pybind11;
using IntArray =
    py::array_t<int64_t, py::array::c_style | py::array::forcecast>;

py::array_t<uint8_t> StepBatch(py::list engine_owners,
                               IntArray candidate_players,
                               py::list session_owners, IntArray tokens,
                               IntArray quantities, IntArray decision_counts,
                               IntArray unit_counts, int workers) {
  const int batch = static_cast<int>(py::len(engine_owners));
  if (batch < 1 || py::len(session_owners) != static_cast<py::size_t>(batch)) {
    throw py::value_error(
        "Native opponent batch inputs must be nonempty and aligned");
  }
  if (workers < 1 || workers > 256) {
    throw py::value_error("Native opponent batch workers must be in [1, 256]");
  }
  const py::buffer_info player_info = candidate_players.request();
  const py::buffer_info token_info = tokens.request();
  const py::buffer_info quantity_info = quantities.request();
  const py::buffer_info decision_info = decision_counts.request();
  const py::buffer_info unit_info = unit_counts.request();
  if (player_info.ndim != 1 || player_info.shape[0] != batch ||
      token_info.ndim != 3 || token_info.shape[0] != batch ||
      token_info.shape[1] != 2 || quantity_info.ndim != 3 ||
      quantity_info.shape != token_info.shape || decision_info.ndim != 2 ||
      decision_info.shape[0] != batch || decision_info.shape[1] != 2 ||
      unit_info.ndim != 2 || unit_info.shape != decision_info.shape) {
    throw py::value_error(
        "Native opponent step requires players [B], actions [B,2,D], and "
        "counts [B,2]");
  }
  std::vector<Engine*> engines;
  std::vector<Session*> sessions;
  engines.reserve(static_cast<size_t>(batch));
  sessions.reserve(static_cast<size_t>(batch));
  for (int index = 0; index < batch; ++index) {
    engines.push_back(
        &py::cast<PyEngine&>(engine_owners[index]).mutable_engine());
    sessions.push_back(&py::cast<Session&>(session_owners[index]));
  }
  if (std::unordered_set<Engine*>(engines.begin(), engines.end()).size() !=
          engines.size() ||
      std::unordered_set<Session*>(sessions.begin(), sessions.end()).size() !=
          sessions.size()) {
    throw py::value_error(
        "parallel lanes require independent engines and opponent sessions");
  }
  const auto* players = static_cast<const int64_t*>(player_info.ptr);
  const auto* token_data = static_cast<const int64_t*>(token_info.ptr);
  const auto* quantity_data = static_cast<const int64_t*>(quantity_info.ptr);
  const auto* decisions = static_cast<const int64_t*>(decision_info.ptr);
  const auto* units = static_cast<const int64_t*>(unit_info.ptr);
  const int width = static_cast<int>(token_info.shape[2]);
  py::array_t<uint8_t> done(batch);
  auto* done_data = done.mutable_data();
  std::exception_ptr first_error;
  std::mutex error_mutex;
  {
    py::gil_scoped_release release;
#ifdef _OPENMP
#pragma omp parallel for schedule(static) num_threads(workers)
#endif
    for (int environment = 0; environment < batch; ++environment) {
      try {
        const int candidate = static_cast<int>(players[environment]);
        if (candidate < 0 || candidate > 1) {
          throw std::invalid_argument("candidate player must be 0 or 1");
        }
        const int seat = environment * 2 + candidate;
        if (decisions[seat] < units[seat] || decisions[seat] > width ||
            units[seat] < 1) {
          throw std::invalid_argument("candidate numeric action is invalid");
        }
        const size_t offset = static_cast<size_t>(seat) * width;
        std::array<PlayerAction, 2> actions;
        actions[candidate] = policy::DecodePlayerAction(
            token_data + offset, quantity_data + offset,
            static_cast<int>(decisions[seat]), static_cast<int>(units[seat]),
            engines[environment]->config().max_market_orders);
        actions[1 - candidate] =
            sessions[environment]->Act(*engines[environment], 1 - candidate);
        engines[environment]->Step(actions[0], actions[1]);
        done_data[environment] = engines[environment]->done() ? 1 : 0;
      } catch (...) {
        std::lock_guard<std::mutex> lock(error_mutex);
        if (!first_error) first_error = std::current_exception();
      }
    }
  }
  if (first_error) std::rethrow_exception(first_error);
  return done;
}

void BindBatch(py::module_& module) {
  module.def("engine_step_native_opponent_batch", &StepBatch);
}

}  // namespace kagg::opponents
