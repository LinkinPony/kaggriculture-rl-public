// pybind11 bindings: accept the official kaggle action/configuration dicts
// and emit observations in the official format, so Python agents and the
// parity harness can use the native engine unchanged.
//
// Malformed-input tolerance mirrors the official engine (silent no-ops),
// with one documented deviation: an unconvertible count argument becomes a
// no-op at parse time instead of raising mid-interpreter.

#include <pybind11/numpy.h>
#include <pybind11/pybind11.h>

#include <algorithm>
#include <array>
#include <cstdint>
#include <exception>
#include <iterator>
#include <limits>
#include <map>
#include <mutex>
#include <optional>
#include <numeric>
#include <string>
#include <unordered_map>
#include <vector>

#include "action_codec.hpp"
#include "action_control.hpp"
#include "actor_encoding.hpp"
#include "boatlee/runtime.hpp"
#include "opponents/runtime.hpp"
#include "capability.hpp"
#include "engine.hpp"
#include "core/engine.hpp"
#include "effects/session.hpp"
#include "intents/session.hpp"
#include "kaito_v39/runtime.hpp"
#include "kaito_v48.hpp"
#include "mugundh/runtime.hpp"
#include "parallel/batch.hpp"
#include "plans/session.hpp"
#include "planner.hpp"
#include "programs/session.hpp"
#include "py_convert.hpp"
#include "py_rng.hpp"
#include "policy_session.hpp"
#include "tasks/session.hpp"
#include "types.hpp"

namespace py = pybind11;

namespace kagg {

// Defined in actor_bindings.cpp.
void BindActorEncoding(py::module_& module);

// Defined in turn_bindings.cpp.
void BindTurn(py::module_& m);

// Defined in rules_bindings.cpp.
void BindRules(py::module_& m);

// Defined in planner_bindings.cpp.
void BindPlanner(py::module_& m);

// Defined in policy_bindings.cpp.
void BindPolicyIo(py::module_& m);



namespace {

using pyconv::ConfigToPy;
using pyconv::ObservationToPy;
using pyconv::ParseConfig;
using pyconv::ParsePlayerAction;

// --- Engine wrapper ---------------------------------------------------------


class PyDeterministicIncumbentSession {
 public:
  explicit PyDeterministicIncumbentSession(py::object configuration)
      : config_(ParseConfig(configuration)),
        planner_(config_, planner::PlannerOptions{}) {}

  PlayerAction Act(const Engine& engine, int player) {
    if (player < 0 || player > 1) {
      throw std::invalid_argument("deterministic incumbent player is invalid");
    }
    return planner_
        .Plan(engine.farm(player), engine.farm(1 - player),
              engine.priv(player), engine.market(), player,
              engine.step_index())
        .action;
  }

