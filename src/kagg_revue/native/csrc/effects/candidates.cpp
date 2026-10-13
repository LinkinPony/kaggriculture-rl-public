#include "effects/session.hpp"

#include <algorithm>
#include <array>
#include <cstdint>
#include <limits>
#include <stdexcept>
#include <tuple>
#include <utility>
#include <vector>

#include "effects/internal.hpp"

namespace kagg::effects {
namespace {

constexpr uint64_t kFnvOffset = 1469598103934665603ULL;

Candidate MakeCandidate(RequestKind kind, int target = -1, int item_index = -1,
                        int64_t quantity = 0) {
  Candidate result;
  result.kind = kind;
  result.fields[0] = static_cast<int64_t>(kind);
  result.fields[1] = target;
  result.fields[2] = item_index + 1;
  result.fields[3] = quantity;
  return result;
}

std::vector<uint8_t> BusyUnits(const std::vector<Job>& jobs, int unit_count) {
  std::vector<uint8_t> result(static_cast<std::size_t>(unit_count), 0);
  for (const Job& job : jobs) {
    if (job.unit >= 0 && job.unit < unit_count) result[job.unit] = 1;
  }
  return result;
}

int64_t AccessibleItem(const PrivateState& priv,
                       const std::vector<uint8_t>& busy, int item_index) {
  int64_t result = priv.shed[item_index];
  for (int unit = 0; unit < static_cast<int>(priv.inventories.size()); ++unit) {
    if (!busy[unit]) result += priv.inventories[unit].Get(item_index);
  }
  return result;
}

int CompletionSteps(const Config& config, const Farm& farm,
                    const PrivateState& priv, const std::vector<uint8_t>& busy,
                    RequestKind kind, int target, int item_index,
                    int bound_unit) {
  const int required = internal::RequiredItem(kind, item_index);
  int best = std::numeric_limits<int>::max();
  for (int unit = 0; unit < static_cast<int>(priv.inventories.size()); ++unit) {
    if (busy[unit] || (bound_unit >= 0 && unit != bound_unit)) continue;
    const auto [x, y] = internal::UnitPosition(farm, unit);
    int cost = 0;
    if (kind == RequestKind::kBank || kind == RequestKind::kLoad ||
        kind == RequestKind::kUnload) {
      const auto shed = internal::NearestShed(x, y, config.board_size);
      cost = internal::Distance(x, y, shed.first, shed.second) + 1;
    } else if (kind == RequestKind::kStage) {
      const auto destination =
          internal::TargetPosition(target, config.board_size);
      cost = internal::Distance(x, y, destination.first, destination.second);
    } else {
      const auto destination =
          internal::TargetPosition(target, config.board_size);
      if (required >= 0 && priv.inventories[unit].Get(required) <= 0) {
        if (priv.shed[required] <= 0) continue;
        const auto shed = internal::BestShedForRoute(
            x, y, destination.first, destination.second, config.board_size);
        cost = internal::Distance(x, y, shed.first, shed.second) + 1 +
               internal::Distance(shed.first, shed.second, destination.first,
                                  destination.second) +
               1;
      } else {
        cost = internal::Distance(x, y, destination.first,
                                  destination.second) +
               1;
      }
    }
    best = std::min(best, cost);
  }
  return best;
}

float TargetState(const Tile& tile) {
  if (tile.kind == TileKind::kPlant) {
    return tile.watered_today ? 1.0F : 0.0F;
  }
  if (tile.kind == TileKind::kStructure && tile.has_animal) {
    return (static_cast<float>(tile.fed_today) +
            static_cast<float>(tile.cared_today) +
            static_cast<float>(tile.yield_units > 0)) /
           3.0F;
  }
  return 0.0F;
}

}  // namespace

void Session::AddWorkCandidate(const Engine& engine, int player,
                               Candidate candidate) {
  const Farm& farm = engine.farm(player);
  const PrivateState& priv = engine.priv(player);
  const int target = static_cast<int>(candidate.fields[1]);
  const int unit = static_cast<int>(candidate.fields[5]) - 1;
  const auto busy = BusyUnits(jobs_, static_cast<int>(priv.inventories.size()));
  const int completion = CompletionSteps(
      config_, farm, priv, busy, candidate.kind, target,
      static_cast<int>(candidate.fields[2]) - 1, unit);
  candidate.features[0] =
      completion == std::numeric_limits<int>::max()
          ? 2.0F
          : static_cast<float>(completion) /
                std::max(1, config_.episode_steps - 1);
  candidate.features[1] =
      candidate.fields[6] == static_cast<int64_t>(ResourceKind::kItem) ||
              candidate.kind == RequestKind::kBank ||
              candidate.kind == RequestKind::kLoad ||
              candidate.kind == RequestKind::kUnload
          ? 1.0F
          : 0.0F;
  candidate.features[2] = static_cast<float>(candidate.fields[8]) /
                          std::max<int64_t>(1, config_.shed_capacity);
  candidate.features[3] = static_cast<float>(candidate.fields[9]) /
                          std::max<int64_t>(1, config_.shed_capacity);
  candidate.features[4] =
      static_cast<float>(config_.episode_steps - 1 - engine.step_index()) /
      std::max(1, config_.episode_steps - 1);
  candidate.features[5] =
      static_cast<float>(config_.turns_per_day - 1 -
                         engine.step_index() % config_.turns_per_day) /
      std::max(1, config_.turns_per_day - 1);
  if (target >= 0 && target < static_cast<int>(farm.tiles.size())) {
    const Tile& tile = farm.tiles[target];
    candidate.features[6] =
        static_cast<float>(target % config_.board_size) /
        std::max(1, config_.board_size - 1);
    candidate.features[7] =
        static_cast<float>(target / config_.board_size) /
        std::max(1, config_.board_size - 1);
    candidate.features[8] = static_cast<float>(tile.kind) / 4.0F;
    candidate.features[9] = TargetState(tile);
  }
  if (unit >= 0 && unit < static_cast<int>(priv.inventories.size())) {
    candidate.features[10] =
        static_cast<float>(internal::InventoryTotal(priv.inventories[unit])) /
        std::max<int64_t>(1, config_.shed_capacity);
  }

  uint64_t hash = internal::HashWord(kSpecVersion, kFnvOffset);
  hash = internal::HashWord(static_cast<uint64_t>(Phase::kWork), hash);
  hash = internal::HashWord(static_cast<uint64_t>(engine.step_index()), hash);
  for (const int64_t field : candidate.fields) {
    hash = internal::HashWord(static_cast<uint64_t>(field), hash);
  }
  candidate.canonical_id = hash == 0 ? 1 : hash;
  candidates_.push_back(std::move(candidate));
}

void Session::GenerateWorkCandidates(const Engine& engine, int player) {
  candidates_.clear();
  candidate_mask_.clear();
  AddWorkCandidate(engine, player, MakeCandidate(RequestKind::kStop));
  const Farm& farm = engine.farm(player);
  const PrivateState& priv = engine.priv(player);
  const int unit_count = static_cast<int>(priv.inventories.size());
  const auto busy = BusyUnits(jobs_, unit_count);
  const int day = engine.step_index() / config_.turns_per_day;
  const int remaining = config_.episode_steps - 1 - engine.step_index();
  const int day_remaining =
      config_.turns_per_day - engine.step_index() % config_.turns_per_day;
  const int completion_limit = std::min(remaining, day_remaining);

  const auto add_target = [&](RequestKind kind, int target, int item_index,
                              ResourceKind resource, int resource_item,
                              int64_t available) {
    Candidate unbound = MakeCandidate(kind, target, item_index, 0);
    unbound.fields[6] = static_cast<int64_t>(resource);
    unbound.fields[7] = resource_item + 1;
    unbound.fields[8] = resource == ResourceKind::kNone ? 0 : 1;
    unbound.fields[9] = available;
    const int unbound_completion = CompletionSteps(
        config_, farm, priv, busy, kind, target, item_index, -1);
    if (unbound_completion > 0 && unbound_completion <= completion_limit) {
      AddWorkCandidate(engine, player, std::move(unbound));
    }

    const auto destination =
        internal::TargetPosition(target, config_.board_size);
    for (int unit = 0; unit < unit_count; ++unit) {
      if (busy[unit] || internal::UnitPosition(farm, unit) != destination) {
        continue;
      }
      Candidate candidate = MakeCandidate(kind, target, item_index, 0);
      candidate.fields[5] = unit + 1;
      const bool carried =
          resource == ResourceKind::kItem && resource_item >= 0 &&
          priv.inventories[unit].Get(resource_item) > 0;
      candidate.fields[6] =
          static_cast<int64_t>(carried ? ResourceKind::kNone : resource);
      candidate.fields[7] = carried ? 0 : resource_item + 1;
      candidate.fields[8] =
          resource == ResourceKind::kNone || carried ? 0 : 1;
      candidate.fields[9] = carried ? 0 : available;
      const int completion = CompletionSteps(config_, farm, priv, busy, kind,
                                             target, item_index, unit);
      if (completion <= 0 || completion > completion_limit) continue;
      AddWorkCandidate(engine, player, std::move(candidate));
    }
  };

  if (idle_units_ > 0) {
    for (int target = 0; target < static_cast<int>(farm.tiles.size()); ++target) {
      const Tile& tile = farm.tiles[target];
      if (tile.kind == TileKind::kEmpty) {
        for (int crop = 0; crop < kNumCrops; ++crop) {
          if (priv.seeds[crop] > 0) {
            add_target(RequestKind::kPlant, target, crop,
                       ResourceKind::kSeed, crop, priv.seeds[crop]);
          }
        }
        add_target(RequestKind::kBuildCoop, target, -1,
                   ResourceKind::kNone, -1, 0);
        add_target(RequestKind::kBuildPasture, target, -1,
                   ResourceKind::kNone, -1, 0);
      } else if (tile.kind == TileKind::kPlant) {
        if (!tile.watered_today) {
          add_target(RequestKind::kWater, target, -1,
                     ResourceKind::kNone, -1, 0);
        }
        if (internal::TargetSupports(farm, day, RequestKind::kHarvest,
                                     target, -1)) {
          add_target(RequestKind::kHarvest, target, -1,
                     ResourceKind::kNone, -1, 0);
        }
        const int64_t fertilizer =
            AccessibleItem(priv, busy, item::kFertilizer);
        if (fertilizer > 0) {
          add_target(RequestKind::kFertilize, target, -1,
                     ResourceKind::kItem, item::kFertilizer, fertilizer);
        }
        add_target(RequestKind::kDig, target, -1, ResourceKind::kNone, -1,
                   0);
      } else if (tile.kind == TileKind::kWeed) {
        add_target(RequestKind::kDig, target, -1, ResourceKind::kNone, -1,
                   0);
      } else if (tile.kind == TileKind::kStructure && !tile.has_animal) {
        for (int animal = 0; animal < kNumAnimals; ++animal) {
          const int item_index = item::kGoose + animal;
          const int64_t available = AccessibleItem(priv, busy, item_index);
          if (available > 0 && tile.structure == kAnimals[animal].structure) {
            add_target(RequestKind::kPlaceAnimal, target, item_index,
                       ResourceKind::kItem, item_index, available);
          }
        }
        add_target(RequestKind::kDig, target, -1, ResourceKind::kNone, -1,
                   0);
      } else if (tile.kind == TileKind::kStructure && tile.has_animal) {
        if (internal::TargetSupports(farm, day, RequestKind::kHarvest,
                                     target, -1)) {
          add_target(RequestKind::kHarvest, target, -1,
                     ResourceKind::kNone, -1, 0);
        }
        const int64_t wheat = AccessibleItem(priv, busy, item::kWheat);
        if (!tile.fed_today && wheat > 0) {
          add_target(RequestKind::kFeed, target, -1, ResourceKind::kItem,
                     item::kWheat, wheat);
        }
        if (!tile.cared_today) {
          add_target(RequestKind::kCare, target, -1,
                     ResourceKind::kNone, -1, 0);
        }
        if (tile.fertilizer_available) {
          add_target(RequestKind::kCollectFertilizer, target, -1,
                     ResourceKind::kNone, -1, 0);
        }
      }
    }

    const int64_t shed_room =
        std::max<int64_t>(0, config_.shed_capacity - ShedTotal(priv));
    for (int unit = 0; unit < unit_count; ++unit) {
      if (busy[unit]) continue;
      const int64_t load = internal::InventoryTotal(priv.inventories[unit]);
      if (load > 0 &&
          CompletionSteps(config_, farm, priv, busy, RequestKind::kBank, -1,
                          -1, unit) <= completion_limit) {
        Candidate bank = MakeCandidate(RequestKind::kBank);
        bank.fields[5] = unit + 1;
        bank.fields[6] = static_cast<int64_t>(ResourceKind::kShedRoom);
        bank.fields[8] = load;
        bank.fields[9] = shed_room;
        AddWorkCandidate(engine, player, std::move(bank));
      }

      for (int item_index = 0; item_index < kNumItems; ++item_index) {
        const int64_t load_upper =
            std::min<int64_t>(AccessibleItem(priv, busy, item_index),
                              maximum_quantity_);
        if (load_upper > 0 &&
            CompletionSteps(config_, farm, priv, busy, RequestKind::kLoad, -1,
                            item_index, unit) <= completion_limit) {
          for (int64_t quantity = 1; quantity <= load_upper; ++quantity) {
            Candidate candidate =
                MakeCandidate(RequestKind::kLoad, -1, item_index, quantity);
            candidate.fields[5] = unit + 1;
            candidate.fields[6] = static_cast<int64_t>(ResourceKind::kItem);
            candidate.fields[7] = item_index + 1;
            candidate.fields[8] = quantity;
            candidate.fields[9] = AccessibleItem(priv, busy, item_index);
            AddWorkCandidate(engine, player, std::move(candidate));
          }
        }

        const int64_t unload_upper =
            std::min(priv.inventories[unit].Get(item_index),
                     static_cast<int64_t>(maximum_quantity_));
        if (unload_upper > 0 &&
            CompletionSteps(config_, farm, priv, busy,
                            RequestKind::kUnload, -1, item_index,
                            unit) <= completion_limit) {
          for (int64_t quantity = 1; quantity <= unload_upper; ++quantity) {
            Candidate candidate =
                MakeCandidate(RequestKind::kUnload, -1, item_index, quantity);
            candidate.fields[5] = unit + 1;
            candidate.fields[6] =
                static_cast<int64_t>(ResourceKind::kShedRoom);
            candidate.fields[7] = item_index + 1;
            candidate.fields[8] = quantity;
            candidate.fields[9] = shed_room;
            AddWorkCandidate(engine, player, std::move(candidate));
          }
        }
      }
    }

    for (int target = 0; target < static_cast<int>(farm.tiles.size());
         ++target) {
      const int completion = CompletionSteps(config_, farm, priv, busy,
                                             RequestKind::kStage, target, -1,
                                             -1);
      if (completion > 0 && completion <= completion_limit) {
        AddWorkCandidate(
            engine, player,
            MakeCandidate(RequestKind::kStage, target, -1, 0));
      }
    }
    constexpr std::array<std::pair<int, int>, 4> kDirections = {
        std::pair{-1, 0}, std::pair{1, 0}, std::pair{0, -1},
        std::pair{0, 1}};
    for (int unit = 0; unit < unit_count; ++unit) {
      if (busy[unit] || destination_tasks_) continue;
      const auto [x, y] = internal::UnitPosition(farm, unit);
      for (const auto& [dx, dy] : kDirections) {
        const int target_x = x + dx;
        const int target_y = y + dy;
        if (target_x < 0 || target_x >= config_.board_size || target_y < 0 ||
            target_y >= config_.board_size) {
          continue;
        }
        Candidate stage = MakeCandidate(
            RequestKind::kStage, target_y * config_.board_size + target_x,
            -1, 0);
        stage.fields[5] = unit + 1;
        AddWorkCandidate(engine, player, std::move(stage));
      }
    }
  }

  for (const Job& job : jobs_) {
    Candidate cancel = MakeCandidate(RequestKind::kCancel);
    cancel.fields[4] = static_cast<int64_t>(job.id);
    cancel.fields[5] = job.unit + 1;
    AddWorkCandidate(engine, player, std::move(cancel));
  }
  candidate_mask_.assign(candidates_.size(), 1);
}

void Session::RefreshWorkMask(const Engine& engine, int player) {
  if (phase_ != Phase::kWork) return;
  const Farm& farm = engine.farm(player);
  const int day_remaining =
      config_.turns_per_day - engine.step_index() % config_.turns_per_day;
  std::array<int64_t, kNumCrops> used_seeds{};
  std::array<int64_t, kNumItems> used_items{};
  int64_t used_room = 0;
  std::vector<uint64_t> cancelled;
  for (const int index : selected_work_) {
    const Candidate& selected = candidates_[index];
    const auto resource = static_cast<ResourceKind>(selected.fields[6]);
    const int item_index = static_cast<int>(selected.fields[7]) - 1;
    if (resource == ResourceKind::kSeed && item_index >= 0) {
      used_seeds[item_index] += selected.fields[8];
    } else if (resource == ResourceKind::kItem && item_index >= 0) {
      used_items[item_index] += selected.fields[8];
    } else if (resource == ResourceKind::kShedRoom) {
      used_room += selected.fields[8];
    }
    if (selected.kind == RequestKind::kCancel) {
      cancelled.push_back(static_cast<uint64_t>(selected.fields[4]));
    }
  }

  const PrivateState& priv = engine.priv(player);
  const auto at_shed = [&](int unit) {
    const auto position = internal::UnitPosition(farm, unit);
    return position ==
           internal::NearestShed(position.first, position.second,
                                 config_.board_size);
  };
  const auto shed_item_before = [&](int item_index, int unit) {
    int64_t available = priv.shed[item_index];
    const auto apply = [&](RequestKind kind, int source_item, int64_t quantity,
                           int source_unit) {
      if (source_unit < 0 || source_unit >= unit || !at_shed(source_unit)) {
        return;
      }
      if (kind == RequestKind::kBank) {
        available += priv.inventories[source_unit].Get(item_index);
      } else if (kind == RequestKind::kUnload && source_item == item_index) {
        available += quantity;
      } else if (kind == RequestKind::kLoad && source_item == item_index) {
        available -= quantity;
      } else {
        const int required = internal::RequiredItem(kind, source_item);
        if (required == item_index &&
            priv.inventories[source_unit].Get(item_index) <= 0) {
          --available;
        }
      }
    };
    for (const Job& job : jobs_) {
      apply(job.kind, job.item, job.quantity, job.unit);
    }
    for (const int selected_index : selected_work_) {
      const Candidate& selected = candidates_[selected_index];
      apply(selected.kind, static_cast<int>(selected.fields[2]) - 1,
            selected.fields[3], static_cast<int>(selected.fields[5]) - 1);
    }
    return available;
  };
  const auto shed_room_before = [&](int unit) {
    int64_t available =
        std::max<int64_t>(0, config_.shed_capacity - ShedTotal(priv));
    const auto apply = [&](RequestKind kind, int64_t quantity,
                           int source_unit) {
      if (source_unit < 0 || source_unit >= unit || !at_shed(source_unit)) {
        return;
      }
      if (kind == RequestKind::kBank) {
        available -= internal::InventoryTotal(priv.inventories[source_unit]);
      } else if (kind == RequestKind::kUnload) {
        available -= quantity;
      } else if (kind == RequestKind::kLoad) {
        available += quantity;
      }
    };
    for (const Job& job : jobs_) {
      apply(job.kind, job.quantity, job.unit);
    }
    for (const int selected_index : selected_work_) {
      const Candidate& selected = candidates_[selected_index];
      apply(selected.kind, selected.fields[3],
            static_cast<int>(selected.fields[5]) - 1);
    }
    return available;
  };
  std::vector<uint8_t> assignment_busy(priv.inventories.size(), 0);
  for (const Job& job : jobs_) {
    if (std::find(cancelled.begin(), cancelled.end(), job.id) ==
            cancelled.end() &&
        job.unit >= 0 &&
        job.unit < static_cast<int>(assignment_busy.size())) {
      assignment_busy[job.unit] = 1;
    }
  }
  std::array<int64_t, kNumItems> assignment_shed{};
  for (int rank = 0; rank < static_cast<int>(selected_work_.size()); ++rank) {
    const Candidate& selected = candidates_[selected_work_[rank]];
    if (selected.kind == RequestKind::kCancel) continue;
    const internal::AssignmentPlan plan = internal::BestAssignment(
        config_, farm, priv, selected, assignment_busy, assignment_shed,
        day_remaining);
    if (plan.unit < 0) {
      throw std::logic_error("effect selection prefix became unassignable");
    }
    assignment_busy[plan.unit] = 1;
    // Expose the same provisional assignment used by legality and compilation.
    // A later cancellation can change it; every prefix refresh recomputes it.
    if (task_conditioning_) turn_work_[rank].unit = plan.unit;
    const int selected_item = static_cast<int>(selected.fields[2]) - 1;
    const int required =
        internal::RequiredItem(selected.kind, selected_item);
    if (plan.uses_shed && required >= 0) ++assignment_shed[required];
  }

  candidate_mask_.assign(candidates_.size(), 1);
  for (int index = 0; index < static_cast<int>(candidates_.size()); ++index) {
    const Candidate& candidate = candidates_[index];
    if (std::find(selected_work_.begin(), selected_work_.end(), index) !=
        selected_work_.end()) {
      candidate_mask_[index] = 0;
      continue;
    }
    if (candidate.kind == RequestKind::kStop) continue;
    if (candidate.kind != RequestKind::kCancel &&
        selected_new_jobs_ >= idle_units_) {
      candidate_mask_[index] = 0;
      continue;
    }
    if (candidate.kind == RequestKind::kCancel) {
      const uint64_t id = static_cast<uint64_t>(candidate.fields[4]);
      candidate_mask_[index] =
          std::none_of(cancelled.begin(), cancelled.end(),
                       [&](uint64_t value) { return value == id; });
      continue;
    }
    const auto resource = static_cast<ResourceKind>(candidate.fields[6]);
    const int item_index = static_cast<int>(candidate.fields[7]) - 1;
    const int64_t required = candidate.fields[8];
    int64_t used = 0;
    if (resource == ResourceKind::kSeed && item_index >= 0) {
      used = used_seeds[item_index];
    } else if (resource == ResourceKind::kItem && item_index >= 0) {
      used = used_items[item_index];
    } else if (resource == ResourceKind::kShedRoom) {
      used = used_room;
    }
    const bool exact_room = candidate.kind == RequestKind::kBank ||
                            candidate.kind == RequestKind::kUnload;
    if (resource != ResourceKind::kNone && !exact_room &&
        used + required > candidate.fields[9]) {
      candidate_mask_[index] = 0;
      continue;
    }
    if (candidate.kind == RequestKind::kLoad) {
      const int bound_unit = static_cast<int>(candidate.fields[5]) - 1;
      const int load_item = static_cast<int>(candidate.fields[2]) - 1;
      if (bound_unit < 0 || load_item < 0 ||
          shed_item_before(load_item, bound_unit) < candidate.fields[3]) {
        candidate_mask_[index] = 0;
        continue;
      }
    }
    if (exact_room) {
      const int bound_unit = static_cast<int>(candidate.fields[5]) - 1;
      if (bound_unit < 0 ||
          shed_room_before(bound_unit) < candidate.fields[8]) {
        candidate_mask_[index] = 0;
        continue;
      }
    }
    for (const int selected_index : selected_work_) {
      const Candidate& selected = candidates_[selected_index];
      if (internal::RequestsConflict(
              candidate.kind, static_cast<int>(candidate.fields[1]),
              static_cast<int>(candidate.fields[2]) - 1, selected.kind,
              static_cast<int>(selected.fields[1]),
              static_cast<int>(selected.fields[2]) - 1, farm)) {
        candidate_mask_[index] = 0;
        break;
      }
    }
    if (!candidate_mask_[index]) continue;
    for (const Job& job : jobs_) {
      if (std::find(cancelled.begin(), cancelled.end(), job.id) !=
          cancelled.end()) {
        continue;
      }
      if (internal::RequestsConflict(
              candidate.kind, static_cast<int>(candidate.fields[1]),
              static_cast<int>(candidate.fields[2]) - 1, job.kind,
              job.target, job.item, farm)) {
        candidate_mask_[index] = 0;
        break;
      }
    }
    if (!candidate_mask_[index]) continue;
    if (internal::BestAssignment(config_, farm, priv, candidate,
                                 assignment_busy, assignment_shed,
                                 day_remaining)
            .unit < 0) {
      candidate_mask_[index] = 0;
    }
  }
}

void Session::AddMarketCandidate(const Engine& engine, int player,
                                 Candidate candidate) {
  (void)engine;
  (void)player;
  const int item_index = static_cast<int>(candidate.fields[2]) - 1;
  const int64_t quantity = candidate.fields[3];
  candidate.features[2] = static_cast<float>(quantity) /
                          std::max(1, maximum_quantity_);
  candidate.features[3] = static_cast<float>(candidate.fields[9]) /
                          std::max(1, maximum_quantity_);
  candidate.features[4] =
      static_cast<float>(projected_farm_.money > 0.0
                             ? std::log1p(projected_farm_.money)
                             : 0.0) /
      16.0F;
  candidate.features[5] =
      static_cast<float>(std::max<int64_t>(
          0, config_.shed_capacity - ShedTotal(projected_priv_))) /
      std::max<int64_t>(1, config_.shed_capacity);
  if (item_index >= 0 && item_index < kNumProducts) {
    candidate.features[8] = static_cast<float>(
        projected_market_.prices[item_index] /
        std::max(1.0, config_.market_params[item_index].base));
    candidate.features[9] =
        static_cast<float>(projected_priv_.shed[item_index]) /
        std::max<int64_t>(1, config_.shed_capacity);
  }
  candidate.features[11] =
      static_cast<float>(turn_market_.size()) /
      std::max(1, config_.max_market_orders);

  uint64_t hash = internal::HashWord(kSpecVersion, kFnvOffset);
  hash = internal::HashWord(static_cast<uint64_t>(Phase::kMarket), hash);
  for (const SemanticAction& action : turn_market_) {
    for (const int64_t field : internal::EncodeAction(action)) {
      hash = internal::HashWord(static_cast<uint64_t>(field), hash);
    }
  }
  for (const int64_t field : candidate.fields) {
    hash = internal::HashWord(static_cast<uint64_t>(field), hash);
  }
  candidate.canonical_id = hash == 0 ? 1 : hash;
  candidates_.push_back(std::move(candidate));
}

void Session::GenerateMarketCandidates(const Engine& engine, int player) {
  candidates_.clear();
  candidate_mask_.clear();
  Candidate stop = MakeCandidate(RequestKind::kStop);
  stop.fields[10] = static_cast<int64_t>(turn_market_.size());
  AddMarketCandidate(engine, player, std::move(stop));
  Candidate skip = MakeCandidate(RequestKind::kSkipMarketSlot);
  skip.fields[10] = static_cast<int64_t>(turn_market_.size());
  AddMarketCandidate(engine, player, std::move(skip));

  const auto add_quantities = [&](RequestKind request, OrderKind order,
                                  int semantic_item, int order_item) {
    const int64_t upper = MarketQuantityUpper(order, order_item);
    for (int64_t quantity = 1; quantity <= upper; ++quantity) {
      Candidate candidate =
          MakeCandidate(request, -1, semantic_item, quantity);
      candidate.fields[9] = upper;
      candidate.fields[10] = static_cast<int64_t>(turn_market_.size());
      AddMarketCandidate(engine, player, std::move(candidate));
    }
  };
  for (int crop = 0; crop < kNumCrops; ++crop) {
    add_quantities(RequestKind::kBuySeed, OrderKind::kBuySeed, crop, crop);
  }
  for (const int product : {item::kWheat, item::kFertilizer}) {
    add_quantities(RequestKind::kBuyProduct, OrderKind::kBuyProduct, product,
                   product);
  }
  for (int animal = 0; animal < kNumAnimals; ++animal) {
    add_quantities(RequestKind::kBuyAnimal, OrderKind::kBuyAnimal,
                   item::kGoose + animal, animal);
  }
  for (int product = 0; product < kNumProducts; ++product) {
    add_quantities(RequestKind::kSell, OrderKind::kSell, product, product);
  }

  const auto atomic_succeeds = [&](OrderKind kind) {
    Farm farm = projected_farm_;
    PrivateState priv = projected_priv_;
    MarketState market = projected_market_;
    Farm dummy_farm;
    dummy_farm.tiles.assign(farm.tiles.size(), Tile{});
    PrivateState dummy_priv;
    dummy_priv.inventories.emplace_back();
    PlayerAction own;
    own.market.push_back(MarketOrder{kind, 0, 0});
    PlayerAction empty;
    std::array<Farm*, 2> farms = {&farm, &dummy_farm};
    std::array<PrivateState*, 2> privates = {&priv, &dummy_priv};
    ApplyMarketPhase(config_, farms, privates, &market, own, empty, nullptr);
    return kind == OrderKind::kHire
               ? priv.inventories.size() > projected_priv_.inventories.size()
               : farm.extra_unlocked > projected_farm_.extra_unlocked;
  };
  if (static_cast<int>(projected_priv_.inventories.size()) < unit_limit_ &&
      atomic_succeeds(OrderKind::kHire)) {
    Candidate hire = MakeCandidate(RequestKind::kHire);
    hire.fields[10] = static_cast<int64_t>(turn_market_.size());
    AddMarketCandidate(engine, player, std::move(hire));
  }
  if (atomic_succeeds(OrderKind::kBuyLand)) {
    Candidate land = MakeCandidate(RequestKind::kBuyLand);
    land.fields[10] = static_cast<int64_t>(turn_market_.size());
    AddMarketCandidate(engine, player, std::move(land));
  }
  candidate_mask_.assign(candidates_.size(), 1);
}

}  // namespace kagg::effects
