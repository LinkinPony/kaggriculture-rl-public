// Complete v5b supplement. Old v4 fields and the trailing legality block are unchanged.
#pragma once

#include <array>
#include <cstdint>
#include <vector>

#include "parallel/state.hpp"
#include "production/geometry.hpp"

namespace kagg::parallel { class PublicHistory; }

namespace kagg::derived {

inline constexpr char kVersion[] = "grounded-derived-context-v5b";
inline constexpr int kGlobalFeatures = 24;
inline constexpr int kBoardFeatures = 20;
inline constexpr int kUnitFeatures = 16;
inline constexpr int kProductFeatures = 96;
inline constexpr int kHorizons = 6;
using Amounts = std::array<int64_t, kNumProducts>;
using ProductRows = std::array<std::array<double, kProductFeatures>, kNumProducts>;

double Count(double value);
double Money(double value);
double Time(double value, const Config& config);
int FeatureCount(int board, int units);
std::array<int, kHorizons> Horizons(const Config& config, int step);
int64_t Ticks(int first, int last, int interval);
int64_t Drain(const Config& config, const std::vector<int>& shops, int product,
              int first, int last);
int Delivery(const Config& config, int harvest_step, int shed_distance);
double Sell(const Config& config, int product, int64_t inventory, int64_t amount);
double Buy(const Config& config, int product, int64_t inventory, int64_t amount);

struct Event {
  int step;
  int delivery;
  int product;
  int64_t amount;
  bool input;
};

struct TileForecast {
  std::vector<Event> events;
  int operations = 0;
  int feed = 0;
  int fertilizer = 0;
};

// Biological scenarios use unlimited service/resources. Delivery times are solo
// route bounds; they do not assert a jointly feasible farm-wide schedule.
TileForecast Forecast(Tile tile, const Config& config, int step, int distance_to_shed,
                      bool boosted, bool peak = false, int intervention = -1,
                      bool apply_intervention = false);

struct Timeline {
  explicit Timeline(int turns = 0) : harvest(turns), delivered(turns), input(turns) {}
  std::vector<Amounts> harvest, delivered, input;
  Amounts initial_ready{};
  int operations = 0;
  void Add(const TileForecast& forecast);
  int64_t Sum(int product, int first, int last, bool consumption = false) const;
};

Timeline FarmForecast(const Config& config, const Farm& farm,
                      const production::FarmGeometry& geometry, int step, bool boosted);

struct Settlement {
  std::vector<int64_t> inventory;
  std::array<std::vector<double>, 2> cash;
};

// Fixed scenario: retain one day of upcoming inputs, sell the remainder, buy
// shortages, then apply current-shop drain. Shared labor/storage/funding and
// unknown opponent holdings are intentionally outside this pressure scenario.
Settlement Settle(const parallel::StateView& state, int seat, int product,
                  const std::array<Timeline, 2>& timelines, const Amounts& own_shed,
                  const Amounts& own_carried, const Timeline* addition = nullptr);

struct Execution {
  std::vector<double> boards, units;
  Amounts carried{}, overflow{};
  std::array<int, 2> critical{}, travel{}, unreachable{};
  std::array<production::FarmGeometry, 2> geometry;
};

Execution ExecutionFeatures(const parallel::StateView& state, int seat, int units);
int CriticalTasks(const Tile& tile, int step, const Config& config);
int TaskDeadline(const Tile& tile, int step, const Config& config);
void ProductFeatures(const parallel::StateView& state, int seat,
                     const parallel::PublicHistory& history, const Execution& execution,
                     const std::array<std::array<Timeline, 2>, 2>& scenarios,
                     const std::array<std::array<Settlement, kNumProducts>, 2>& settlement,
                     ProductRows& rows);
std::array<double, kGlobalFeatures> GlobalFeatures(
    const parallel::StateView& state, int seat, const Execution& execution,
    const std::array<Timeline, 2>& baseline);
void Interventions(const parallel::StateView& state, const Tile& tile, int shed_distance,
                   double* row);
void InvestmentFeatures(const parallel::StateView& state, int seat,
                        const Execution& execution,
                        const std::array<std::array<Timeline, 2>, 2>& scenarios,
                        const std::array<std::array<Settlement, kNumProducts>, 2>& settlement,
                        ProductRows& rows);
void Encode(const parallel::StateView& state, int seat, const parallel::PublicHistory& history,
            int units, uint16_t* output);

}  // namespace kagg::derived
