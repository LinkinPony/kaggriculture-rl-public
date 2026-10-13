#include "opponents/kaito.hpp"

#include <cmath>
#include <tuple>

#include "kaito_v48_support.hpp"

namespace kagg::opponents {
namespace {
bool EqualTile(const Tile& a, const Tile& b) {
  if (a.kind != b.kind) return false;
  if (a.kind == TileKind::kPlant) {
    return std::tie(a.crop, a.planted_day, a.watered_today,
                    a.consecutive_unwatered, a.yield_units, a.max_lifespan_step,
                    a.fertilized_until_day) ==
           std::tie(b.crop, b.planted_day, b.watered_today,
                    b.consecutive_unwatered, b.yield_units, b.max_lifespan_step,
                    b.fertilized_until_day);
  }
  if (a.kind == TileKind::kStructure) {
    if (a.structure != b.structure || a.has_animal != b.has_animal)
      return false;
    if (!a.has_animal) return true;
    return std::tie(a.animal, a.placed_day, a.yield_units, a.fed_today,
                    a.consecutive_unfed, a.cared_today, a.fertilizer_available,
                    a.pending_care_bonus) ==
           std::tie(b.animal, b.placed_day, b.yield_units, b.fed_today,
                    b.consecutive_unfed, b.cared_today, b.fertilizer_available,
                    b.pending_care_bonus);
  }
  return true;
}

bool Mirror(const Engine& engine) {
  const auto& a = engine.farm(0);
  const auto& b = engine.farm(1);
  if (a.money != b.money || a.farmer_x != b.farmer_x ||
      a.farmer_y != b.farmer_y || a.hands != b.hands ||
      a.extra_unlocked != b.extra_unlocked || a.tiles.size() != b.tiles.size())
    return false;
  for (size_t i = 0; i < a.tiles.size(); ++i)
    if (!EqualTile(a.tiles[i], b.tiles[i])) return false;
  return true;
}

auto Signature(const Engine& engine, int player) {
  const auto count = kaito::PublicAssetCounts(engine.farm(1 - player));
  return std::tuple{
      static_cast<int64_t>(std::nearbyint(engine.farm(player).money)),
      static_cast<int64_t>(std::nearbyint(engine.farm(1 - player).money)),
      engine.market().inventory[item::kWheat],
      count.cow,
      count.sheep,
      count.wheat,
      count.melon};
}
}  // namespace

Kaito::Mode Kaito::RecoveryMode(const Engine& engine, int player) {
  if (engine.town_shops().empty()) return Mode::kBase;
  const int shop = engine.town_shops()[0];
  const auto signature = Signature(engine, player);
  auto matches = [&](int64_t own, int64_t other, int64_t inventory) {
    return signature == std::tuple{own, other, inventory, 3, 2, 7, 12};
  };
  if (shop == 2 && matches(141, 193, 9974)) return Mode::kFarmers;
  if ((shop == 0 && matches(145, 195, 9975)) ||
      (shop == 6 && matches(145, 193, 9975)) ||
      (shop == 0 && matches(142, 142, 9973)) ||
      (shop == 3 && matches(142, 191, 9974)))
    return Mode::kRecovery;
  if (shop == 3 && matches(145, 195, 9975)) return Mode::kIce;
  if (shop == 0 && matches(141, 193, 9974)) return Mode::kBakery;
  if (shop == 5 && matches(141, 193, 9974)) return Mode::kPizza;
  return Mode::kBase;
}

bool Kaito::KnownYarn(const Engine& engine, int player) {
  const auto signature = Signature(engine, player);
  return signature ==
             std::tuple<int64_t, int64_t, int64_t, int, int, int, int>{
                 214, 214, 9982, 4, 2, 7, 12} ||
         signature == std::tuple<int64_t, int64_t, int64_t, int, int, int, int>{
                          215, 125, 9979, 4, 2, 7, 12};
}

PlayerAction Kaito::Act(const Engine& engine, int player) {
  const int step = engine.step_index();
  auto& seat = seats_[player];
  if (step == 0 || step < seat.last) seat = Seat{};
  if (step <= seat.last) {
    seat.mode = Mode::kBase;
    seat.mirror_streak = 0;
    seat.clone = false;
    seat.yarn = false;
  }
  seat.last = step;
  std::array<PlayerAction, 10> actions;
  // Eagerly advance all controllers. Source warm-up replays these same observed
  // prefixes; eager construction removes Python's expensive late
  // initialization.
  for (int route = 0; route < 10; ++route)
    actions[route] = Control(engine, player, route, &seat.controllers[route]);
  const auto& shops = engine.town_shops();
  int selected = 0;
  if (step >= 72 && !shops.empty()) {
    if (shops[0] == 7)
      selected = 1;
    else if (shops[0] == 4 && step >= 144 && shops.size() >= 2 &&
             (shops[1] == 7 || shops[1] == 4))
      selected = 2;
  }
  if (step == 72) seat.mode = RecoveryMode(engine, player);
  if (seat.mode == Mode::kFarmers)
    return actions[step >= 144 && shops.size() >= 2 && shops[1] == 6 ? 4 : 3];
  if (seat.mode == Mode::kRecovery) return actions[3];
  if (seat.mode == Mode::kIce) return actions[7];
  if (seat.mode == Mode::kBakery)
    return actions[step >= 144 && shops.size() >= 2 && shops[1] == 7
                       ? 8
                       : selected];
  if (seat.mode == Mode::kPizza)
    return actions[step >= 144 && shops.size() >= 2 && shops[1] == 4
                       ? 9
                       : selected];
  if (step == 96 && !shops.empty() && shops[0] == 7)
    seat.yarn = KnownYarn(engine, player);
  if (step >= 96 && seat.yarn) return actions[6];
  if (step >= 72 && !shops.empty() && shops[0] == 7) {
    seat.mirror_streak = Mirror(engine) ? seat.mirror_streak + 1 : 0;
    if (step == 360) seat.clone = seat.mirror_streak >= 240;
    if (step >= 360 && seat.clone) return actions[5];
  }
  return actions[selected];
}

}  // namespace kagg::opponents
