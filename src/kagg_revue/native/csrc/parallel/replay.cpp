#include "parallel/batch.hpp"

#include <array>
#include <stdexcept>
#include <vector>

#include "py_convert.hpp"

namespace kagg::parallel {

void Batch::ReplayPrefixes(py::list prefixes) {
  if (prefixes.size() != engines_.size() || transitions() != 0 ||
      !opponents_.empty() || !teachers_.empty()) {
    throw std::invalid_argument("replay requires a fresh self-play batch and one prefix per lane");
  }
  std::vector<std::vector<std::array<PlayerAction, 2>>> actions(size());
  int turns = -1;
  for (int lane = 0; lane < size(); ++lane) {
    const auto prefix = py::cast<py::list>(prefixes[lane]);
    if (turns < 0) turns = prefix.size();
    if (prefix.size() != static_cast<size_t>(turns) || turns >= config_.episode_steps - 1) {
      throw std::invalid_argument("replay prefixes must share a nonterminal boundary");
    }
    for (py::handle value : prefix) {
      const auto pair = py::cast<py::list>(value);
      if (pair.size() != 2) throw std::invalid_argument("replay turn requires both official actions");
      actions[lane].push_back({
          pyconv::ParsePlayerAction(pair[0], config_.max_market_orders),
          pyconv::ParsePlayerAction(pair[1], config_.max_market_orders)});
    }
  }
  // Parse before mutation, then commit the entire batch only after every lane succeeds.
  auto engines = engines_;
  auto history = history_;
  py::gil_scoped_release release;
  ForEach([&](int lane) {
    for (const auto& pair : actions[lane]) {
      engines[lane].Step(pair[0], pair[1]);
      history[lane].Record(engines[lane]);
    }
    for (int seat = 0; seat < 2; ++seat) {
      if (engines[lane].farm(seat).hands.size() >= static_cast<size_t>(units_)) {
        throw std::runtime_error("replay exceeds the actor unit capacity");
      }
    }
  });
  engines_.swap(engines);
  history_.swap(history);
}

}  // namespace kagg::parallel
