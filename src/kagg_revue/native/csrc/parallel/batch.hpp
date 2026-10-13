// Fixed-buffer, one-handshake-per-turn actor boundary. Rules remain in Engine.
#pragma once

#include <pybind11/numpy.h>
#include <pybind11/pybind11.h>

#include <functional>
#include <memory>
#include <vector>

#include "engine.hpp"
#include "parallel/observation.hpp"

namespace kagg::parallel {

namespace py = pybind11;

struct NativeActor {
  std::function<PlayerAction(const Engine&, int)> act;
  std::function<NativeActor()> clone;
  PlayerAction operator()(const Engine& engine, int player) const {
    return act(engine, player);
  }
};

class Batch {
 public:
  Batch(py::dict configuration, std::vector<int64_t> seeds,
        std::vector<int> seats, int units, int workers,
        std::vector<int64_t> quantities);
  Batch(py::dict configuration, std::vector<int64_t> seeds,
        std::vector<int> seats, std::vector<std::string> opponent_ids,
        py::list opponents, py::list teachers, int units, int workers,
        std::vector<int64_t> quantities);
  void Observe(py::array output);
  void ObserveSelfPlay(py::array output);
  void Teacher(py::array labels);
  void Step(py::array actions);
  void Advance(py::array contracts, int turns);
  void AdvanceSelfPlay(py::array contracts, int turns);
  void AdvancePrograms(py::array plans, int turns, int capacity, bool selfplay);
  void PrepareOpponents();
  void ReplayPrefixes(py::list prefixes);
  std::unique_ptr<Batch> Fork(py::array parents) const;
  py::array_t<double> Cash() const;
  py::dict Observation(int lane, int player = -1) const;
  py::dict Action(int lane, py::array actions) const;
  py::dict ContractAction(int lane, py::array contracts, int player = -1) const;
  int completed() const;
  int64_t transitions() const;
  int features() const;
  int entity_features() const { return features() + EntityExtraFeatures(units_); }
  int slots() const;
  int step() const { return engines_.front().step_index(); }
  int size() const { return static_cast<int>(engines_.size()); }

 private:
  Batch(const Batch& source, const int64_t* parents, int count);
  void ObserveSeat(int lane, int seat, uint16_t* row) const;
  void Apply(int lane, const PlayerAction& left, const PlayerAction& right);
  PlayerAction Decode(int lane, const int64_t* actions) const;
  void Encode(int lane, const PlayerAction& action, int64_t* output) const;
  void ForEach(const std::function<void(int)>& function) const;
  PlayerAction OpponentAction(int lane);
  Config config_;
  std::vector<Engine> engines_;
  std::vector<PublicHistory> history_;
  std::vector<int> seats_;
  py::list owners_;
  std::vector<NativeActor> opponents_;
  std::vector<NativeActor> teachers_;
  int units_;
  int workers_;
  std::vector<int64_t> quantities_;
  std::vector<PlayerAction> prepared_opponents_;
  std::vector<int> prepared_steps_;
};

void Bind(py::module_& module);

}  // namespace kagg::parallel
