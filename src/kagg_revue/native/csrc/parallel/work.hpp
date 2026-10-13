// Ordered spatial jobs with native navigation and shared official transitions.
#pragma once

#include "parallel/state.hpp"

namespace kagg::parallel {

int ProgramSize(const Config& config, int units, int capacity);
void ValidateProgram(const Config& config, const int64_t* plan, int units,
                     int capacity, int quantities);
PlayerAction ExecuteProgram(const StateView& engine, int player, const int64_t* plan,
                            int capacity, int units, const std::vector<int64_t>& quantities,
                            int elapsed, std::vector<int>* cursors);

}  // namespace kagg::parallel
