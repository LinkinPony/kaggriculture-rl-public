// Spatial operating contracts. No route library or teacher is used in execution.
#pragma once

#include "parallel/state.hpp"

namespace kagg::parallel {

inline constexpr int kCellFields = 4;  // replacement asset, upkeep, harvest, priority
inline constexpr int kControlFields = 5;  // workers, land, cash reserve, bank load, supply load
inline constexpr int kProductFields = 2;  // reserve, minimum sale price
inline constexpr int kContractVocabulary = 32;
inline constexpr int kReserveCount = 16;
inline constexpr int64_t kReserveValues[kReserveCount] = {
    0, 1, 2, 3, 4, 6, 8, 12, 16, 24, 32, 48, 64, 80, 96, 100};
inline constexpr double kPriceRatios[16] = {
    0, .25, .5, .75, .9, 1, 1.1, 1.2, 1.35, 1.5, 1.75, 2, 2.5, 3, 4, 8};
inline constexpr double kCashReserves[16] = {
    0, 50, 100, 200, 300, 500, 750, 1000, 1500, 2000, 3000, 4000, 6000, 8000, 12000, 20000};

int ContractSize(const Config& config);
void ValidateContract(const Config& config, const int64_t* contract, int unit_limit);
PlayerAction ExecuteContract(const StateView& engine, int player, const int64_t* contract,
                             int unit_limit);

}  // namespace kagg::parallel
