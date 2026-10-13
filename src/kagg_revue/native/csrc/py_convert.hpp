// Shared Python<->native conversion helpers used by the engine, actor encoder,
// turn compiler, and deterministic planner bindings.
#pragma once

#include <pybind11/pybind11.h>

#include <string>

#include "engine.hpp"
#include "types.hpp"

namespace kagg {
namespace pyconv {

namespace py = pybind11;

// Official configuration dict (or None) -> Config. Throws on wrong types.
Config ParseConfig(py::object configuration);
py::dict ConfigToPy(const Config& configuration);

// Official action dict -> typed PlayerAction (market truncated to max_orders).
PlayerAction ParsePlayerAction(py::handle action, int max_orders);

// Typed PlayerAction -> official action dict (inverse of ParsePlayerAction).
py::dict PlayerActionToPy(const PlayerAction& action);

// Typed unit action and state fragments -> official-format Python objects.
py::list UnitActionToPy(const UnitAction& action);
py::list MarketOrderToPy(const MarketOrder& order);
py::dict FarmToPy(const Farm& farm, int board_size);
py::dict PrivateToPy(const PrivateState& priv);

// Full official observation dict for `player`.
py::dict ObservationToPy(const Engine& engine, int player);

// Official observation fragments -> native structs. Shared by the actor
// encoder, turn compiler, and deterministic fallback planner.
Tile ParseTile(py::handle h);
Farm ParseFarm(const py::dict& d, int board_size);
PrivateState ParsePrivate(const py::dict& d);

// Item name -> index below `limit`, or -1.
int LookupItem(const std::string& name, int limit);

}  // namespace pyconv
}  // namespace kagg
