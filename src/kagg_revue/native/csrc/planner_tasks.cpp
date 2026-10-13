#include "planner.hpp"

#include <algorithm>
#include <array>
#include <cmath>
#include <map>
#include <numeric>
#include <set>
#include <string>
#include <tuple>

namespace kagg::planner {
namespace {

constexpr int kHardPriority = 1100;

int OperationPriority(UnitOp op) {
  switch (op) {
    case UnitOp::kWater:
      return 850;
    case UnitOp::kFeed:
      return 800;
    case UnitOp::kHarvest:
      return 750;
    case UnitOp::kPlant:
      return 700;
    case UnitOp::kPlace:
      return 675;
    case UnitOp::kDig:
      return 625;
    case UnitOp::kBuildCoop:
    case UnitOp::kBuildPasture:
      return 600;
    case UnitOp::kCare:
      return 500;
    case UnitOp::kCollectFertilizer:
      return 475;
    case UnitOp::kFertilize:
      return 450;
    default:
      return 0;
  }
}

int NeedPriority(UnitOp op, bool hard, const StrategyOptions& options) {
  if (hard) return kHardPriority;
  if (options.soft_service_mode == SoftServiceMode::kSurvivalFirst) {
    if (op == UnitOp::kWater) return 400;
    if (op == UnitOp::kFeed) return 425;
  }
  return OperationPriority(op);
}

std::optional<int> NeedDeadline(bool hard, int end_of_day,
                                const StrategyOptions& options) {
  if (hard || options.soft_service_mode == SoftServiceMode::kEager) {
    return end_of_day;
  }
  return std::nullopt;
}

bool CanMature(int crop, int day, int final_day) {
  return day + kCrops[crop].first_yield_day <= final_day;
}

int CarriedAndShed(const PrivateState& priv, int item_index) {
  int64_t total = priv.shed[item_index];
  for (const Inventory& inventory : priv.inventories) {
    total += inventory.Get(item_index);
  }
  return static_cast<int>(total);
}

int CropDeficit(const StrategyOptions& options,
                const std::array<int, kNumCrops>& crop_counts, int crop,
                int retiring_crop = -1) {
  if (!options.has_crop_targets) return crop == options.preferred_crop ? 1 : 0;
  const int remaining = crop_counts[crop] - (crop == retiring_crop ? 1 : 0);
  return std::max(0, options.target_crops[crop] - remaining);
}

int ReserveCrop(const std::array<int64_t, kNumCrops>& seeds, int day,
                int final_day, const StrategyOptions& options,
                const std::array<int, kNumCrops>& crop_counts,
                int retiring_crop = -1) {
  std::array<int, kNumCrops> crops{};
  std::iota(crops.begin(), crops.end(), 0);
  std::sort(crops.begin(), crops.end(), [&](int left, int right) {
    return std::tuple(-CropDeficit(options, crop_counts, left, retiring_crop),
                      left != options.preferred_crop,
                      kCrops[left].first_yield_day,
                      std::string(kItemNames[left])) <
           std::tuple(-CropDeficit(options, crop_counts, right, retiring_crop),
                      right != options.preferred_crop,
                      kCrops[right].first_yield_day,
                      std::string(kItemNames[right]));
  });
  for (int crop : crops) {
    if (options.has_crop_targets &&
        CropDeficit(options, crop_counts, crop, retiring_crop) <= 0) {
      continue;
    }
    if (seeds[crop] > 0 && CanMature(crop, day, final_day)) return crop;
  }
  return -1;
}

Intent MakeIntent(UnitAction action, std::string key, int priority,
                  std::optional<int> deadline = std::nullopt) {
  Intent intent;
  intent.action = action;
  intent.key = std::move(key);
  intent.priority = priority;
  intent.deadline_step = deadline;
  return intent;
}

Intent PlantIntent(int crop, std::string key, int priority,
                   std::optional<int> deadline) {
  return MakeIntent(UnitAction{UnitOp::kPlant, crop, 1}, std::move(key),
                    priority, deadline);
}

Intent SimpleIntent(UnitOp op, std::string key, int priority,
                    std::optional<int> deadline = std::nullopt) {
  return MakeIntent(UnitAction{op, -1, 1}, std::move(key), priority, deadline);
}

int MaxPriority(const std::vector<Intent>& intents) {
  int result = 0;
  for (const Intent& intent : intents) result = std::max(result, intent.priority);
  return result;
}

std::optional<int> EarliestDeadline(const std::vector<Intent>& intents) {
  std::optional<int> result;
  for (const Intent& intent : intents) {
    if (!intent.deadline_step) continue;
    if (!result || *intent.deadline_step < *result) result = intent.deadline_step;
  }
  return result;
}

void AddPlantPipeline(std::vector<Intent>* intents, int crop, int priority,
                      int deadline, std::string exclusive_group,
                      int resource_limit) {
  Intent plant = PlantIntent(crop, "plant", priority, deadline);
  plant.exclusive_group = std::move(exclusive_group);
  plant.resource_group = "seed:" + std::to_string(crop);
  plant.resource_limit = resource_limit;
  intents->push_back(std::move(plant));
  Intent water = SimpleIntent(UnitOp::kWater, "water", priority, deadline);
  water.predecessors = {"plant"};
  intents->push_back(std::move(water));
}

std::vector<Intent> AnimalSetupIntents(int animal, int deadline,
                                       std::optional<UnitOp> build,
                                       int available,
                                       const std::string& exclusive_group,
                                       const std::string& build_group,
                                       int build_limit, bool reserve_before_ready,
                                       bool allow_supply, bool requires_command) {
  std::vector<Intent> intents;
  if (build) {
    Intent build_intent =
        SimpleIntent(*build, "build", OperationPriority(*build), deadline);
    build_intent.exclusive_group =
        "build_target:" + exclusive_group.substr(exclusive_group.find(':') + 1);
    build_intent.resource_group = build_group;
    build_intent.resource_limit = build_limit;
    build_intent.requires_command = requires_command;
    intents.push_back(std::move(build_intent));
  }
  Intent place = MakeIntent(
      UnitAction{UnitOp::kPlace, item::kGoose + animal, 1}, "place",
      OperationPriority(UnitOp::kPlace), deadline);
  place.required_item = item::kGoose + animal;
  if (build) place.predecessors = {"build"};
  place.resource_group = build_group.empty()
                             ? "animal:" + std::to_string(animal)
                             : build_group;
  place.resource_limit = std::max(1, build_limit > 0 ? build_limit : available);
  place.exclusive_group = exclusive_group;
  place.reserve_before_ready = reserve_before_ready;
  place.allow_supply = allow_supply;
  place.requires_command = requires_command;
  intents.push_back(std::move(place));

  Intent feed = SimpleIntent(UnitOp::kFeed, "feed",
                             OperationPriority(UnitOp::kFeed), deadline);
  feed.required_item = item::kWheat;
  feed.predecessors = {"place"};
  feed.requires_command = requires_command;
  intents.push_back(std::move(feed));
  Intent care = SimpleIntent(UnitOp::kCare, "care",
                             OperationPriority(UnitOp::kCare), deadline);
  care.predecessors = {"place"};
  care.requires_command = requires_command;
  intents.push_back(std::move(care));
  return intents;
}

double AnimalFutureValue(int animal, int day, int final_day,
                         const MarketState& market) {
  const AnimalData& rule = kAnimals[animal];
  const int first_day = day + rule.first_yield_day;
  const int productions =
      1 + std::max(0, final_day - first_day) / std::max(1, rule.interval);
  const int remaining_days = std::max(0, final_day - day);
  return productions * static_cast<double>(market.prices[rule.product]) +
         remaining_days * static_cast<double>(market.prices[item::kFertilizer]) -
         remaining_days * static_cast<double>(market.prices[item::kWheat]);
}

struct ProjectLayout {
  bool enabled = false;
  int board_cells = 0;
  std::map<std::pair<int, int>, int> service_rank;
  std::set<std::pair<int, int>> animal_zone;
  std::set<std::pair<int, int>> crop_zone;

