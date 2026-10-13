#include "tasks/session.hpp"

#include <algorithm>
#include <set>
#include <tuple>

namespace kagg::tasks {

bool IsOfficial(Operation operation) {
  return static_cast<int64_t>(operation) >=
         static_cast<int64_t>(Operation::kPickup);
}

bool NeedsQuantity(Operation operation) {
  return operation == Operation::kPickup || operation == Operation::kPlace;
}

int ManhattanDistance(int left_x, int left_y, int right_x, int right_y) {
  return std::abs(left_x - right_x) + std::abs(left_y - right_y);
}

std::vector<Candidate> Session::BuildCatalog() const {
  std::vector<Candidate> result;
  std::set<std::tuple<int64_t, int, int, int>> seen;
  const auto append = [&result, &seen](Operation operation, int argument,
                                       int x, int y) {
    const auto key = std::tuple(static_cast<int64_t>(operation), argument, x, y);
    if (seen.insert(key).second) {
      result.push_back(Candidate{operation, argument, x, y});
    }
  };
  append(Operation::kEnd, -1, -1, -1);
  append(Operation::kWait, -1, -1, -1);
  for (int y = 0; y < config_.board_size; ++y) {
    for (int x = 0; x < config_.board_size; ++x) {
      append(Operation::kPosition, -1, x, y);
    }
  }
  const auto shed = ShedAccessTiles(config_.board_size);
  for (int item_index = 0; item_index < kNumItems; ++item_index) {
    for (const auto& [x, y] : shed) {
      append(Operation::kPickup, item_index, x, y);
    }
  }
  for (const auto& [x, y] : shed) {
    append(Operation::kDrop, -1, x, y);
  }
  for (int item_index = 0; item_index < kNumItems; ++item_index) {
    for (const auto& [x, y] : shed) {
      append(Operation::kPlace, item_index, x, y);
    }
  }
  for (int animal = 0; animal < kNumAnimals; ++animal) {
    for (int y = 0; y < config_.board_size; ++y) {
      for (int x = 0; x < config_.board_size; ++x) {
        append(Operation::kPlace, item::kGoose + animal, x, y);
      }
    }
  }
  for (int crop = 0; crop < kNumCrops; ++crop) {
    for (int y = 0; y < config_.board_size; ++y) {
      for (int x = 0; x < config_.board_size; ++x) {
        append(Operation::kPlant, crop, x, y);
      }
    }
  }
  constexpr std::array<Operation, 9> operations = {
      Operation::kWater,
      Operation::kHarvest,
      Operation::kFertilize,
      Operation::kDig,
      Operation::kBuildCoop,
      Operation::kBuildPasture,
      Operation::kFeed,
      Operation::kCollectFertilizer,
      Operation::kCare,
  };
  for (Operation operation : operations) {
    for (int y = 0; y < config_.board_size; ++y) {
      for (int x = 0; x < config_.board_size; ++x) {
        append(operation, -1, x, y);
      }
    }
  }
  return result;
}

std::vector<std::string> CandidateFeatureNames() {
  return {
      "present",
      "distance_fraction",
      "arrival_fraction",
      "earliest_completion_fraction",
      "remaining_after_fraction",
      "wait_fraction",
      "exact_feasible",
      "currently_legal",
      "declared_target_conflicts",
      "declared_resource_conflicts",
      "reason_feasible",
      "reason_end",
      "reason_out_of_time",
      "reason_no_progress",
      "reason_invalid_geometry",
      "target_x_fraction",
      "target_y_fraction",
      "operation_turns",
  };
}

std::vector<std::string> RootFeatureNames() {
  return {
      "hour_fraction",
      "day_fraction",
      "unit_index_fraction",
      "unit_count_fraction",
      "simulated_x_fraction",
      "simulated_y_fraction",
      "available_fraction",
      "remaining_fraction",
      "new_task_count_fraction",
      "retained_suffix_fraction",
      "history_fill_fraction",
      "successful_task_fraction",
      "failed_task_fraction",
      "forced_end_fraction",
      "reason_day_start",
      "reason_new_unit",
      "reason_queue_empty",
      "reason_task_completed",
      "reason_target_invalid",
      "reason_operation_failed",
      "reason_deadline_missed",
      "mode_continue_legal",
      "mode_rewrite_legal",
      "planning_first_task",
  };
}

std::vector<std::string> TaskFieldNames() {
  return {
      "unit_index",
      "operation",
      "argument_plus_one",
      "target_x_plus_one",
      "target_y_plus_one",
      "quantity",
      "earliest_start",
      "deadline",
      "status_token",
  };
}

}  // namespace kagg::tasks
