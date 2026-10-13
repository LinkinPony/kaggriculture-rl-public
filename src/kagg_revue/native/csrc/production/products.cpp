#include "production/products.hpp"

#include <algorithm>
#include <cmath>

#include "production/placement.hpp"
#include "production/pricing.hpp"

namespace kagg::production {
namespace {

double Log(double value) { return std::log1p(std::max(0.0, value)) / 5.0; }

double Ratio(double value) { return std::min(value, 4.0) / 4.0; }

double Symlog(double value) { return std::copysign(std::log1p(std::abs(value)), value); }

int Until(int step, int interval) { return (interval - step % interval) % interval; }

void FillMarket(const parallel::StateView& state, int seat, const Ledger& ledger,
                const Holdings& holdings, int product, std::array<double, kProductFeatures>& row) {
  namespace f = production::product;
  const auto& config = state.config();
  const auto& params = config.market_params[product];
  const int64_t inventory = state.market().inventory[product];
  const int64_t stock = state.priv(seat).shed[product] +
      static_cast<int64_t>(holdings.carried[product]);
  const auto quote = QuoteSell(config, product, inventory, stock);
  for (size_t rung = 0; rung < kSellLadder.size(); ++rung) {
    row[f::kSellAveragePrice2 + rung] = Ratio(quote.average_ratio[rung]);
  }
  row[f::kSellAveragePriceAllStock] = stock > 0 ? Ratio(quote.stock_ratio) : 0;
  row[f::kUnitsUntilPriceBelow75] = std::log1p(quote.until_below_75) / 7.0;
  row[f::kUnitsUntilPriceBelow50] = std::log1p(quote.until_below_50) / 7.0;
  row[f::kUnitsUntilPriceFloor] = std::log1p(quote.until_floor) / 7.0;
  row[f::kPriceAfterVisibleSupply] = Ratio(PriceRatio(
      config, product,
      inventory + holdings.own_supply[product] + holdings.opponent_supply[product]));
  const double drain = TownDrainPerDay(config, state.town_shops(), product);
  row[f::kMarketGlutted] = inventory > params.i0;
  row[f::kGlutRecoveryDays] = inventory > params.i0 && drain > 0
      ? std::min((inventory - params.i0) / drain, 30.0) / 30.0 : 0;
  if (product == item::kWheat || product == item::kFertilizer) {
    row[f::kBuyAveragePrice10] = Ratio(AverageBuyRatio(config, product, inventory, 10));
    row[f::kBuyAveragePrice50] = Ratio(AverageBuyRatio(config, product, inventory, 50));
  }
  row[f::kOwnHarvestedCumulative] = Log(ledger.harvested[seat][product]);
  row[f::kOpponentHarvestedCumulative] = Log(ledger.harvested[1 - seat][product]);
  row[f::kPlayersNetMarketFlowCumulative] = Symlog(ledger.net_market_flow[product] / params.t) / 2.0;
}

}  // namespace

void FinishProducts(const parallel::StateView& state, int seat, const Ledger& ledger,
                    const Holdings& holdings, ProductRows& rows) {
  namespace f = production::product;
  const auto& config = state.config();
  const int area = config.board_size * config.board_size;
  const int step = state.step_index(), day = step / config.turns_per_day;
  const auto& priv = state.priv(seat);
  for (int product = 0; product < kNumProducts; ++product) {
    auto& row = rows[product];
    row[f::kOwnAvailableTasks] = (row[f::kOwnHarvestableTiles] + row[f::kOwnNeedsWater] +
        row[f::kOwnNeedsFeed] + row[f::kOwnUsefulCareAvailable] +
        row[f::kOwnFertilizerCollectable]) / area;
    for (int i = f::kOwnImmatureTiles; i <= f::kOwnFertilizerCollectable; ++i) row[i] /= area;
    for (int i = f::kOpponentImmatureTiles; i <= f::kOpponentExhaustedOngoingTiles; ++i) {
      row[i] /= area;
    }
    for (int i = f::kOwnHarvestableQuantity; i <= f::kOwnNextProductionOverflow; ++i) {
      row[i] = Log(row[i]);
    }
    for (int i = f::kOpponentHarvestableQuantity; i <= f::kOpponentAdditionalHarvest4Days; ++i) {
      row[i] = Log(row[i]);
    }
    int lead = -1;
    if (product < kNumCrops) {
      row[f::kUnplantedSeedsOrStoredAnimals] = Log(priv.seeds[product]);
      row[f::kEmptyCompatibleTiles] = holdings.empty / static_cast<double>(area);
      lead = kCrops[product].first_yield_day;
    } else {
      for (int animal = 0; animal < kNumAnimals; ++animal) {
        const auto& rule = kAnimals[animal];
        if (rule.product != product) continue;
        row[f::kUnplantedSeedsOrStoredAnimals] = Log(priv.shed[item::kGoose + animal]);
        row[f::kCarriedAnimals] = Log(holdings.carried[item::kGoose + animal]);
        row[f::kEmptyCompatibleTiles] =
            holdings.structures[static_cast<int>(rule.structure)] / static_cast<double>(area);
        lead = rule.first_yield_day;
      }
    }
    row[f::kTownConsumptionPerDay] = Log(TownDrainPerDay(config, state.town_shops(), product));
    int next = config.episode_steps;
    if (product != item::kFertilizer) next = Until(step, config.center_sell_interval);
    if (ShopDemand(state.town_shops(), product) > 0) {
      next = std::min(next, Until(step, config.shop_sell_interval));
    }
    row[f::kHasTownConsumptionBeforeEnd] =
        next < config.episode_steps && step + next <= config.episode_steps - 2;
    row[f::kNextTownConsumptionTurns] = row[f::kHasTownConsumptionBeforeEnd]
        ? next / static_cast<double>(config.turns_per_day) : 0;
    // Ideal placement now; travel, feeding, harvest and selling still need actions.
    row[f::kNewPlacementFirstHarvestTerminalSlack] = lead < 0 ? 0 : std::clamp(
        (config.episode_steps - 2 - (day + lead) * config.turns_per_day) /
            static_cast<double>(std::max(1, config.episode_steps - 1)), -1.0, 1.0);
    row[f::kNewPlacementTotalYield] = Log(PlacementTotal(product, config, step, false));
    row[f::kNewPlacementTotalYieldBoosted] = Log(PlacementTotal(product, config, step, true));
    FillMarket(state, seat, ledger, holdings, product, row);
  }
}

}  // namespace kagg::production