  int ServiceRank(std::pair<int, int> position) const {
    if (!enabled) return 0;
    const auto it = service_rank.find(position);
    return it == service_rank.end() ? board_cells : it->second;
  }

  int AnimalCost(std::pair<int, int> position) const {
    return ServiceRank(position) +
           (crop_zone.contains(position) ? board_cells : 0);
  }

  int CropCost(std::pair<int, int> position) const {
    return ServiceRank(position) +
           (animal_zone.contains(position) ? board_cells : 0);
  }
};

ProjectLayout BuildProjectLayout(int board_size, ProjectLayoutKind kind,
                                 int animal_zone_cells,
                                 int crop_zone_cells) {
  ProjectLayout result;
  result.enabled = kind != ProjectLayoutKind::kAdaptive;
  result.board_cells = board_size * board_size;
  if (!result.enabled) return result;

  const auto sheds = ShedAccessTiles(board_size);
  std::vector<std::pair<int, int>> cells;
  cells.reserve(result.board_cells);
  for (int y = 0; y < board_size; ++y) {
    for (int x = 0; x < board_size; ++x) cells.emplace_back(x, y);
  }
  std::sort(cells.begin(), cells.end(), [&](const auto& left,
                                            const auto& right) {
    const auto shed_distance = [&](const auto& position) {
      return std::min({
          std::abs(position.first - sheds[0].first) +
              std::abs(position.second - sheds[0].second),
          std::abs(position.first - sheds[1].first) +
              std::abs(position.second - sheds[1].second),
          std::abs(position.first - sheds[2].first) +
              std::abs(position.second - sheds[2].second),
          std::abs(position.first - sheds[3].first) +
              std::abs(position.second - sheds[3].second),
      });
    };
    const auto route_index = [&](const auto& position) {
      const int offset = position.second % 2 == 0
                             ? position.first
                             : board_size - 1 - position.first;
      return position.second * board_size + offset;
    };
    return std::tuple(shed_distance(left), route_index(left), left) <
           std::tuple(shed_distance(right), route_index(right), right);
  });
  for (size_t index = 0; index < cells.size(); ++index) {
    result.service_rank[cells[index]] = static_cast<int>(index);
    if (kind == ProjectLayoutKind::kServiceZones &&
        static_cast<int>(index) < animal_zone_cells) {
      result.animal_zone.insert(cells[index]);
    }
    if (kind == ProjectLayoutKind::kCropCore &&
        static_cast<int>(index) < crop_zone_cells) {
      result.crop_zone.insert(cells[index]);
    }
  }
  return result;
}

std::vector<int> InvestmentAnimals(const PlannerStateView& state, int day,
                                   int final_day) {
  std::vector<int> result;
  for (int animal = 0; animal < kNumAnimals; ++animal) {
    if (day + kAnimals[animal].first_yield_day <= final_day &&
        AnimalFutureValue(animal, day, final_day, state.market) >
            static_cast<double>(kAnimals[animal].cost)) {
      result.push_back(animal);
    }
  }
  std::sort(result.begin(), result.end(), [&](int left, int right) {
    const double left_margin = AnimalFutureValue(left, day, final_day, state.market) -
                               static_cast<double>(kAnimals[left].cost);
    const double right_margin =
        AnimalFutureValue(right, day, final_day, state.market) -
        static_cast<double>(kAnimals[right].cost);
    return std::tuple(-left_margin, kAnimals[left].first_yield_day,
                      std::string(kItemNames[item::kGoose + left])) <
           std::tuple(-right_margin, kAnimals[right].first_yield_day,
                      std::string(kItemNames[item::kGoose + right]));
  });
  return result;
}

}  // namespace

std::vector<Task> GenerateTasks(const PlannerStateView& state,
                                const StrategyOptions& options,
                                ProjectLayoutKind project_layout,
                                int animal_zone_cells,
                                int crop_zone_cells,
                                int project_layout_start_day) {
  const Farm& farm = state.farm;
  const PrivateState& priv = state.priv;
  const Config& config = state.config;
  const int step = state.step;
  const int day = step / std::max(1, config.turns_per_day);
  const int final_day = (std::max(2, config.episode_steps) - 2) /
                        std::max(1, config.turns_per_day);
  const int end_of_day = (day + 1) * std::max(1, config.turns_per_day) - 1;
  const ProjectLayout layout = BuildProjectLayout(
      config.board_size,
      day >= project_layout_start_day ? project_layout
                                      : ProjectLayoutKind::kAdaptive,
      animal_zone_cells, crop_zone_cells);

  std::vector<Task> urgent;
  std::vector<Task> renewal;
  std::vector<Task> optional;
  std::vector<std::tuple<int, int, StructureKind>> bare_structures;
  std::vector<std::pair<int, int>> empty_positions;
  std::array<int, kNumCrops> crop_counts{};
  std::array<int, kNumAnimals> animal_counts{};
  int unfed_animals = 0;

  for (const Tile& tile : farm.tiles) {
    if (tile.kind == TileKind::kPlant) {
      ++crop_counts[tile.crop];
    } else if (tile.kind == TileKind::kStructure && tile.has_animal) {
      ++animal_counts[tile.animal];
    }
  }
  const int plant_count =
      std::accumulate(crop_counts.begin(), crop_counts.end(), 0);
  const int existing_animals =
      std::accumulate(animal_counts.begin(), animal_counts.end(), 0);

  for (int y = 0; y < config.board_size; ++y) {
    for (int x = 0; x < config.board_size; ++x) {
      const Tile& tile = farm.tiles[y * config.board_size + x];
      if (tile.kind == TileKind::kEmpty) {
        empty_positions.emplace_back(x, y);
        continue;
      }
      if (tile.kind == TileKind::kPlant) {
        const CropData& crop = kCrops[tile.crop];
        const bool mature = tile.yield_units > 0 &&
                            day - tile.planted_day >= crop.first_yield_day;
        const bool harvest_ready =
            mature &&
            (crop.ongoing || !options.defer_one_time_harvest ||
             tile.yield_units >= crop.max_yield ||
             day - tile.planted_day >= crop.max_yield_day);
        const bool needs_water = !tile.watered_today;
        const bool hard_water = needs_water && tile.consecutive_unwatered >= 1;
        const bool hard_harvest = mature && tile.max_lifespan_step >= 0 &&
                                  tile.max_lifespan_step <= end_of_day;
        const bool expired = tile.max_lifespan_step >= 0 &&
                             tile.max_lifespan_step < step;
        const bool retire_soon = crop.ongoing && tile.max_lifespan_step >= 0 &&
                                 tile.max_lifespan_step <= end_of_day + 1;
        std::vector<Intent> intents;
        std::string reason;
        std::string task_prefix;
        if (expired || retire_soon) {
          const bool critical_harvest =
              hard_harvest || (mature && hard_water && !crop.ongoing);
          if (mature) {
            Intent harvest = SimpleIntent(
                UnitOp::kHarvest, "harvest",
                critical_harvest ? kHardPriority
                                 : OperationPriority(UnitOp::kHarvest),
                hard_harvest ? std::optional<int>(tile.max_lifespan_step)
                             : critical_harvest ? std::optional<int>(end_of_day)
                                                : std::nullopt);
            harvest.hard = critical_harvest;
            if (expired) harvest.exclusive_group =
                "retire_terminal:" + std::to_string(x) + ":" + std::to_string(y);
            intents.push_back(std::move(harvest));
          }
          if (needs_water) {
            Intent water = SimpleIntent(
                UnitOp::kWater, "water_before_retirement",
                NeedPriority(UnitOp::kWater, hard_water, options),
                NeedDeadline(hard_water, end_of_day, options));
            water.hard = hard_water;
            intents.push_back(std::move(water));
          }
          Intent dig = SimpleIntent(UnitOp::kDig, "dig",
                                    OperationPriority(UnitOp::kDig), end_of_day);
          if (mature && retire_soon && !expired) dig.predecessors = {"harvest"};
          if (expired) dig.exclusive_group =
              "retire_terminal:" + std::to_string(x) + ":" + std::to_string(y);
          dig.requires_command = retire_soon && !expired && !mature;
          intents.push_back(std::move(dig));
          for (int replacement = 0;
               options.allow_crop_investment && replacement < kNumCrops;
               ++replacement) {
            if (priv.seeds[replacement] <= 0 ||
                !CanMature(replacement, day, final_day)) {
              continue;
            }
            const int target_deficit = CropDeficit(
                options, crop_counts, replacement, tile.crop);
            if (options.has_crop_targets && target_deficit <= 0) continue;
            const std::string plant_key =
                "plant:" + std::to_string(replacement);
            Intent plant = PlantIntent(replacement, plant_key,
                                       OperationPriority(UnitOp::kPlant),
                                       end_of_day);
            plant.predecessors = {"dig"};
            plant.resource_group = "seed:" + std::to_string(replacement);
            plant.resource_limit = std::min(
                static_cast<int>(priv.seeds[replacement]),
                options.has_crop_targets ? target_deficit
                                         : static_cast<int>(priv.seeds[replacement]));
            plant.exclusive_group = "replacement:" + std::to_string(x) + ":" +
                                    std::to_string(y);
            plant.requires_command = retire_soon && !expired && !mature;
            intents.push_back(std::move(plant));
            Intent water = SimpleIntent(UnitOp::kWater,
                                        "water:" + std::to_string(replacement),
                                        OperationPriority(UnitOp::kWater));
            water.predecessors = {plant_key};
            water.requires_command = retire_soon && !expired && !mature;
            intents.push_back(std::move(water));
          }
          reason = expired ? "replace_expired_crop" : "replace_expiring_crop";
          task_prefix = "retire:";
        } else {
          const bool critical_harvest =
              hard_harvest || (mature && hard_water && !crop.ongoing);
          if (harvest_ready) {
            Intent harvest = SimpleIntent(
                UnitOp::kHarvest, "harvest",
                critical_harvest ? kHardPriority
                                 : OperationPriority(UnitOp::kHarvest),
                hard_harvest ? std::optional<int>(tile.max_lifespan_step)
                             : critical_harvest ? std::optional<int>(end_of_day)
                                                : std::nullopt);
            harvest.hard = critical_harvest;
            intents.push_back(std::move(harvest));
            if (options.allow_crop_investment && !crop.ongoing) {
              const int replacement =
                  ReserveCrop(priv.seeds, day, final_day, options, crop_counts,
                              tile.crop);
              if (replacement >= 0) {
                Intent plant = PlantIntent(replacement, "plant",
                                           OperationPriority(UnitOp::kPlant),
                                           end_of_day);
                plant.predecessors = {"harvest"};
                plant.resource_group = "seed:" + std::to_string(replacement);
                plant.resource_limit = static_cast<int>(priv.seeds[replacement]);
                intents.push_back(std::move(plant));
                Intent water = SimpleIntent(UnitOp::kWater, "water",
                                            OperationPriority(UnitOp::kPlant),
                                            end_of_day);
                water.predecessors = {"plant"};
                intents.push_back(std::move(water));
              }
            }
            if (needs_water) {
              Intent water = SimpleIntent(
                  UnitOp::kWater, "water_before_harvest",
                  NeedPriority(UnitOp::kWater, hard_water, options),
                  NeedDeadline(hard_water, end_of_day, options));
              water.hard = hard_water;
              intents.push_back(std::move(water));
            }
          } else if (needs_water) {
            Intent water = SimpleIntent(
                UnitOp::kWater, "water",
                NeedPriority(UnitOp::kWater, hard_water, options),
                NeedDeadline(hard_water, end_of_day, options));
            water.hard = hard_water;
            intents.push_back(std::move(water));
          }
          reason = hard_water       ? "prevent_crop_loss"
                   : hard_harvest   ? "prevent_harvest_loss"
                                    : "crop_lifecycle";
          task_prefix = "plant:";
        }
        if (!intents.empty()) {
          Task task;
          task.key = task_prefix + std::to_string(x) + ":" + std::to_string(y);
          task.position = {x, y};
          task.priority = MaxPriority(intents);
          task.deadline_step = EarliestDeadline(intents);
          task.reason = std::move(reason);
          task.intents = std::move(intents);
          (expired || retire_soon ? renewal : urgent).push_back(std::move(task));
        }
        continue;
      }

      if (tile.kind == TileKind::kStructure) {
        if (!tile.has_animal) {
          bare_structures.emplace_back(x, y, tile.structure);
          continue;
        }
        if (!tile.fed_today) ++unfed_animals;
        std::vector<Intent> intents;
        if (tile.yield_units > 0) {
          intents.push_back(SimpleIntent(UnitOp::kHarvest, "harvest",
                                         OperationPriority(UnitOp::kHarvest)));
        }
        const bool hard_feed = tile.consecutive_unfed >= 1 && !tile.fed_today;
        if (!tile.fed_today) {
          Intent feed = SimpleIntent(
              UnitOp::kFeed, "feed",
              NeedPriority(UnitOp::kFeed, hard_feed, options),
              NeedDeadline(hard_feed, end_of_day, options));
          feed.required_item = item::kWheat;
          feed.hard = hard_feed;
          intents.push_back(std::move(feed));
        }
        if (!tile.cared_today) {
          intents.push_back(SimpleIntent(UnitOp::kCare, "care",
                                         OperationPriority(UnitOp::kCare),
                                         end_of_day));
        }
        if (tile.fertilizer_available) {
          intents.push_back(SimpleIntent(
              UnitOp::kCollectFertilizer, "collect_fertilizer",
              OperationPriority(UnitOp::kCollectFertilizer)));
        }
        if (!intents.empty()) {
          Task task;
          task.key = "animal:" + std::to_string(x) + ":" + std::to_string(y);
          task.position = {x, y};
          task.priority = MaxPriority(intents);
          task.deadline_step = end_of_day;
          task.reason = hard_feed ? "prevent_animal_escape" : "animal_lifecycle";
          task.intents = std::move(intents);
          urgent.push_back(std::move(task));
        }
        continue;
      }

      if (tile.kind == TileKind::kWeed) {
        std::vector<Intent> intents;
        intents.push_back(SimpleIntent(UnitOp::kDig, "dig",
                                       OperationPriority(UnitOp::kDig)));
        const int crop = options.allow_crop_investment
                             ? ReserveCrop(priv.seeds, day, final_day, options,
                                           crop_counts)
                             : -1;
        if (crop >= 0) {
          Intent plant = PlantIntent(crop, "plant", 450, std::nullopt);
          plant.predecessors = {"dig"};
          plant.resource_group = "seed:" + std::to_string(crop);
          plant.resource_limit = static_cast<int>(priv.seeds[crop]);
          intents.push_back(std::move(plant));
          Intent water = SimpleIntent(UnitOp::kWater, "water", 450);
          water.predecessors = {"plant"};
          intents.push_back(std::move(water));
        }
        renewal.push_back(Task{"weed:" + std::to_string(x) + ":" +
                                   std::to_string(y),
                               {x, y}, std::move(intents), 450, std::nullopt,
                               "recover_tile"});
      }
    }
  }

  const int unit_count = 1 + static_cast<int>(farm.hands.size());
  const int action_capacity = unit_count * std::max(1, config.turns_per_day);
  const bool sustainable = plant_count + existing_animals * 4 + 4 <= action_capacity;
  const bool supplied = CarriedAndShed(priv, item::kWheat) >= unfed_animals;
  const bool spare_actor = unfed_animals == 0 || unit_count > 1;
  std::array<int, kNumAnimals> animal_inventory{};
  int total_animals = 0;
  for (int animal = 0; animal < kNumAnimals; ++animal) {
    animal_inventory[animal] = CarriedAndShed(priv, item::kGoose + animal);
    total_animals += animal_inventory[animal];
  }
  std::array<int, kNumAnimals> placement_deficits{};
  std::array<int, kNumAnimals> acquisition_deficits{};
  std::vector<int> investments;
  const std::vector<int> economic_investments =
      InvestmentAnimals(state, day, final_day);
  for (int animal = 0; animal < kNumAnimals; ++animal) {
    if (options.has_animal_targets) {
      placement_deficits[animal] =
          std::max(0, options.target_animals[animal] - animal_counts[animal]);
      acquisition_deficits[animal] = std::max(
          0, placement_deficits[animal] - animal_inventory[animal]);
      if (acquisition_deficits[animal] > 0 &&
          day + kAnimals[animal].first_yield_day <= final_day) {
        investments.push_back(animal);
      }
      continue;
    }
    placement_deficits[animal] = animal_inventory[animal];
  }
  if (!options.has_animal_targets && options.allow_animal_investment &&
      total_animals == 0 && sustainable && supplied && spare_actor) {
    investments = economic_investments;
    if (options.preferred_animal >= 0) {
      auto it = std::find(investments.begin(), investments.end(),
                          options.preferred_animal);
      if (it != investments.end()) std::rotate(investments.begin(), it, it + 1);
    }
    if (!investments.empty()) {
      placement_deficits[investments.front()] = 1;
      acquisition_deficits[investments.front()] = 1;
    }
  }
  if (!options.allow_animal_investment || !sustainable || !supplied ||
      !spare_actor) {
    investments.clear();
    acquisition_deficits.fill(0);
  }

  for (const auto& [x, y, structure] : bare_structures) {
    for (int animal = 0; animal < kNumAnimals; ++animal) {
      if (kAnimals[animal].structure != structure) continue;
      if (placement_deficits[animal] <= 0) continue;
      const bool acquire = animal_inventory[animal] <= 0;
      const bool allow_supply = acquisition_deficits[animal] > 0;
      auto intents = AnimalSetupIntents(
          animal, end_of_day, std::nullopt,
          std::max(1, placement_deficits[animal]),
          "occupy:" + std::to_string(x) + ":" + std::to_string(y),
          "animal_goal:" + std::to_string(animal),
          std::max(1, placement_deficits[animal]), allow_supply,
          !acquire || allow_supply, acquire && !allow_supply);
      Task task{
          "animal_setup:" + std::to_string(animal) + ":" + std::to_string(x) +
              ":" + std::to_string(y),
          {x, y}, std::move(intents), OperationPriority(UnitOp::kFeed),
          end_of_day,
          acquire ? "acquire_and_place_animal" : "place_owned_animal"};
      task.layout_cost = layout.AnimalCost({x, y});
      renewal.push_back(std::move(task));
    }
  }

  for (int animal = 0; animal < kNumAnimals; ++animal) {
    if (placement_deficits[animal] <= 0) continue;
    const bool acquire = animal_inventory[animal] <= 0;
    const bool allow_supply = acquisition_deficits[animal] > 0;
    const int bare_count = static_cast<int>(std::count_if(
        bare_structures.begin(), bare_structures.end(), [&](const auto& entry) {
          return std::get<2>(entry) == kAnimals[animal].structure;
        }));
    const int required_builds =
        std::max(0, placement_deficits[animal] - bare_count);
    bool requires_command = acquire ? (!allow_supply || bare_count > 0)
                                    : required_builds == 0;
    requires_command = requires_command ||
                       day + kAnimals[animal].first_yield_day > final_day;
    const UnitOp build = kAnimals[animal].structure == StructureKind::kCoop
                             ? UnitOp::kBuildCoop
                             : UnitOp::kBuildPasture;
    for (const auto& [x, y] : empty_positions) {
      auto intents = AnimalSetupIntents(
          animal, end_of_day, build, std::max(1, placement_deficits[animal]),
          "occupy:" + std::to_string(x) + ":" + std::to_string(y),
          "animal_goal:" + std::to_string(animal),
          std::max(1, required_builds), allow_supply, !acquire || allow_supply,
          requires_command);
      Task task{
          "animal_setup:" + std::to_string(animal) + ":" + std::to_string(x) +
              ":" + std::to_string(y),
          {x, y}, std::move(intents), OperationPriority(UnitOp::kFeed),
          end_of_day,
          allow_supply ? "build_for_planned_animal"
                       : animal_inventory[animal] > 0 ? "build_for_owned_animal"
                                                      : "prepare_animal_structure"};
      task.layout_cost = layout.AnimalCost({x, y});
      optional.push_back(std::move(task));
    }
  }

  int expansion_limit = options.enforce_production_targets
                            ? std::max(0, options.target_plants - plant_count)
                            : -1;
  std::array<int, kNumCrops> crop_order{};
  std::iota(crop_order.begin(), crop_order.end(), 0);
  std::sort(crop_order.begin(), crop_order.end(), [&](int left, int right) {
    return std::tuple(left != options.preferred_crop,
                      kCrops[left].first_yield_day,
                      std::string(kItemNames[left])) <
           std::tuple(right != options.preferred_crop,
                      kCrops[right].first_yield_day,
                      std::string(kItemNames[right]));
  });
  for (int crop : crop_order) {
    const int target_deficit = CropDeficit(options, crop_counts, crop);
    if (options.has_crop_targets && target_deficit <= 0) continue;
    if (options.enforce_production_targets && !options.has_crop_targets &&
        crop != options.preferred_crop) {
      continue;
    }
    int available = static_cast<int>(priv.seeds[crop]);
    if (options.has_crop_targets) available = std::min(available, target_deficit);
    if (expansion_limit >= 0) available = std::min(available, expansion_limit);
    if (available <= 0 || !CanMature(crop, day, final_day)) continue;
    for (const auto& [x, y] : empty_positions) {
      std::vector<Intent> intents;
      AddPlantPipeline(&intents, crop, 300, end_of_day,
                       "build_target:" + std::to_string(x) + ":" +
                           std::to_string(y),
                       available);
      Task task{"empty:" + std::to_string(crop) + ":" +
                    std::to_string(x) + ":" + std::to_string(y),
                {x, y}, std::move(intents), 300, end_of_day,
                "use_available_seed"};
      task.layout_cost = layout.CropCost({x, y});
      optional.push_back(std::move(task));
    }
  }

  std::vector<Task> result;
  result.reserve(urgent.size() + renewal.size() + optional.size());
  result.insert(result.end(), std::make_move_iterator(urgent.begin()),
                std::make_move_iterator(urgent.end()));
  result.insert(result.end(), std::make_move_iterator(renewal.begin()),
                std::make_move_iterator(renewal.end()));
  result.insert(result.end(), std::make_move_iterator(optional.begin()),
                std::make_move_iterator(optional.end()));
  std::stable_sort(result.begin(), result.end(), [](const Task& left, const Task& right) {
    return std::tuple(!left.deadline_step.has_value(),
                      left.deadline_step.value_or(0), -left.priority,
                      left.position.second, left.position.first) <
           std::tuple(!right.deadline_step.has_value(),
                      right.deadline_step.value_or(0), -right.priority,
                      right.position.second, right.position.first);
  });
  return result;
}

}  // namespace kagg::planner
