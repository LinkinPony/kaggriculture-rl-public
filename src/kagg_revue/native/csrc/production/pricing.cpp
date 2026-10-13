#include "production/pricing.hpp"

#include <algorithm>

#include "market_phase.hpp"

namespace kagg::production {
namespace {

// Smallest inventory level at or above `inventory` whose quote drops below
// `threshold`, capped; prices never rise with inventory, so bisection is exact.
int64_t UnitsUntilBelow(const Config& config, int product, int64_t inventory, double threshold) {
  if (ComputeMarketPrice(config, product, inventory) < threshold) return 0;
  int64_t low = inventory, high = inventory + kThresholdCap;
  if (ComputeMarketPrice(config, product, high) >= threshold) return kThresholdCap;
  while (high - low > 1) {
    const int64_t middle = low + (high - low) / 2;
    if (ComputeMarketPrice(config, product, middle) < threshold) {
      high = middle;
    } else {
      low = middle;
    }
  }
  return high - inventory;
}

}  // namespace

double PriceRatio(const Config& config, int product, int64_t inventory) {
  return ComputeMarketPrice(config, product, inventory) / config.market_params[product].base;
}

SellQuote QuoteSell(const Config& config, int product, int64_t inventory, int64_t stock) {
  SellQuote quote;
  const double base = config.market_params[product].base;
  const int64_t scan = std::max(kSellLadder.back(), std::min(stock, kSellScanLimit));
  double total = 0;
  int64_t level = inventory;
  size_t rung = 0;
  for (int64_t sold = 1; sold <= scan; ++sold) {
    const int64_t price = ComputeMarketPrice(config, product, level);
    total += price;
    if (price > kPriceFloor) ++level;  // floor sales leave inventory unchanged
    if (rung < kSellLadder.size() && sold == kSellLadder[rung]) {
      quote.average_ratio[rung++] = total / sold / base;
    }
    if (sold == std::min(stock, kSellScanLimit)) quote.stock_ratio = total / sold / base;
  }
  quote.until_below_75 = UnitsUntilBelow(config, product, inventory, 0.75 * base);
  quote.until_below_50 = UnitsUntilBelow(config, product, inventory, 0.5 * base);
  quote.until_floor = UnitsUntilBelow(config, product, inventory, kPriceFloor + 1);
  return quote;
}

double AverageBuyRatio(const Config& config, int product, int64_t inventory, int64_t units) {
  double total = 0;
  for (int64_t bought = 1; bought <= units; ++bought) {
    total += ComputeMarketPrice(config, product, --inventory);
  }
  return total / units / config.market_params[product].base;
}

int64_t ShopDemand(const std::vector<int>& shops, int product) {
  int64_t demand = 0;
  for (int shop : shops) {
    const auto& rule = kShops[shop];
    for (int i = 0; i < rule.n_products; ++i) {
      if (rule.products[i] == product) demand += rule.n_products == 1 ? 2 : 1;
    }
  }
  return demand;
}

double TownDrainPerDay(const Config& config, const std::vector<int>& shops, int product) {
  const double center = product != item::kFertilizer;
  return config.turns_per_day *
      (static_cast<double>(ShopDemand(shops, product)) / config.shop_sell_interval +
       center / config.center_sell_interval);
}

}  // namespace kagg::production