 private:
  Config config_;
  planner::NativePlanner planner_;
};

using IntArray =
    py::array_t<int64_t, py::array::c_style | py::array::forcecast>;

py::array_t<uint8_t> StepEngineNumericBatch(
    py::list engine_owners, IntArray tokens, IntArray quantities,
    IntArray decision_counts, IntArray unit_counts, int workers) {
  const int batch = static_cast<int>(py::len(engine_owners));
  if (batch < 1) {
    throw py::value_error("numeric engine batch cannot be empty");
  }
  if (workers < 1 || workers > 256) {
    throw py::value_error("numeric engine batch workers must be in [1, 256]");
  }
  const py::buffer_info token_info = tokens.request();
  const py::buffer_info quantity_info = quantities.request();
  const py::buffer_info decision_info = decision_counts.request();
  const py::buffer_info unit_info = unit_counts.request();
  if (token_info.ndim != 3 || token_info.shape[0] != batch ||
      token_info.shape[1] != 2 || quantity_info.ndim != 3 ||
      quantity_info.shape != token_info.shape || decision_info.ndim != 2 ||
      decision_info.shape[0] != batch || decision_info.shape[1] != 2 ||
      unit_info.ndim != 2 || unit_info.shape != decision_info.shape) {
    throw py::value_error(
        "numeric engine batch requires tokens/quantities [B,2,D] and counts "
        "[B,2]");
  }
  std::vector<Engine*> engines;
  engines.reserve(static_cast<size_t>(batch));
  for (py::handle owner : engine_owners) {
    engines.push_back(&py::cast<PyEngine&>(owner).mutable_engine());
  }
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
        std::array<PlayerAction, 2> actions;
        for (int player = 0; player < 2; ++player) {
          const int seat = environment * 2 + player;
          const int64_t decisions_value = decisions[seat];
          const int64_t units_value = units[seat];
          if (decisions_value < 0 || decisions_value > width ||
              units_value < 1 || units_value > decisions_value) {
            throw std::invalid_argument("numeric action counts are invalid");
          }
          const size_t offset = static_cast<size_t>(seat) * width;
          actions[player] = policy::DecodePlayerAction(
              token_data + offset, quantity_data + offset,
              static_cast<int>(decisions_value),
              static_cast<int>(units_value),
              engines[environment]->config().max_market_orders);
        }
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

py::array_t<uint8_t> StepEngineDeterministicIncumbentBatch(
    py::list engine_owners, IntArray candidate_players,
    py::list session_owners, IntArray tokens, IntArray quantities,
    IntArray decision_counts, IntArray unit_counts, int workers) {
  const int batch = static_cast<int>(py::len(engine_owners));
  if (batch < 1 ||
      py::len(session_owners) != static_cast<py::size_t>(batch)) {
    throw py::value_error(
        "deterministic incumbent batch inputs must be nonempty and aligned");
  }
  if (workers < 1 || workers > 256) {
    throw py::value_error(
        "deterministic incumbent batch workers must be in [1, 256]");
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
        "deterministic incumbent step requires players [B], actions "
        "[B,2,D], and counts [B,2]");
  }
  std::vector<Engine*> engines;
  std::vector<PyDeterministicIncumbentSession*> sessions;
  engines.reserve(static_cast<size_t>(batch));
  sessions.reserve(static_cast<size_t>(batch));
  for (int index = 0; index < batch; ++index) {
    engines.push_back(
        &py::cast<PyEngine&>(engine_owners[index]).mutable_engine());
    sessions.push_back(
        &py::cast<PyDeterministicIncumbentSession&>(session_owners[index]));
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
        actions[1 - candidate] = sessions[environment]->Act(
            *engines[environment], 1 - candidate);
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

py::array_t<uint8_t> StepEngineKaitoV48Batch(
    py::list engine_owners, IntArray candidate_players,
    py::list session_owners, IntArray tokens, IntArray quantities,
    IntArray decision_counts, IntArray unit_counts, int workers) {
  const int batch = static_cast<int>(py::len(engine_owners));
  if (batch < 1 ||
      py::len(session_owners) != static_cast<py::size_t>(batch)) {
    throw py::value_error("Kaito v48 batch inputs must be nonempty and aligned");
  }
  if (workers < 1 || workers > 256) {
    throw py::value_error("Kaito v48 batch workers must be in [1, 256]");
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
        "Kaito v48 step requires players [B], actions [B,2,D], and counts "
        "[B,2]");
  }
  std::vector<Engine*> engines;
  std::vector<kaito::Session*> sessions;
  engines.reserve(static_cast<size_t>(batch));
  sessions.reserve(static_cast<size_t>(batch));
  for (int index = 0; index < batch; ++index) {
    engines.push_back(
        &py::cast<PyEngine&>(engine_owners[index]).mutable_engine());
    sessions.push_back(&py::cast<kaito::Session&>(session_owners[index]));
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

py::array_t<uint8_t> StepEngineKaitoV39Batch(
    py::list engine_owners, IntArray candidate_players,
    py::list session_owners, IntArray tokens, IntArray quantities,
    IntArray decision_counts, IntArray unit_counts, int workers) {
  const int batch = static_cast<int>(py::len(engine_owners));
  if (batch < 1 ||
      py::len(session_owners) != static_cast<py::size_t>(batch)) {
    throw py::value_error("Kaito v39 batch inputs must be nonempty and aligned");
  }
  if (workers < 1 || workers > 256) {
    throw py::value_error("Kaito v39 batch workers must be in [1, 256]");
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
        "Kaito v39 step requires players [B], actions [B,2,D], and counts "
        "[B,2]");
  }
  std::vector<Engine*> engines;
  std::vector<kaito_v39::Session*> sessions;
  engines.reserve(static_cast<size_t>(batch));
  sessions.reserve(static_cast<size_t>(batch));
  for (int index = 0; index < batch; ++index) {
    engines.push_back(
        &py::cast<PyEngine&>(engine_owners[index]).mutable_engine());
    sessions.push_back(
        &py::cast<kaito_v39::Session&>(session_owners[index]));
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
        actions[1 - candidate] = sessions[environment]->Act(
            *engines[environment], 1 - candidate);
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

py::array_t<uint8_t> StepEngineMugundhV21Batch(
    py::list engine_owners, IntArray candidate_players,
    py::list session_owners, IntArray tokens, IntArray quantities,
    IntArray decision_counts, IntArray unit_counts, int workers) {
  const int batch = static_cast<int>(py::len(engine_owners));
  if (batch < 1 ||
      py::len(session_owners) != static_cast<py::size_t>(batch)) {
    throw py::value_error(
        "Mugundh v21 batch inputs must be nonempty and aligned");
  }
  if (workers < 1 || workers > 256) {
    throw py::value_error("Mugundh v21 batch workers must be in [1, 256]");
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
        "Mugundh v21 step requires players [B], actions [B,2,D], and "
        "counts [B,2]");
  }
  std::vector<Engine*> engines;
  std::vector<mugundh::Session*> sessions;
  engines.reserve(static_cast<size_t>(batch));
  sessions.reserve(static_cast<size_t>(batch));
  for (int index = 0; index < batch; ++index) {
    engines.push_back(
        &py::cast<PyEngine&>(engine_owners[index]).mutable_engine());
    sessions.push_back(
        &py::cast<mugundh::Session&>(session_owners[index]));
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

py::array_t<uint8_t> StepEngineBoatleeV21Batch(
    py::list engine_owners, IntArray candidate_players,
    py::list session_owners, IntArray tokens, IntArray quantities,
    IntArray decision_counts, IntArray unit_counts, int workers) {
  const int batch = static_cast<int>(py::len(engine_owners));
  if (batch < 1 ||
      py::len(session_owners) != static_cast<py::size_t>(batch)) {
    throw py::value_error(
        "Boatlee v21 batch inputs must be nonempty and aligned");
  }
  if (workers < 1 || workers > 256) {
    throw py::value_error("Boatlee v21 batch workers must be in [1, 256]");
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
        "Boatlee v21 step requires players [B], actions [B,2,D], and "
        "counts [B,2]");
  }
  std::vector<Engine*> engines;
  std::vector<boatlee::Session*> sessions;
  engines.reserve(static_cast<size_t>(batch));
  sessions.reserve(static_cast<size_t>(batch));
  for (int index = 0; index < batch; ++index) {
    engines.push_back(
        &py::cast<PyEngine&>(engine_owners[index]).mutable_engine());
    sessions.push_back(
        &py::cast<boatlee::Session&>(session_owners[index]));
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

// --- Capability-space policy boundary -------------------------------------

py::dict CapabilitySpec() {
  py::dict out;
  out["version"] = capability::kCapabilitySpecVersion;
  out["integer_field_count"] = capability::kIntegerFieldCount;
  out["float_field_count"] = capability::kFloatFieldCount;
  out["candidate_feature_count"] = capability::kCandidateFeatureCount;
  out["root_feature_count"] = capability::kRootFeatureCount;
  out["integer_fields"] = py::make_tuple(
      "edit_type", "object_kind", "reference", "target_bucket",
      "deadline_day_bucket", "flags");
  out["integer_vocab_sizes"] = py::make_tuple(4, 6, 12, 1024, 64, 8);
  out["float_fields"] = py::make_tuple(
      "spend_cap_over_starting_money", "price_guard_over_item_base",
      "urgency", "priority");
  out["target_bucket"] =
      "clamp(raw_absolute_target, 0, 1023); edit_mask identifies padding";
  out["deadline_day_bucket"] =
      "0=unset; otherwise 1+clamp(ceil((deadline-root_step)/turnsPerDay),0,62)";
  py::dict modes;
  modes["DIRECT_TURN"] = static_cast<int64_t>(capability::Mode::kDirectTurn);
  modes["CONTINUE"] = static_cast<int64_t>(capability::Mode::kContinue);
  modes["CANCEL"] = static_cast<int64_t>(capability::Mode::kCancel);
  modes["PATCH"] = static_cast<int64_t>(capability::Mode::kPatch);
  out["modes"] = std::move(modes);
  py::dict edits;
  edits["NONE"] = static_cast<int64_t>(capability::EditType::kNone);
  edits["ENSURE"] = static_cast<int64_t>(capability::EditType::kEnsure);
  edits["REDUCE"] = static_cast<int64_t>(capability::EditType::kReduce);
  edits["TRADE"] = static_cast<int64_t>(capability::EditType::kTrade);
  out["edit_types"] = std::move(edits);
  py::dict objects;
  objects["NONE"] = static_cast<int64_t>(capability::ObjectKind::kNone);
  objects["WORKER"] = static_cast<int64_t>(capability::ObjectKind::kWorker);
  objects["LAND"] = static_cast<int64_t>(capability::ObjectKind::kLand);
  objects["CROP"] = static_cast<int64_t>(capability::ObjectKind::kCrop);
  objects["ANIMAL"] = static_cast<int64_t>(capability::ObjectKind::kAnimal);
  objects["PRODUCT"] = static_cast<int64_t>(capability::ObjectKind::kProduct);
  out["object_kinds"] = std::move(objects);
  py::list candidate_features;
  for (const std::string& name : capability::CandidateFeatureNames()) {
    candidate_features.append(name);
  }
  out["candidate_features"] = std::move(candidate_features);
  py::list root_features;
  for (const std::string& name : capability::RootFeatureNames()) {
    root_features.append(name);
  }
  out["root_features"] = std::move(root_features);
  out["canonical_id"] =
      "uint64 FNV-1a over version and unbucketed canonical descriptor";
  return out;
}

struct CapabilityOwners {
  std::vector<capability::Session*> sessions;
  std::vector<const Engine*> engines;
  std::vector<int> players;
};

CapabilityOwners ParseCapabilityOwners(py::list session_owners,
                                       py::list engine_owners,
                                       IntArray players, int workers) {
  const int batch = static_cast<int>(py::len(session_owners));
  if (batch < 1 || py::len(engine_owners) != static_cast<py::size_t>(batch)) {
    throw py::value_error("capability batch inputs must be nonempty and aligned");
  }
  if (workers < 1 || workers > 256) {
    throw py::value_error("capability batch workers must be in [1, 256]");
  }
  const py::buffer_info player_info = players.request();
  if (player_info.ndim != 1 || player_info.shape[0] != batch) {
    throw py::value_error("capability players must have shape [B]");
  }
  const auto* player_data = static_cast<const int64_t*>(player_info.ptr);
  CapabilityOwners out;
  out.sessions.reserve(static_cast<size_t>(batch));
  out.engines.reserve(static_cast<size_t>(batch));
  out.players.reserve(static_cast<size_t>(batch));
  for (int index = 0; index < batch; ++index) {
    const int player = static_cast<int>(player_data[index]);
    if (player < 0 || player > 1) {
      throw py::value_error("capability player must be 0 or 1");
    }
    out.sessions.push_back(
        &py::cast<capability::Session&>(session_owners[index]));
    out.engines.push_back(
        &py::cast<const PyEngine&>(engine_owners[index]).raw_engine());
    out.players.push_back(player);
  }
  const int max_candidates = out.sessions.front()->max_candidates();
  const int max_edits = out.sessions.front()->max_edits();
  for (const capability::Session* session : out.sessions) {
    if (session->max_candidates() != max_candidates ||
        session->max_edits() != max_edits) {
      throw py::value_error(
          "capability sessions in one batch must use identical K and L");
    }
  }
  return out;
}

py::dict MakeCapabilityCandidates(const CapabilityOwners& owners,
                                  int workers) {
  const int batch = static_cast<int>(owners.sessions.size());
  const int candidate_count = owners.sessions.front()->max_candidates();
  const int edit_count = owners.sessions.front()->max_edits();
  py::array_t<int64_t> modes({batch, candidate_count});
  py::array_t<int64_t> integer_fields(
      {batch, candidate_count, edit_count,
       capability::kIntegerFieldCount});
  py::array_t<float> float_fields(
      {batch, candidate_count, edit_count, capability::kFloatFieldCount});
  py::array_t<uint8_t> edit_mask({batch, candidate_count, edit_count});
  py::array_t<int64_t> edit_counts({batch, candidate_count});
  py::array_t<float> candidate_features(
      {batch, candidate_count, capability::kCandidateFeatureCount});
  py::array_t<uint8_t> candidate_mask({batch, candidate_count});
  py::array_t<uint64_t> canonical_ids({batch, candidate_count});
  py::array_t<float> root_features(
      {batch, capability::kRootFeatureCount});

  std::fill_n(modes.mutable_data(), modes.size(), int64_t{0});
  std::fill_n(integer_fields.mutable_data(), integer_fields.size(), int64_t{0});
  std::fill_n(float_fields.mutable_data(), float_fields.size(), 0.0F);
  std::fill_n(edit_mask.mutable_data(), edit_mask.size(), uint8_t{0});
  std::fill_n(edit_counts.mutable_data(), edit_counts.size(), int64_t{0});
  std::fill_n(candidate_features.mutable_data(), candidate_features.size(), 0.0F);
  std::fill_n(candidate_mask.mutable_data(), candidate_mask.size(), uint8_t{0});
  std::fill_n(canonical_ids.mutable_data(), canonical_ids.size(), uint64_t{0});
  std::fill_n(root_features.mutable_data(), root_features.size(), 0.0F);

  auto* mode_data = modes.mutable_data();
  auto* integer_data = integer_fields.mutable_data();
  auto* float_data = float_fields.mutable_data();
  auto* edit_mask_data = edit_mask.mutable_data();
  auto* edit_count_data = edit_counts.mutable_data();
  auto* feature_data = candidate_features.mutable_data();
  auto* candidate_mask_data = candidate_mask.mutable_data();
  auto* id_data = canonical_ids.mutable_data();
  auto* root_data = root_features.mutable_data();
  std::exception_ptr first_error;
  std::mutex error_mutex;
  {
    py::gil_scoped_release release;
#ifdef _OPENMP
#pragma omp parallel for schedule(static) num_threads(workers)
#endif
    for (int batch_index = 0; batch_index < batch; ++batch_index) {
      try {
        capability::Session& session = *owners.sessions[batch_index];
        const Engine& engine = *owners.engines[batch_index];
        const int player = owners.players[batch_index];
        const std::vector<capability::Candidate>& candidates =
            session.Candidates(engine, player);
        const auto root =
            capability::EncodeRootFeatures(engine, player, session);
        std::copy(root.begin(), root.end(),
                  root_data + static_cast<size_t>(batch_index) *
                                  capability::kRootFeatureCount);
        for (int candidate_index = 0;
             candidate_index < static_cast<int>(candidates.size());
             ++candidate_index) {
          const capability::Candidate& candidate = candidates[candidate_index];
          const size_t candidate_offset =
              static_cast<size_t>(batch_index) * candidate_count +
              candidate_index;
          mode_data[candidate_offset] =
              static_cast<int64_t>(candidate.mode);
          edit_count_data[candidate_offset] =
              static_cast<int64_t>(candidate.edits.size());
          candidate_mask_data[candidate_offset] = candidate.valid ? 1 : 0;
          id_data[candidate_offset] = candidate.canonical_id;
          std::copy(candidate.features.begin(), candidate.features.end(),
                    feature_data + candidate_offset *
                                       capability::kCandidateFeatureCount);
          for (int edit_index = 0;
               edit_index < static_cast<int>(candidate.edits.size());
               ++edit_index) {
            const capability::Edit& edit = candidate.edits[edit_index];
            const size_t edit_offset =
                candidate_offset * edit_count + edit_index;
            edit_mask_data[edit_offset] = 1;
            int64_t* integers =
                integer_data + edit_offset * capability::kIntegerFieldCount;
            integers[0] = static_cast<int64_t>(edit.type);
            integers[1] = static_cast<int64_t>(edit.object);
            integers[2] = std::clamp<int64_t>(edit.reference, 0, 11);
            integers[3] = std::clamp<int64_t>(edit.target, 0, 1023);
            if (edit.deadline_step >= 0) {
              const int turns_per_day =
                  std::max(1, engine.config().turns_per_day);
              const int remaining = std::max<int64_t>(
                  0, edit.deadline_step - engine.step_index());
              const int days = (remaining + turns_per_day - 1) / turns_per_day;
              integers[4] = 1 + std::clamp(days, 0, 62);
            }
            integers[5] = std::clamp<int64_t>(edit.flags, 0, 7);
            float* values =
                float_data + edit_offset * capability::kFloatFieldCount;
            values[0] = static_cast<float>(
                edit.spend_cap /
                std::max<double>(1.0, engine.config().starting_money));
            double price_base = 1.0;
            if (edit.object == capability::ObjectKind::kProduct &&
                edit.reference >= 0 && edit.reference < kNumProducts) {
              price_base = engine.config()
                               .market_params[static_cast<int>(edit.reference)]
                               .base;
            }
            values[1] = static_cast<float>(
                edit.price_guard / std::max(1.0, price_base));
            values[2] = edit.urgency;
            values[3] = edit.priority;
          }
        }
      } catch (...) {
        std::lock_guard<std::mutex> lock(error_mutex);
        if (!first_error) first_error = std::current_exception();
      }
    }
  }
  if (first_error) std::rethrow_exception(first_error);
  py::dict out;
  out["mode"] = std::move(modes);
  out["int_fields"] = std::move(integer_fields);
  out["float_fields"] = float_fields;
  out["edit_values"] = float_fields;
  out["edit_mask"] = std::move(edit_mask);
  out["edit_counts"] = std::move(edit_counts);
  out["candidate_features"] = std::move(candidate_features);
  out["candidate_mask"] = candidate_mask;
  out["mask"] = candidate_mask;
  out["canonical_id"] = std::move(canonical_ids);
  out["root_features"] = std::move(root_features);
  out["version"] = capability::kCapabilitySpecVersion;
  return out;
}

py::dict CapabilityCandidatesBatch(py::list session_owners,
                                   py::list engine_owners, IntArray players,
                                   int workers) {
  return MakeCapabilityCandidates(
      ParseCapabilityOwners(session_owners, engine_owners, std::move(players),
                            workers),
      workers);
}

py::dict CapabilityActionsBatch(py::list session_owners,
                                py::list engine_owners, IntArray players,
                                int workers) {
  const CapabilityOwners owners = ParseCapabilityOwners(
      session_owners, engine_owners, std::move(players), workers);
  const int batch = static_cast<int>(owners.sessions.size());
  std::vector<capability::NumericAction> actions(static_cast<size_t>(batch));
  std::exception_ptr first_error;
  std::mutex error_mutex;
  {
    py::gil_scoped_release release;
#ifdef _OPENMP
#pragma omp parallel for schedule(static) num_threads(workers)
#endif
    for (int index = 0; index < batch; ++index) {
      try {
        actions[index] = owners.sessions[index]->Action(
            *owners.engines[index], owners.players[index]);
      } catch (...) {
        std::lock_guard<std::mutex> lock(error_mutex);
        if (!first_error) first_error = std::current_exception();
      }
    }
  }
  if (first_error) std::rethrow_exception(first_error);
  int width = 1;
  for (const capability::NumericAction& action : actions) {
    width = std::max(width, static_cast<int>(action.decision_count));
  }
  py::array_t<int64_t> tokens({batch, width});
  py::array_t<int64_t> quantities({batch, width});
  py::array_t<int64_t> decision_counts(batch);
  py::array_t<int64_t> unit_counts(batch);
  py::array_t<uint8_t> requires_direct(batch);
  std::fill_n(tokens.mutable_data(), tokens.size(), int64_t{0});
  std::fill_n(quantities.mutable_data(), quantities.size(), int64_t{0});
  for (int index = 0; index < batch; ++index) {
    const capability::NumericAction& action = actions[index];
    std::copy(action.tokens.begin(), action.tokens.end(),
              tokens.mutable_data() + static_cast<size_t>(index) * width);
    std::copy(action.quantities.begin(), action.quantities.end(),
              quantities.mutable_data() + static_cast<size_t>(index) * width);
    decision_counts.mutable_at(index) = action.decision_count;
    unit_counts.mutable_at(index) = action.unit_count;
    requires_direct.mutable_at(index) = action.requires_direct ? 1 : 0;
  }
  py::dict out;
  out["tokens"] = std::move(tokens);
  out["quantities"] = std::move(quantities);
  out["decision_counts"] = std::move(decision_counts);
  out["unit_counts"] = std::move(unit_counts);
  out["requires_direct"] = std::move(requires_direct);
  return out;
}

py::dict CapabilitySelectBatch(py::list session_owners, IntArray indices,
                               int workers) {
  const int batch = static_cast<int>(py::len(session_owners));
  if (batch < 1) {
    throw py::value_error("capability select batch cannot be empty");
  }
  if (workers < 1 || workers > 256) {
    throw py::value_error("capability batch workers must be in [1, 256]");
  }
  const py::buffer_info index_info = indices.request();
  if (index_info.ndim != 1 || index_info.shape[0] != batch) {
    throw py::value_error("capability selected indices must have shape [B]");
  }
  const auto* index_data = static_cast<const int64_t*>(index_info.ptr);
  std::vector<capability::Session*> sessions;
  sessions.reserve(static_cast<size_t>(batch));
  for (py::handle owner : session_owners) {
    sessions.push_back(&py::cast<capability::Session&>(owner));
  }
  py::array_t<int64_t> modes(batch);
  py::array_t<uint64_t> canonical_ids(batch);
  auto* mode_data = modes.mutable_data();
  auto* id_data = canonical_ids.mutable_data();
  std::exception_ptr first_error;
  std::mutex error_mutex;
  {
    py::gil_scoped_release release;
#ifdef _OPENMP
#pragma omp parallel for schedule(static) num_threads(workers)
#endif
    for (int index = 0; index < batch; ++index) {
      try {
        mode_data[index] = static_cast<int64_t>(
            sessions[index]->Select(static_cast<int>(index_data[index])));
        id_data[index] = sessions[index]->selected_canonical_id();
      } catch (...) {
        std::lock_guard<std::mutex> lock(error_mutex);
        if (!first_error) first_error = std::current_exception();
      }
    }
  }
  if (first_error) std::rethrow_exception(first_error);
  py::dict out;
  out["mode"] = std::move(modes);
  out["canonical_id"] = std::move(canonical_ids);
  return out;
}

py::array_t<uint8_t> CapabilityDecisionRequiredBatch(
    py::list session_owners, py::list engine_owners, IntArray players,
    int workers) {
  const CapabilityOwners owners = ParseCapabilityOwners(
      session_owners, engine_owners, std::move(players), workers);
  const int batch = static_cast<int>(owners.sessions.size());
  py::array_t<uint8_t> result(batch);
  auto* result_data = result.mutable_data();
  std::exception_ptr first_error;
  std::mutex error_mutex;
  {
    py::gil_scoped_release release;
#ifdef _OPENMP
#pragma omp parallel for schedule(static) num_threads(workers)
#endif
    for (int index = 0; index < batch; ++index) {
      try {
        result_data[index] = owners.sessions[index]->DecisionRequired(
                                 *owners.engines[index], owners.players[index])
                                 ? 1
                                 : 0;
      } catch (...) {
        std::lock_guard<std::mutex> lock(error_mutex);
        if (!first_error) first_error = std::current_exception();
      }
    }
  }
  if (first_error) std::rethrow_exception(first_error);
  return result;
}

void KaitoV48ActionNumericBatchInto(
    py::list engine_owners, IntArray players, py::list session_owners,
    py::array_t<int64_t, py::array::c_style> tokens,
    py::array_t<int64_t, py::array::c_style> quantities,
    py::array_t<int64_t, py::array::c_style> decision_counts,
    py::array_t<int64_t, py::array::c_style> unit_counts, int workers) {
  const int batch = static_cast<int>(py::len(engine_owners));
  if (batch < 1 || py::len(session_owners) != static_cast<py::size_t>(batch)) {
    throw py::value_error(
        "Kaito v48 action batch inputs must be nonempty and aligned");
  }
  if (workers < 1 || workers > 256) {
    throw py::value_error("Kaito v48 action workers must be in [1, 256]");
  }
  const py::buffer_info player_info = players.request();
  const py::buffer_info token_info = tokens.request();
  const py::buffer_info quantity_info = quantities.request();
  const py::buffer_info decision_info = decision_counts.request();
  const py::buffer_info unit_info = unit_counts.request();
  if (player_info.ndim != 1 || player_info.shape[0] != batch ||
      token_info.ndim != 2 || token_info.shape[0] != batch ||
      quantity_info.ndim != 2 || quantity_info.shape != token_info.shape ||
      decision_info.ndim != 1 || decision_info.shape[0] != batch ||
      unit_info.ndim != 1 || unit_info.shape[0] != batch) {
    throw py::value_error(
        "Kaito v48 action output requires players/counts [B] and action "
        "buffers [B,D]");
  }
  const auto* player_data = static_cast<const int64_t*>(player_info.ptr);
  auto* token_data = static_cast<int64_t*>(token_info.ptr);
  auto* quantity_data = static_cast<int64_t*>(quantity_info.ptr);
  auto* decision_data = static_cast<int64_t*>(decision_info.ptr);
  auto* unit_data = static_cast<int64_t*>(unit_info.ptr);
  const int width = static_cast<int>(token_info.shape[1]);
  std::vector<const Engine*> engines;
  std::vector<kaito::Session*> sessions;
  engines.reserve(static_cast<size_t>(batch));
  sessions.reserve(static_cast<size_t>(batch));
  for (int index = 0; index < batch; ++index) {
    const int player = static_cast<int>(player_data[index]);
    if (player < 0 || player > 1) {
      throw py::value_error("Kaito v48 action player must be 0 or 1");
    }
    engines.push_back(
        &py::cast<const PyEngine&>(engine_owners[index]).raw_engine());
    sessions.push_back(&py::cast<kaito::Session&>(session_owners[index]));
  }
  std::exception_ptr first_error;
  std::mutex error_mutex;
  {
    py::gil_scoped_release release;
#ifdef _OPENMP
#pragma omp parallel for schedule(static) num_threads(workers)
#endif
    for (int index = 0; index < batch; ++index) {
      try {
        const int player = static_cast<int>(player_data[index]);
        const int unit_count =
            1 + static_cast<int>(engines[index]->farm(player).hands.size());
        const size_t offset = static_cast<size_t>(index) * width;
        std::fill_n(token_data + offset, width, int64_t{0});
        std::fill_n(quantity_data + offset, width, int64_t{0});
        const PlayerAction action = sessions[index]->Act(*engines[index], player);
        decision_data[index] = policy::EncodePlayerAction(
            action, unit_count, token_data + offset, quantity_data + offset,
            width);
        unit_data[index] = unit_count;
      } catch (...) {
        std::lock_guard<std::mutex> lock(error_mutex);
        if (!first_error) first_error = std::current_exception();
      }
    }
  }
  if (first_error) std::rethrow_exception(first_error);
}

void KaitoV48RouteActionNumericBatchInto(
    py::list engine_owners, IntArray players, py::list session_owners,
    IntArray routes, py::array_t<int64_t, py::array::c_style> tokens,
    py::array_t<int64_t, py::array::c_style> quantities,
    py::array_t<int64_t, py::array::c_style> decision_counts,
    py::array_t<int64_t, py::array::c_style> unit_counts, int workers) {
  const int batch = static_cast<int>(py::len(engine_owners));
  if (batch < 1 || py::len(session_owners) != static_cast<py::size_t>(batch)) {
    throw py::value_error(
        "Kaito v48 route action batch inputs must be nonempty and aligned");
  }
  if (workers < 1 || workers > 256) {
    throw py::value_error("Kaito v48 route action workers must be in [1, 256]");
  }
  const py::buffer_info player_info = players.request();
  const py::buffer_info route_info = routes.request();
  const py::buffer_info token_info = tokens.request();
  const py::buffer_info quantity_info = quantities.request();
  const py::buffer_info decision_info = decision_counts.request();
  const py::buffer_info unit_info = unit_counts.request();
  if (player_info.ndim != 1 || player_info.shape[0] != batch ||
      route_info.ndim != 1 || route_info.shape[0] != batch ||
      token_info.ndim != 2 || token_info.shape[0] != batch ||
      quantity_info.ndim != 2 || quantity_info.shape != token_info.shape ||
      decision_info.ndim != 1 || decision_info.shape[0] != batch ||
      unit_info.ndim != 1 || unit_info.shape[0] != batch) {
    throw py::value_error(
        "Kaito v48 route action output requires players/routes/counts [B] "
        "and action buffers [B,D]");
  }
  const auto* player_data = static_cast<const int64_t*>(player_info.ptr);
  const auto* route_data = static_cast<const int64_t*>(route_info.ptr);
  auto* token_data = static_cast<int64_t*>(token_info.ptr);
  auto* quantity_data = static_cast<int64_t*>(quantity_info.ptr);
  auto* decision_data = static_cast<int64_t*>(decision_info.ptr);
  auto* unit_data = static_cast<int64_t*>(unit_info.ptr);
  const int width = static_cast<int>(token_info.shape[1]);
  std::vector<const Engine*> engines;
  std::vector<kaito::Session*> sessions;
  engines.reserve(static_cast<size_t>(batch));
  sessions.reserve(static_cast<size_t>(batch));
  for (int index = 0; index < batch; ++index) {
    const int player = static_cast<int>(player_data[index]);
    const int route = static_cast<int>(route_data[index]);
    if (player < 0 || player > 1) {
      throw py::value_error("Kaito v48 route action player must be 0 or 1");
    }
    if (route < 0 || route >= kaito::kRouteCount) {
      throw py::value_error("Kaito v48 route action route must be in [0, 5]");
    }
    engines.push_back(
        &py::cast<const PyEngine&>(engine_owners[index]).raw_engine());
    sessions.push_back(&py::cast<kaito::Session&>(session_owners[index]));
  }
  std::exception_ptr first_error;
  std::mutex error_mutex;
  {
    py::gil_scoped_release release;
#ifdef _OPENMP
#pragma omp parallel for schedule(static) num_threads(workers)
#endif
    for (int index = 0; index < batch; ++index) {
      try {
        const int player = static_cast<int>(player_data[index]);
        const int route = static_cast<int>(route_data[index]);
        const int unit_count =
            1 + static_cast<int>(engines[index]->farm(player).hands.size());
        const size_t offset = static_cast<size_t>(index) * width;
        std::fill_n(token_data + offset, width, int64_t{0});
        std::fill_n(quantity_data + offset, width, int64_t{0});
        const PlayerAction action = sessions[index]->ActRoute(
            *engines[index], player, static_cast<kaito::Route>(route));
        decision_data[index] = policy::EncodePlayerAction(
            action, unit_count, token_data + offset, quantity_data + offset,
            width);
        unit_data[index] = unit_count;
      } catch (...) {
        std::lock_guard<std::mutex> lock(error_mutex);
        if (!first_error) first_error = std::current_exception();
      }
    }
  }
  if (first_error) std::rethrow_exception(first_error);
}

#include "plans/python_boundary.inc"
#include "programs/python_boundary.inc"
#include "programs/teacher_trace.inc"
#include "tasks/python_boundary.inc"
#include "intents/python_boundary.inc"
#include "effects/python_boundary.inc"

}  // namespace
}  // namespace kagg

PYBIND11_MODULE(_revue_native, m) {
  m.doc() = "Native official-rules backend; equivalence requires external conformance evidence.";

  kagg::BindEngine(m).def(
      "policy_session", [](const kagg::PyEngine& owner, int player, int unit_limit) {
        if (player < 0 || player > 1) throw py::value_error("player must be 0 or 1");
        return kagg::MakeEnginePolicySession(owner.raw_engine(), player, unit_limit);
      }, py::arg("player"), py::arg("unit_limit"),
      "Create a numeric policy session directly from native state.");

  py::class_<kagg::PyDeterministicIncumbentSession>(
      m, "DeterministicIncumbentSession")
      .def(py::init<py::object>(), py::arg("configuration") = py::none(),
           "Create episode-local state for the deterministic incumbent.");

  py::class_<kagg::capability::Session>(m, "CapabilitySession")
      .def(py::init([](py::object configuration, int max_candidates,
                       int max_edits) {
             return std::make_unique<kagg::capability::Session>(
                 kagg::pyconv::ParseConfig(configuration), max_candidates,
                 max_edits);
           }),
           py::arg("configuration") = py::none(),
           py::arg("max_candidates") = 16, py::arg("max_edits") = 2)
      .def(
          "candidates",
          [](kagg::capability::Session& session,
             const kagg::PyEngine& owner, int player) {
            if (player < 0 || player > 1) {
              throw py::value_error("player must be 0 or 1");
            }
            kagg::CapabilityOwners owners;
            owners.sessions.push_back(&session);
            owners.engines.push_back(&owner.raw_engine());
            owners.players.push_back(player);
            py::dict batched = kagg::MakeCapabilityCandidates(owners, 1);
            py::dict out;
            constexpr std::array<const char*, 11> array_keys = {
                "mode",          "int_fields",       "float_fields",
                "edit_values",   "edit_mask",        "edit_counts",
                "candidate_features", "candidate_mask", "mask",
                "canonical_id",  "root_features",
            };
            for (const char* key : array_keys) {
              const py::object value = batched[key];
              out[key] = value.attr("__getitem__")(0);
            }
            out["version"] = kagg::capability::kCapabilitySpecVersion;
            return out;
          },
          py::arg("engine"), py::arg("player"),
          "Generate a fixed-width actor-visible capability candidate set.")
      .def(
          "select",
          [](kagg::capability::Session& session, int candidate_index) {
            return static_cast<int64_t>(session.Select(candidate_index));
          },
          py::arg("candidate_index"),
          "Select exactly one candidate from the most recently generated set.")
      .def(
          "action_numeric",
          [](kagg::capability::Session& session,
             const kagg::PyEngine& owner, int player) {
            const kagg::capability::NumericAction action =
                session.Action(owner.raw_engine(), player);
            py::array_t<int64_t> tokens(action.decision_count);
            py::array_t<int64_t> quantities(action.decision_count);
            std::copy(action.tokens.begin(), action.tokens.end(),
                      tokens.mutable_data());
            std::copy(action.quantities.begin(), action.quantities.end(),
                      quantities.mutable_data());
            py::dict out;
            out["tokens"] = std::move(tokens);
            out["quantities"] = std::move(quantities);
            out["decision_count"] = action.decision_count;
            out["unit_count"] = action.unit_count;
            out["requires_direct"] = action.requires_direct;
            return out;
          },
          py::arg("engine"), py::arg("player"),
          "Compile the selected capability to one numeric official action.")
      .def(
          "decision_required",
          [](kagg::capability::Session& session,
             const kagg::PyEngine& owner, int player) {
            return session.DecisionRequired(owner.raw_engine(), player);
          },
          py::arg("engine"), py::arg("player"))
      .def("reset", &kagg::capability::Session::Reset)
      .def_property_readonly("max_candidates",
                             &kagg::capability::Session::max_candidates)
      .def_property_readonly("max_edits",
                             &kagg::capability::Session::max_edits)
      .def_property_readonly("active", &kagg::capability::Session::active)
      .def_property_readonly(
          "selected_mode", [](const kagg::capability::Session& session) {
            return static_cast<int64_t>(session.selected_mode());
          })
      .def_property_readonly("selected_canonical_id",
                             &kagg::capability::Session::selected_canonical_id);

  m.def("capability_spec", &kagg::CapabilitySpec,
        "Return the versioned fixed-shape capability numeric ABI.");
  m.def("capability_candidates_batch", &kagg::CapabilityCandidatesBatch,
        py::arg("sessions"), py::arg("engines"), py::arg("players"),
        py::arg("workers"),
        "Generate capability candidates and actor-visible root features in "
        "one parallel native batch.");
  m.def("capability_select_batch", &kagg::CapabilitySelectBatch,
        py::arg("sessions"), py::arg("candidate_indices"),
        py::arg("workers"),
        "Apply selected candidate indices without a Python per-root loop.");
  m.def("capability_actions_batch", &kagg::CapabilityActionsBatch,
        py::arg("sessions"), py::arg("engines"), py::arg("players"),
        py::arg("workers"),
        "Compile selected capabilities into a compact numeric action batch.");
  m.def("capability_decision_required_batch",
        &kagg::CapabilityDecisionRequiredBatch, py::arg("sessions"),
        py::arg("engines"), py::arg("players"), py::arg("workers"),
        "Return the event-driven macro decision mask for a session batch.");

  py::class_<kagg::PyRandom>(m, "PyRandom")
      .def(py::init([](int64_t seed) {
             if (seed < 0) throw py::value_error("seed must be non-negative");
             return kagg::PyRandom(static_cast<kagg::uint128>(seed));
           }),
           py::arg("seed"))
      .def("random", &kagg::PyRandom::Random)
      .def("getrandbits", &kagg::PyRandom::GetRandBits, py::arg("k"))
      .def("randbelow", &kagg::PyRandom::RandBelow, py::arg("n"));

  kagg::BindActorEncoding(m);
  kagg::BindPolicyIo(m);
  kagg::opponents::Bind(m);
  kagg::boatlee::Bind(m);
  kagg::kaito_v39::Bind(m);
  kagg::kaito::Bind(m);
  kagg::mugundh::Bind(m);
  kagg::parallel::Bind(m);
  m.def(
      "kaito_v48_action",
      [](const kagg::PyEngine& owner, int player,
         kagg::kaito::Session& session) {
        if (player < 0 || player > 1) {
          throw py::value_error("player must be 0 or 1");
        }
        return kagg::pyconv::PlayerActionToPy(
            session.Act(owner.raw_engine(), player));
      },
      py::arg("engine"), py::arg("player"), py::arg("session"),
      "Evaluate Kaito v48 directly against one native engine state.");
  m.def(
      "kaito_v48_proposed_route",
      [](const kagg::PyEngine& owner, int player, int route) {
        if (route < 0 || route >= kagg::kaito::kRouteCount) {
          throw py::value_error("route must be in [0, 5]");
        }
        return static_cast<int64_t>(kagg::kaito::ProposedRoute(
            owner.raw_engine(), player, static_cast<kagg::kaito::Route>(route)));
      },
      py::arg("engine"), py::arg("player"), py::arg("route"),
      "Return the frozen Kaito v48 route proposal for one visible state.");
  m.def("engine_step_kaito_v48_batch", &kagg::StepEngineKaitoV48Batch,
        py::arg("engines"), py::arg("candidate_players"),
        py::arg("sessions"), py::arg("tokens"), py::arg("quantities"),
        py::arg("decision_counts"), py::arg("unit_counts"),
        py::arg("workers"),
        "Evaluate native Kaito v48 opponents and advance a numeric batch.");
  m.def("kaito_v48_action_numeric_batch",
        &kagg::KaitoV48ActionNumericBatchInto, py::arg("engines"),
        py::arg("players"), py::arg("sessions"), py::arg("tokens"),
        py::arg("quantities"), py::arg("decision_counts"),
        py::arg("unit_counts"), py::arg("workers"),
        "Write Kaito v48 actions into caller-owned numeric buffers without "
        "advancing the engines.");
  m.def("kaito_v48_route_action_numeric_batch",
        &kagg::KaitoV48RouteActionNumericBatchInto, py::arg("engines"),
        py::arg("players"), py::arg("sessions"), py::arg("routes"),
        py::arg("tokens"), py::arg("quantities"),
        py::arg("decision_counts"), py::arg("unit_counts"),
        py::arg("workers"),
        "Write PPO-selected Kaito v48 route actions into caller-owned "
        "numeric buffers without advancing the engines.");
  m.def(
      "kaito_v39_action",
      [](const kagg::PyEngine& owner, int player,
         kagg::kaito_v39::Session& session) {
        if (player < 0 || player > 1) {
          throw py::value_error("player must be 0 or 1");
        }
        return kagg::pyconv::PlayerActionToPy(
            session.Act(owner.raw_engine(), player));
      },
      py::arg("engine"), py::arg("player"), py::arg("session"),
      "Evaluate Kaito v39 directly against one native engine state.");
  m.def("engine_step_kaito_v39_batch", &kagg::StepEngineKaitoV39Batch,
        py::arg("engines"), py::arg("candidate_players"),
        py::arg("sessions"), py::arg("tokens"), py::arg("quantities"),
        py::arg("decision_counts"), py::arg("unit_counts"),
        py::arg("workers"),
        "Evaluate native Kaito v39 opponents and advance a numeric batch.");
  m.def(
      "mugundh_v21_action",
      [](const kagg::PyEngine& owner, int player,
         kagg::mugundh::Session& session) {
        if (player < 0 || player > 1) {
          throw py::value_error("player must be 0 or 1");
        }
        return kagg::pyconv::PlayerActionToPy(
            session.Act(owner.raw_engine(), player));
      },
      py::arg("engine"), py::arg("player"), py::arg("session"),
      "Evaluate Mugundh v21 directly against one native engine state.");
  m.def("engine_step_mugundh_v21_batch", &kagg::StepEngineMugundhV21Batch,
        py::arg("engines"), py::arg("candidate_players"),
        py::arg("sessions"), py::arg("tokens"), py::arg("quantities"),
        py::arg("decision_counts"), py::arg("unit_counts"),
        py::arg("workers"),
        "Evaluate native Mugundh v21 opponents and advance a numeric batch.");
  m.def(
      "boatlee_v21_action",
      [](const kagg::PyEngine& owner, int player,
         kagg::boatlee::Session& session) {
        if (player < 0 || player > 1) {
          throw py::value_error("player must be 0 or 1");
        }
        return kagg::pyconv::PlayerActionToPy(
            session.Act(owner.raw_engine(), player));
      },
      py::arg("engine"), py::arg("player"), py::arg("session"),
      "Evaluate Boatlee v21 directly against one native engine state.");
  m.def("engine_step_boatlee_v21_batch", &kagg::StepEngineBoatleeV21Batch,
        py::arg("engines"), py::arg("candidate_players"),
        py::arg("sessions"), py::arg("tokens"), py::arg("quantities"),
        py::arg("decision_counts"), py::arg("unit_counts"),
        py::arg("workers"),
        "Evaluate native Boatlee v21 opponents and advance a numeric batch.");
  m.def(
      "engine_policy_session_batch",
      [](py::list engines, py::list players, int unit_limit, int workers) {
        const py::ssize_t count = static_cast<py::ssize_t>(py::len(engines));
        if (count != static_cast<py::ssize_t>(py::len(players))) {
          throw py::value_error("engine policy batch inputs must be aligned");
        }
        std::vector<const kagg::Engine*> raw_engines;
        std::vector<int> raw_players;
        raw_engines.reserve(static_cast<size_t>(count));
        raw_players.reserve(static_cast<size_t>(count));
        for (py::ssize_t index = 0; index < count; ++index) {
          const auto* engine =
              py::cast<const kagg::PyEngine*>(engines[index]);
          raw_engines.push_back(&engine->raw_engine());
          raw_players.push_back(py::cast<int>(players[index]));
        }
        return kagg::MakeEnginePolicySessionBatch(
            raw_engines, raw_players, unit_limit, workers);
      },
      py::arg("engines"), py::arg("players"), py::arg("unit_limit"),
      py::arg("workers"),
      "Create and encode-ready policy sessions from native engines in parallel.");
  m.def(
      "engine_policy_turn_inputs",
      [](py::list engines, py::list players, int unit_limit, int workers) {
        const py::ssize_t count = static_cast<py::ssize_t>(py::len(engines));
        if (count != static_cast<py::ssize_t>(py::len(players))) {
          throw py::value_error("engine policy inputs must be aligned");
        }
        std::vector<const kagg::Engine*> raw_engines;
        std::vector<int> raw_players;
        raw_engines.reserve(static_cast<size_t>(count));
        raw_players.reserve(static_cast<size_t>(count));
        for (py::ssize_t index = 0; index < count; ++index) {
          const auto* engine =
              py::cast<const kagg::PyEngine*>(engines[index]);
          raw_engines.push_back(&engine->raw_engine());
          raw_players.push_back(py::cast<int>(players[index]));
        }
        return kagg::MakeEnginePolicyTurnInputs(
            raw_engines, raw_players, unit_limit, workers);
      },
      py::arg("engines"), py::arg("players"), py::arg("unit_limit"),
      py::arg("workers"),
      "Encode actor inputs and compact policy state in one parallel pass.");
  m.def(
      "engine_policy_turn_inputs_into",
      [](py::list engines, py::list players, int unit_limit, int workers,
         py::array_t<float, py::array::c_style> board,
         py::array_t<float, py::array::c_style> units,
         py::array_t<float, py::array::c_style> global,
         py::array_t<int64_t, py::array::c_style> unit_counts,
         py::array_t<int64_t, py::array::c_style> state) {
        const py::ssize_t count = static_cast<py::ssize_t>(py::len(engines));
        if (count != static_cast<py::ssize_t>(py::len(players))) {
          throw py::value_error("engine policy inputs must be aligned");
        }
        std::vector<const kagg::Engine*> raw_engines;
        std::vector<int> raw_players;
        raw_engines.reserve(static_cast<size_t>(count));
        raw_players.reserve(static_cast<size_t>(count));
        for (py::ssize_t index = 0; index < count; ++index) {
          const auto* engine =
              py::cast<const kagg::PyEngine*>(engines[index]);
          raw_engines.push_back(&engine->raw_engine());
          raw_players.push_back(py::cast<int>(players[index]));
        }
        kagg::WriteEnginePolicyTurnInputs(
            raw_engines, raw_players, unit_limit, workers, std::move(board),
            std::move(units), std::move(global), std::move(unit_counts),
            std::move(state));
      },
      py::arg("engines"), py::arg("players"), py::arg("unit_limit"),
      py::arg("workers"), py::arg("board"), py::arg("units"),
      py::arg("global_features"), py::arg("unit_counts"), py::arg("state"),
      "Encode actor inputs directly into caller-owned contiguous buffers.");
  m.def(
      "engine_policy_turn_inputs_compact_into",
      [](py::list engines, py::list players, int unit_limit, int workers,
         py::array board, py::array units,
         py::array_t<float, py::array::c_style> global,
         py::array_t<int64_t, py::array::c_style> unit_counts,
         py::array_t<int32_t, py::array::c_style> state) {
        const py::ssize_t count = static_cast<py::ssize_t>(py::len(engines));
        if (count != static_cast<py::ssize_t>(py::len(players))) {
          throw py::value_error("engine policy inputs must be aligned");
        }
        std::vector<const kagg::Engine*> raw_engines;
        std::vector<int> raw_players;
        raw_engines.reserve(static_cast<size_t>(count));
        raw_players.reserve(static_cast<size_t>(count));
        for (py::ssize_t index = 0; index < count; ++index) {
          const auto* engine =
              py::cast<const kagg::PyEngine*>(engines[index]);
          raw_engines.push_back(&engine->raw_engine());
          raw_players.push_back(py::cast<int>(players[index]));
        }
        kagg::WriteCompactEnginePolicyTurnInputs(
            raw_engines, raw_players, unit_limit, workers, std::move(board),
            std::move(units), std::move(global), std::move(unit_counts),
            std::move(state));
      },
      py::arg("engines"), py::arg("players"), py::arg("unit_limit"),
      py::arg("workers"), py::arg("board"), py::arg("units"),
      py::arg("global_features"), py::arg("unit_counts"), py::arg("state"),
      "Encode float16 board/unit features, float32 global features, and int32 "
      "policy state into rollout buffers.");
  m.def("engine_step_numeric_batch", &kagg::StepEngineNumericBatch,
        py::arg("engines"), py::arg("tokens"), py::arg("quantities"),
        py::arg("decision_counts"), py::arg("unit_counts"),
        py::arg("workers"),
        "Advance independent native engines from one batched numeric action.");
  m.def("engine_step_deterministic_incumbent_batch",
        &kagg::StepEngineDeterministicIncumbentBatch, py::arg("engines"),
        py::arg("candidate_players"), py::arg("sessions"),
        py::arg("tokens"), py::arg("quantities"),
        py::arg("decision_counts"), py::arg("unit_counts"),
        py::arg("workers"),
        "Evaluate deterministic incumbents and advance a numeric batch.");
  kagg::BindStructuredPlans(m);
  kagg::BindConditionalPrograms(m);
  kagg::BindConditionalProgramTeacherTrace(m);
  kagg::BindUnitTasks(m);
  kagg::BindIntentLedgers(m);
  kagg::BindAtomicEffects(m);
  kagg::control::BindOfficialActionControl(m);
  kagg::BindRules(m);
  kagg::BindTurn(m);
  kagg::BindPlanner(m);
}
