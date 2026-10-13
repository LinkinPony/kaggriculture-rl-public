// Legacy callback construction is excluded from the self-play target.
#include <stdexcept>

#include "boatlee/runtime.hpp"
#include "kaito_v39/runtime.hpp"
#include "kaito_v48.hpp"
#include "mugundh/runtime.hpp"
#include "opponents/runtime.hpp"
#include "parallel/batch.hpp"

namespace kagg::parallel {
namespace {

using Actor = NativeActor;

template <typename Session>
Actor SessionActor(std::shared_ptr<Session> session) {
  return {[session](const Engine& engine, int player) {
            return session->Act(engine, player);
          },
          [session]() {
            return SessionActor(std::make_shared<Session>(*session));
          }};
}

template <typename Session>
Actor ActorFrom(py::handle handle) {
  auto* session = &py::cast<Session&>(handle);
  // The source batch retains Python ownership; forks own independent C++
  // sessions.
  return SessionActor(std::shared_ptr<Session>(session, [](Session*) {}));
}

Actor PassActor() {
  return {[](const Engine&, int) { return PlayerAction{}; },
          [] { return PassActor(); }};
}

Actor Opponent(const std::string& name, py::handle handle) {
  if (py::isinstance<opponents::Session>(handle)) {
    if (py::cast<opponents::Session&>(handle).kind() != name)
      throw std::invalid_argument("opponent identity mismatch");
    return ActorFrom<opponents::Session>(handle);
  }
  if (name == "kaito_v48") return ActorFrom<kaito::Session>(handle);
  if (name == "kaito_v39") return ActorFrom<kaito_v39::Session>(handle);
  if (name == "boatlee_v21") return ActorFrom<boatlee::Session>(handle);
  if (name == "mugundh_v21") return ActorFrom<mugundh::Session>(handle);
  if (name == "pass") return PassActor();
  throw std::invalid_argument("unknown parallel opponent: " + name);
}

}  // namespace

Batch::Batch(py::dict configuration, std::vector<int64_t> seeds,
             std::vector<int> seats, std::vector<std::string> opponent_ids,
             py::list opponents, py::list teachers, int units, int workers,
             std::vector<int64_t> quantities)
    : Batch(configuration, std::move(seeds), std::move(seats), units, workers,
            std::move(quantities)) {
  const size_t count = engines_.size();
  if ((opponent_ids.size() != 0 && opponent_ids.size() != count) ||
      opponents.size() != opponent_ids.size() ||
      (teachers.size() != 0 && teachers.size() != count)) {
    throw std::invalid_argument("invalid parallel batch construction");
  }
  for (size_t i = 0; i < count; ++i) {
    if (!opponent_ids.empty()) {
      owners_.append(opponents[i]);
      opponents_.push_back(Opponent(opponent_ids[i], opponents[i]));
    }
    if (teachers.size()) {
      owners_.append(teachers[i]);
      teachers_.push_back(ActorFrom<kaito::Session>(teachers[i]));
    }
  }
}

}  // namespace kagg::parallel
