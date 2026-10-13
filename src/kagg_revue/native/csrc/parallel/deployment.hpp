// Official-observation adapter. No opponent private state or simulation is used.
#pragma once

#include <pybind11/numpy.h>
#include <pybind11/pybind11.h>

#include "parallel/observation.hpp"

namespace kagg::parallel {

class ContractSession {
 public:
  ContractSession(pybind11::dict configuration, int units);
  void Update(pybind11::dict observation);
  void Observe(pybind11::array output) const;
  pybind11::dict Action(pybind11::array plan) const;
  void SetProgram(pybind11::array plan, int capacity, std::vector<int64_t> quantities);
  pybind11::dict ProgramAction();
  void EncodeReplay(pybind11::list steps, int seat, pybind11::array observations,
                    pybind11::array actions);

 private:
  StateView view() const;
  void WriteObservation(uint16_t* output) const;
  Config config_;
  int units_;
  int seat_ = -1;
  int step_ = -1;
  std::array<Farm, 2> farms_;
  std::array<PrivateState, 2> private_;
  MarketState market_;
  std::vector<int> shops_;
  PublicHistory history_;
  std::vector<int64_t> program_;
  std::vector<int64_t> quantities_;
  std::vector<int> cursors_;
  int capacity_ = 0;
  int program_start_ = -1;
  int action_step_ = -1;
  PlayerAction cached_action_;
};

}  // namespace kagg::parallel
