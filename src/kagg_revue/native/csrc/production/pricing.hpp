// Own-order price impact on the official nonlinear market curve.
#pragma once

#include <array>
#include <cstdint>

#include "types.hpp"

namespace kagg::production {

inline constexpr std::array<int64_t, 6> kSellLadder = {2, 4, 8, 16, 32, 64};
inline constexpr int64_t kSellScanLimit = 256;
inline constexpr int64_t kThresholdCap = 1024;

struct SellQuote {
  std::array<double, kSellLadder.size()> average_ratio{};  // mean unit price / base
  double stock_ratio = 0;   // mean unit price / base when selling `stock` units (scan-capped)
  int64_t until_below_75 = 0;
  int64_t until_below_50 = 0;
  int64_t until_floor = 0;  // units absorbed before the price floor; further sells earn the floor
};

double PriceRatio(const Config& config, int product, int64_t inventory);
SellQuote QuoteSell(const Config& config, int product, int64_t inventory, int64_t stock);
double AverageBuyRatio(const Config& config, int product, int64_t inventory, int64_t units);
// Units the unlocked shops remove per shop interval, and per day including the center.
int64_t ShopDemand(const std::vector<int>& shops, int product);
double TownDrainPerDay(const Config& config, const std::vector<int>& shops, int product);

}  // namespace kagg::production
