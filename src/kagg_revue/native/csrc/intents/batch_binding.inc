using IntentIntOutput = py::array_t<int64_t, py::array::c_style>;
using IntentFloatOutput = py::array_t<float, py::array::c_style>;
using IntentBoolOutput = py::array_t<bool, py::array::c_style>;

struct IntentRolloutRow {
  intents::Observation observation;
  uint8_t force_commit = 0;
  int episode_index = 0;
  int turn_index = 0;
  int selected = 0;
  int64_t behavior_index = -1;
  float log_probability = 0.0F;
  float value = 0.0F;
};

int IntentWidthBucket(std::size_t width) {
  int result = 0;
  for (std::size_t remaining = width; remaining != 0; remaining >>= 1) {
    result = result == 0 ? 1 : result << 1;
  }
  if (width != 0 && static_cast<std::size_t>(result) < width) result <<= 1;
  return result;
}

using IntentTeacherCriteria = std::vector<std::pair<int, int64_t>>;

int FindIntentTeacherCandidate(
    const intents::Observation& observation,
    const IntentTeacherCriteria& criteria) {
  int selected = -1;
  for (int index = 0;
       index < static_cast<int>(observation.candidates.size()); ++index) {
    const auto& fields = observation.candidates[index].fields;
    const bool matches = std::all_of(
        criteria.begin(), criteria.end(), [&](const auto& criterion) {
          return fields[criterion.first] == criterion.second;
        });
    if (!matches) continue;
    if (selected >= 0) {
      throw std::logic_error("intent teacher candidate is ambiguous");
    }
    selected = index;
  }
  return selected;
}

void SelectIntentTeacherCandidate(
    intents::Session* session, const Engine& engine, int player,
    const IntentTeacherCriteria& criteria, int episode_index, int turn_index,
    std::vector<IntentRolloutRow>* tape) {
  intents::Observation observation = session->Observe(engine, player);
  const int selected = FindIntentTeacherCandidate(observation, criteria);
  if (selected < 0) {
    std::string detail;
    for (const auto& [field, value] : criteria) {
      detail += " field" + std::to_string(field) + "=" +
                std::to_string(value);
    }
    throw std::logic_error("intent teacher candidate is unavailable:" +
                           detail);
  }
  tape->push_back(IntentRolloutRow{
      .observation = std::move(observation),
      .force_commit = 0,
      .episode_index = episode_index,
      .turn_index = turn_index,
      .selected = selected,
  });
  session->Select(selected);
}

class IntentLedgerBatch {
 public:
  IntentLedgerBatch(py::list session_owners, py::list engine_owners,
                    IntArray players, int workers)
      : session_owners_(std::move(session_owners)),
        engine_owners_(std::move(engine_owners)),
        workers_(workers) {
    owners_ = ParseIntentOwners(session_owners_, engine_owners_,
                                std::move(players), workers_);
    transaction_steps_.assign(owners_.sessions.size(), 0);
  }

  py::dict Observe(IntArray active, int maximum_steps) {
    Prepare(std::move(active), maximum_steps);
    return IntentObservationsToPy(prepared_observations_,
                                  prepared_force_commit_, workers_);
  }

  py::tuple ObserveCompact(IntArray active, int maximum_steps) {
    Prepare(std::move(active), maximum_steps);
    int maximum_candidates = 0;
    int maximum_work_orders = 0;
    int maximum_market_orders = 0;
    int singleton_masks = 0;
    for (int row = 0; row < static_cast<int>(prepared_observations_.size());
         ++row) {
      const intents::Observation& observation = prepared_observations_[row];
      maximum_candidates =
          std::max(maximum_candidates,
                   static_cast<int>(observation.candidates.size()));
      maximum_work_orders =
          std::max(maximum_work_orders,
                   static_cast<int>(observation.work_orders.size()));
      maximum_market_orders =
          std::max(maximum_market_orders,
                   static_cast<int>(observation.market_prefix.size()));
      const int commit_count = static_cast<int>(std::count_if(
          observation.candidates.begin(), observation.candidates.end(),
          [](const intents::Candidate& candidate) {
            return candidate.kind == intents::ChoiceKind::kCommit;
          }));
      const bool force = prepared_force_commit_[row] != 0 && commit_count == 1;
      singleton_masks += force || observation.candidates.size() == 1;
    }
    return py::make_tuple(maximum_candidates, maximum_work_orders,
                          maximum_market_orders, singleton_masks);
  }

  py::dict DeviceAuxiliary() const {
    const int batch = batch_size();
    if (batch < 1) {
      throw py::value_error("intent device auxiliary requires a batch");
    }
    std::vector<intents::DeviceAuxiliary> values(batch);
    std::exception_ptr first_error;
    std::mutex error_mutex;
    {
      py::gil_scoped_release release;
#ifdef _OPENMP
#pragma omp parallel for schedule(static) num_threads(workers_)
#endif
      for (int row = 0; row < batch; ++row) {
        try {
          values[row] = owners_.sessions[row]->DeviceStateAuxiliary(
              *owners_.engines[row], owners_.players[row]);
        } catch (...) {
          std::lock_guard<std::mutex> lock(error_mutex);
          if (!first_error) first_error = std::current_exception();
        }
      }
    }
    if (first_error) std::rethrow_exception(first_error);
    const int cells = static_cast<int>(values.front().asset_risk.size());
    py::array_t<int64_t> inactive({batch, cells, 2});
    py::array_t<int64_t> risk({batch, cells});
    for (int row = 0; row < batch; ++row) {
      if (static_cast<int>(values[row].inactive_status.size()) != cells ||
          static_cast<int>(values[row].asset_risk.size()) != cells) {
        throw py::value_error("intent device auxiliary changed board shape");
      }
      for (int target = 0; target < cells; ++target) {
        std::copy(values[row].inactive_status[target].begin(),
                  values[row].inactive_status[target].end(),
                  inactive.mutable_data(row, target));
        risk.mutable_at(row, target) = values[row].asset_risk[target];
      }
    }
    py::dict result;
    result["inactive_status"] = std::move(inactive);
    result["asset_risk"] = std::move(risk);
    return result;
  }

 private:
  void Prepare(IntArray active, int maximum_steps) {
    if (maximum_steps < 2) {
      throw py::value_error("intent transaction limit must be at least two");
    }
    prepared_rows_ = IntentActiveRows(std::move(active), batch_size());
    prepared_force_commit_.assign(prepared_rows_.size(), 0);
    for (int index = 0; index < static_cast<int>(prepared_rows_.size());
         ++index) {
      prepared_force_commit_[index] =
          transaction_steps_[prepared_rows_[index]] >= maximum_steps - 1;
    }
    prepared_observations_ = IntentObservationValues(
        IntentOwnerSubset(owners_, prepared_rows_),
        std::min(workers_, static_cast<int>(prepared_rows_.size())));
  }

 public:

  void WritePrepared(
      IntentIntOutput candidate_fields,
      IntentFloatOutput candidate_features,
      IntentBoolOutput candidate_mask, IntentIntOutput ledger,
      IntentIntOutput status, IntentIntOutput work_priorities,
      IntentIntOutput work_orders, IntentBoolOutput work_mask,
      IntentIntOutput positions, IntentIntOutput market_prefix,
      IntentBoolOutput market_mask, IntentIntOutput phase,
      IntentIntOutput model_rows) const {
    const int live_rows = static_cast<int>(prepared_observations_.size());
    if (live_rows < 1 || prepared_rows_.size() != prepared_observations_.size()) {
      throw py::value_error("intent batch has no prepared observation");
    }
    const int rows = static_cast<int>(candidate_fields.shape(0));
    const int candidate_capacity = static_cast<int>(candidate_fields.shape(1));
    const int work_capacity = static_cast<int>(work_orders.shape(1));
    const int market_capacity = static_cast<int>(market_prefix.shape(1));
    const int cells =
        static_cast<int>(prepared_observations_.front().ledger.size());
    const int work_kinds = static_cast<int>(intents::WorkKind::kStore);
    if (rows < live_rows || candidate_fields.ndim() != 3 ||
        candidate_fields.shape(2) != intents::kCandidateFieldCount ||
        candidate_features.ndim() != 3 ||
        candidate_features.shape(0) != rows ||
        candidate_features.shape(1) != candidate_capacity ||
        candidate_features.shape(2) != intents::kCandidateFeatureCount ||
        candidate_mask.ndim() != 2 || candidate_mask.shape(0) != rows ||
        candidate_mask.shape(1) != candidate_capacity ||
        ledger.ndim() != 3 || ledger.shape(0) != rows ||
        ledger.shape(1) != cells ||
        ledger.shape(2) != intents::kLedgerFieldCount || status.ndim() != 3 ||
        status.shape(0) != rows || status.shape(1) != cells ||
        status.shape(2) != intents::kStatusFieldCount ||
        work_priorities.ndim() != 3 || work_priorities.shape(0) != rows ||
        work_priorities.shape(1) != cells ||
        work_priorities.shape(2) != work_kinds || work_orders.ndim() != 3 ||
        work_orders.shape(0) != rows ||
        work_orders.shape(2) != intents::kWorkFieldCount ||
        work_mask.ndim() != 2 || work_mask.shape(0) != rows ||
        work_mask.shape(1) != work_capacity || positions.ndim() != 3 ||
        positions.shape(0) != rows || positions.shape(1) != 2 ||
        positions.shape(2) != intents::kPositionFieldCount ||
        market_prefix.ndim() != 3 || market_prefix.shape(0) != rows ||
        market_prefix.shape(2) != intents::kMarketFieldCount ||
        market_mask.ndim() != 2 || market_mask.shape(0) != rows ||
        market_mask.shape(1) != market_capacity || phase.ndim() != 1 ||
        phase.shape(0) != rows || model_rows.ndim() != 1 ||
        model_rows.shape(0) != rows) {
      throw py::value_error("intent prepared output buffers changed ABI");
    }
    std::fill_n(candidate_fields.mutable_data(), candidate_fields.size(),
                int64_t{0});
    std::fill_n(candidate_features.mutable_data(), candidate_features.size(),
                0.0F);
    std::fill_n(candidate_mask.mutable_data(), candidate_mask.size(), false);
    std::fill_n(work_orders.mutable_data(), work_orders.size(), int64_t{0});
    std::fill_n(work_mask.mutable_data(), work_mask.size(), false);
    std::fill_n(market_prefix.mutable_data(), market_prefix.size(), int64_t{0});
    std::fill_n(market_mask.mutable_data(), market_mask.size(), false);
    for (int row = 0; row < live_rows; ++row) {
      const intents::Observation& observation = prepared_observations_[row];
      if (observation.candidates.size() >
              static_cast<std::size_t>(candidate_capacity) ||
          observation.work_orders.size() >
              static_cast<std::size_t>(work_capacity) ||
          observation.market_prefix.size() >
              static_cast<std::size_t>(market_capacity) ||
          observation.ledger.size() != static_cast<std::size_t>(cells)) {
        throw py::value_error("intent prepared observation exceeds graph bucket");
      }
      const int commit_count = static_cast<int>(std::count_if(
          observation.candidates.begin(), observation.candidates.end(),
          [](const intents::Candidate& candidate) {
            return candidate.kind == intents::ChoiceKind::kCommit;
          }));
      const bool force = prepared_force_commit_[row] != 0 && commit_count == 1;
      for (int candidate = 0;
           candidate < static_cast<int>(observation.candidates.size());
           ++candidate) {
        std::copy(observation.candidates[candidate].fields.begin(),
                  observation.candidates[candidate].fields.end(),
                  candidate_fields.mutable_data(row, candidate));
        std::copy(observation.candidates[candidate].features.begin(),
                  observation.candidates[candidate].features.end(),
                  candidate_features.mutable_data(row, candidate));
        candidate_mask.mutable_at(row, candidate) =
            !force || observation.candidates[candidate].kind ==
                          intents::ChoiceKind::kCommit;
      }
      for (int target = 0; target < cells; ++target) {
        std::copy(observation.ledger[target].begin(),
                  observation.ledger[target].end(),
                  ledger.mutable_data(row, target));
        std::copy(observation.status[target].begin(),
                  observation.status[target].end(),
                  status.mutable_data(row, target));
        std::copy(observation.work_priorities[target].begin(),
                  observation.work_priorities[target].end(),
                  work_priorities.mutable_data(row, target));
      }
      for (int order = 0;
           order < static_cast<int>(observation.work_orders.size()); ++order) {
        std::copy(observation.work_orders[order].begin(),
                  observation.work_orders[order].end(),
                  work_orders.mutable_data(row, order));
        work_mask.mutable_at(row, order) = true;
      }
      for (int role = 0; role < 2; ++role) {
        std::copy(observation.positions[role].begin(),
                  observation.positions[role].end(),
                  positions.mutable_data(row, role));
      }
      for (int order = 0;
           order < static_cast<int>(observation.market_prefix.size()); ++order) {
        std::copy(observation.market_prefix[order].begin(),
                  observation.market_prefix[order].end(),
                  market_prefix.mutable_data(row, order));
        market_mask.mutable_at(row, order) = true;
      }
      phase.mutable_at(row) = static_cast<int64_t>(observation.phase);
      model_rows.mutable_at(row) = prepared_rows_[row];
    }
    const int last = live_rows - 1;
    for (int row = live_rows; row < rows; ++row) {
      std::copy_n(candidate_fields.data(last),
                  candidate_capacity * intents::kCandidateFieldCount,
                  candidate_fields.mutable_data(row));
      std::copy_n(candidate_features.data(last),
                  candidate_capacity * intents::kCandidateFeatureCount,
                  candidate_features.mutable_data(row));
      std::copy_n(candidate_mask.data(last), candidate_capacity,
                  candidate_mask.mutable_data(row));
      std::copy_n(ledger.data(last), cells * intents::kLedgerFieldCount,
                  ledger.mutable_data(row));
      std::copy_n(status.data(last), cells * intents::kStatusFieldCount,
                  status.mutable_data(row));
      std::copy_n(work_priorities.data(last), cells * work_kinds,
                  work_priorities.mutable_data(row));
      std::copy_n(work_orders.data(last),
                  work_capacity * intents::kWorkFieldCount,
                  work_orders.mutable_data(row));
      std::copy_n(work_mask.data(last), work_capacity,
                  work_mask.mutable_data(row));
      std::copy_n(positions.data(last), 2 * intents::kPositionFieldCount,
                  positions.mutable_data(row));
      std::copy_n(market_prefix.data(last),
                  market_capacity * intents::kMarketFieldCount,
                  market_prefix.mutable_data(row));
      std::copy_n(market_mask.data(last), market_capacity,
                  market_mask.mutable_data(row));
      phase.mutable_at(row) = phase.at(last);
      model_rows.mutable_at(row) = prepared_rows_.back();
    }
  }

  void RecordPrepared(IntentIntOutput selected,
                      IntentFloatOutput log_probability,
                      IntentFloatOutput value, int turn_index) {
    const int rows = static_cast<int>(prepared_observations_.size());
    if (rows < 1 || selected.ndim() != 1 || selected.shape(0) != rows ||
        log_probability.ndim() != 1 || log_probability.shape(0) != rows ||
        value.ndim() != 1 || value.shape(0) != rows || turn_index < 0) {
      throw py::value_error("intent recorded behavior differs from prepared rows");
    }
    for (int row = 0; row < rows; ++row) {
      intents::Observation& observation = prepared_observations_[row];
      const int choice = static_cast<int>(selected.at(row));
      if (choice < 0 ||
          choice >= static_cast<int>(observation.candidates.size())) {
        throw py::value_error("intent recorded candidate is out of range");
      }
      const int commit_count = static_cast<int>(std::count_if(
          observation.candidates.begin(), observation.candidates.end(),
          [](const intents::Candidate& candidate) {
            return candidate.kind == intents::ChoiceKind::kCommit;
          }));
      const bool force = prepared_force_commit_[row] != 0 && commit_count == 1;
      if (force && observation.candidates[choice].kind !=
                       intents::ChoiceKind::kCommit) {
        throw py::value_error("intent recorded a masked forced candidate");
      }
      tape_.push_back(IntentRolloutRow{
          .observation = std::move(observation),
          .force_commit = static_cast<uint8_t>(force),
          .episode_index = prepared_rows_[row],
          .turn_index = turn_index,
          .selected = choice,
          .behavior_index = -1,
          .log_probability = log_probability.at(row),
          .value = value.at(row),
      });
    }
  }

  void RecordPreparedIndexed(IntentIntOutput selected, int64_t behavior_offset,
                             int turn_index) {
    const int rows = static_cast<int>(prepared_observations_.size());
    if (rows < 1 || selected.ndim() != 1 || selected.shape(0) != rows ||
        behavior_offset < 0 || turn_index < 0) {
      throw py::value_error("intent device behavior differs from prepared rows");
    }
    for (int row = 0; row < rows; ++row) {
      intents::Observation& observation = prepared_observations_[row];
      const int choice = static_cast<int>(selected.at(row));
      if (choice < 0 ||
          choice >= static_cast<int>(observation.candidates.size())) {
        throw py::value_error("intent recorded candidate is out of range");
      }
      const int commit_count = static_cast<int>(std::count_if(
          observation.candidates.begin(), observation.candidates.end(),
          [](const intents::Candidate& candidate) {
            return candidate.kind == intents::ChoiceKind::kCommit;
          }));
      const bool force = prepared_force_commit_[row] != 0 && commit_count == 1;
      if (force && observation.candidates[choice].kind !=
                       intents::ChoiceKind::kCommit) {
        throw py::value_error("intent recorded a masked forced candidate");
      }
      tape_.push_back(IntentRolloutRow{
          .observation = std::move(observation),
          .force_commit = static_cast<uint8_t>(force),
          .episode_index = prepared_rows_[row],
          .turn_index = turn_index,
          .selected = choice,
          .behavior_index = behavior_offset + row,
      });
    }
  }

  int ReplayTransaction(IntentIntOutput selected,
                        IntentIntOutput selected_fields,
                        IntentIntOutput counts, int64_t behavior_offset,
                        int turn_index, int maximum_steps) {
    const int batch = batch_size();
    if (selected.ndim() != 2 || selected.shape(0) != batch ||
        selected_fields.ndim() != 3 || selected_fields.shape(0) != batch ||
        selected_fields.shape(1) != selected.shape(1) ||
        selected_fields.shape(2) != intents::kCandidateFieldCount ||
        counts.ndim() != 1 || counts.shape(0) != batch ||
        behavior_offset < 0 || turn_index < 0 || maximum_steps < 2) {
      throw py::value_error("intent device transaction trace changed ABI");
    }
    const int capacity = static_cast<int>(selected.shape(1));
    std::vector<std::vector<IntentRolloutRow>> rows(batch);
    std::vector<int> forced(batch, 0);
    std::exception_ptr first_error;
    std::mutex error_mutex;
    {
      py::gil_scoped_release release;
#ifdef _OPENMP
#pragma omp parallel for schedule(static) num_threads(workers_)
#endif
      for (int row = 0; row < batch; ++row) {
        try {
          const int decisions = static_cast<int>(counts.at(row));
          if (decisions < 1 || decisions > capacity) {
            throw std::out_of_range(
                "intent device transaction decision count is invalid");
          }
          rows[row].reserve(decisions);
          for (int step = 0; step < decisions; ++step) {
            intents::Observation observation = owners_.sessions[row]->Observe(
                *owners_.engines[row], owners_.players[row]);
            const int choice = static_cast<int>(selected.at(row, step));
            if (choice < 0 ||
                choice >= static_cast<int>(observation.candidates.size())) {
              throw std::out_of_range(
                  "intent device candidate mismatch at row " +
                  std::to_string(row) + " step " + std::to_string(step) +
                  " turn " + std::to_string(turn_index) +
                  ": selected " + std::to_string(choice) + " of native " +
                  std::to_string(observation.candidates.size()) +
                  ", device kind " +
                  std::to_string(selected_fields.at(row, step, 0)) +
                  ", device target " +
                  std::to_string(selected_fields.at(row, step, 1)));
            }
            const auto& native_fields = observation.candidates[choice].fields;
            for (int field = 0; field < intents::kCandidateFieldCount; ++field) {
              if (selected_fields.at(row, step, field) != native_fields[field]) {
                throw std::logic_error(
                    "intent device candidate fields diverged at row " +
                    std::to_string(row) + " step " + std::to_string(step) +
                    " turn " + std::to_string(turn_index) +
                    " field " + std::to_string(field));
              }
            }
            const int commit_count = static_cast<int>(std::count_if(
                observation.candidates.begin(), observation.candidates.end(),
                [](const intents::Candidate& candidate) {
                  return candidate.kind == intents::ChoiceKind::kCommit;
                }));
            const bool force = step >= maximum_steps - 1 && commit_count == 1;
            forced[row] += force ? 1 : 0;
            if (force && observation.candidates[choice].kind !=
                             intents::ChoiceKind::kCommit) {
              throw std::logic_error(
                  "intent device ignored the native forced commit");
            }
            rows[row].push_back(IntentRolloutRow{
                .observation = std::move(observation),
                .force_commit = static_cast<uint8_t>(force),
                .episode_index = row,
                .turn_index = turn_index,
                .selected = choice,
                .behavior_index =
                    behavior_offset + static_cast<int64_t>(step) * batch + row,
            });
            owners_.sessions[row]->Select(choice);
          }
          if (owners_.sessions[row]->phase() != intents::Phase::kDone) {
            throw std::logic_error(
                "intent device transaction ended before native COMMIT");
          }
        } catch (...) {
          std::lock_guard<std::mutex> lock(error_mutex);
          if (!first_error) first_error = std::current_exception();
        }
      }
    }
    if (first_error) std::rethrow_exception(first_error);
    for (auto& lane : rows) {
      tape_.insert(tape_.end(),
                   std::make_move_iterator(lane.begin()),
                   std::make_move_iterator(lane.end()));
    }
    return std::accumulate(forced.begin(), forced.end(), 0);
  }

  py::dict ApplyTeacherPlans(
      IntentIntOutput directive_operations,
      IntentIntOutput directive_targets, IntentIntOutput directive_items,
      IntentIntOutput directive_quantities, IntentIntOutput directive_counts,
      IntentIntOutput market_choices, IntentIntOutput market_items,
      IntentIntOutput market_quantities, IntentIntOutput market_counts,
      int turn_index, int maximum_steps) {
    const int batch = batch_size();
    const bool directive_shape =
        directive_operations.ndim() == 2 &&
        directive_operations.shape(0) == batch &&
        directive_targets.ndim() == 2 &&
        directive_targets.shape(0) == batch &&
        directive_targets.shape(1) == directive_operations.shape(1) &&
        directive_items.ndim() == 2 &&
        directive_items.shape(0) == batch &&
        directive_items.shape(1) == directive_operations.shape(1) &&
        directive_quantities.ndim() == 2 &&
        directive_quantities.shape(0) == batch &&
        directive_quantities.shape(1) == directive_operations.shape(1) &&
        directive_counts.ndim() == 1 && directive_counts.shape(0) == batch;
    const bool market_shape =
        market_choices.ndim() == 2 && market_choices.shape(0) == batch &&
        market_items.ndim() == 2 && market_items.shape(0) == batch &&
        market_items.shape(1) == market_choices.shape(1) &&
        market_quantities.ndim() == 2 &&
        market_quantities.shape(0) == batch &&
        market_quantities.shape(1) == market_choices.shape(1) &&
        market_counts.ndim() == 1 && market_counts.shape(0) == batch;
    if (!directive_shape || !market_shape || turn_index < 0 ||
        maximum_steps < 2) {
      throw py::value_error("intent teacher plan arrays changed ABI");
    }
    const int directive_capacity =
        static_cast<int>(directive_operations.shape(1));
    const int market_capacity = static_cast<int>(market_choices.shape(1));
    std::vector<std::vector<IntentRolloutRow>> rows(batch);
    std::vector<int64_t> decisions(batch, 0);
    std::vector<int64_t> clipped_market(batch, 0);
    std::vector<int64_t> omitted_sell(batch, 0);
    std::vector<int64_t> replaced_sell(batch, 0);
    std::exception_ptr first_error;
    std::mutex error_mutex;
    {
      py::gil_scoped_release release;
#ifdef _OPENMP
#pragma omp parallel for schedule(static) num_threads(workers_)
#endif
      for (int row = 0; row < batch; ++row) {
        try {
          intents::Session* session = owners_.sessions[row];
          const Engine& engine = *owners_.engines[row];
          const int player = owners_.players[row];
          const int unit_count = static_cast<int>(directive_counts.at(row));
          const int order_count = static_cast<int>(market_counts.at(row));
          if (unit_count < 1 || unit_count > directive_capacity ||
              unit_count !=
                  static_cast<int>(engine.priv(player).inventories.size()) ||
              order_count < 0 || order_count > market_capacity) {
            throw std::out_of_range(
                "intent teacher plan entity count is invalid");
          }

          const intents::Observation root = session->Observe(engine, player);
          for (int unit = 0; unit < unit_count; ++unit) {
            const int64_t operation =
                directive_operations.at(row, unit);
            const int64_t target = directive_targets.at(row, unit);
            const int64_t item = directive_items.at(row, unit);
            const int64_t quantity = directive_quantities.at(row, unit);
            if (operation <
                    static_cast<int64_t>(
                        intents::DirectiveOperation::kPosition) ||
                operation >
                    static_cast<int64_t>(intents::DirectiveOperation::kCare)) {
              throw std::out_of_range(
                  "intent teacher directive operation is invalid");
            }
            const int64_t work_kind = 9 + operation;
            const auto existing = std::find_if(
                root.work_orders.begin(), root.work_orders.end(),
                [&](const auto& work) {
                  return work[0] == work_kind && work[1] == target &&
                         work[2] == item + 1 && work[3] == quantity &&
                         work[4] ==
                             static_cast<int64_t>(intents::Priority::kHigh) &&
                         work[8] == unit + 1;
                });
            if (existing != root.work_orders.end()) continue;

            SelectIntentTeacherCandidate(
                session, engine, player,
                {{0, static_cast<int64_t>(
                         intents::ChoiceKind::kBeginDirective)}},
                row, turn_index, &rows[row]);
            SelectIntentTeacherCandidate(
                session, engine, player,
                {{0, static_cast<int64_t>(
                         intents::ChoiceKind::kSelectDirectiveUnit)},
                 {8, unit + 1}},
                row, turn_index, &rows[row]);
            SelectIntentTeacherCandidate(
                session, engine, player,
                {{0, static_cast<int64_t>(
                         intents::ChoiceKind::kSelectDirectiveOperation)},
                 {8, unit + 1},
                 {9, operation}},
                row, turn_index, &rows[row]);

            if (operation == static_cast<int64_t>(
                                 intents::DirectiveOperation::kWait)) {
              SelectIntentTeacherCandidate(
                  session, engine, player,
                  {{0, static_cast<int64_t>(
                           intents::ChoiceKind::kSetDirective)},
                   {7, quantity},
                   {8, unit + 1},
                   {9, operation}},
                  row, turn_index, &rows[row]);
              continue;
            }

            const bool needs_item =
                operation == static_cast<int64_t>(
                                 intents::DirectiveOperation::kPickup) ||
                operation == static_cast<int64_t>(
                                 intents::DirectiveOperation::kPlace) ||
                operation == static_cast<int64_t>(
                                 intents::DirectiveOperation::kPlant);
            const bool needs_quantity =
                operation == static_cast<int64_t>(
                                 intents::DirectiveOperation::kPickup) ||
                operation == static_cast<int64_t>(
                                 intents::DirectiveOperation::kPlace);
            SelectIntentTeacherCandidate(
                session, engine, player,
                {{0, static_cast<int64_t>(
                         needs_item
                             ? intents::ChoiceKind::kSelectDirectiveTarget
                             : intents::ChoiceKind::kSetDirective)},
                 {1, target},
                 {8, unit + 1},
                 {9, operation}},
                row, turn_index, &rows[row]);
            if (!needs_item) continue;
            SelectIntentTeacherCandidate(
                session, engine, player,
                {{0, static_cast<int64_t>(
                         needs_quantity
                             ? intents::ChoiceKind::kSelectDirectiveItem
                             : intents::ChoiceKind::kSetDirective)},
                 {1, target},
                 {2, item + 1},
                 {8, unit + 1},
                 {9, operation}},
                row, turn_index, &rows[row]);
            if (!needs_quantity) continue;
            SelectIntentTeacherCandidate(
                session, engine, player,
                {{0, static_cast<int64_t>(
                         intents::ChoiceKind::kSetDirective)},
                 {1, target},
                 {2, item + 1},
                 {7, quantity},
                 {8, unit + 1},
                 {9, operation}},
                row, turn_index, &rows[row]);
          }

          for (int order = 0; order < order_count; ++order) {
            const int64_t choice = market_choices.at(row, order);
            const int64_t item = market_items.at(row, order);
            const int64_t quantity = market_quantities.at(row, order);
            const bool immediate =
                choice == static_cast<int64_t>(
                              intents::ChoiceKind::kMarketHire) ||
                choice == static_cast<int64_t>(
                              intents::ChoiceKind::kMarketBuyLand);
            const bool quantity_order =
                choice >= static_cast<int64_t>(
                              intents::ChoiceKind::kMarketSell) &&
                choice <= static_cast<int64_t>(
                              intents::ChoiceKind::kMarketBuyAnimal);
            if (!immediate && !quantity_order) {
              throw std::out_of_range(
                  "intent teacher market choice is invalid");
            }
            intents::Observation market_root = session->Observe(engine, player);
            IntentTeacherCriteria root_criteria{{0, choice}};
            if (!immediate) root_criteria.emplace_back(2, item);
            const int selected =
                FindIntentTeacherCandidate(market_root, root_criteria);
            if (selected < 0 &&
                choice == static_cast<int64_t>(
                              intents::ChoiceKind::kMarketSell)) {
              root_criteria = {{0, static_cast<int64_t>(
                                       intents::ChoiceKind::kMarketSkipSlot)}};
              const int skip =
                  FindIntentTeacherCandidate(market_root, root_criteria);
              if (skip < 0) {
                throw std::logic_error(
                    "intent teacher market skip candidate is unavailable");
              }
              rows[row].push_back(IntentRolloutRow{
                  .observation = std::move(market_root),
                  .force_commit = 0,
                  .episode_index = row,
                  .turn_index = turn_index,
                  .selected = skip,
              });
              session->Select(skip);
              ++replaced_sell[row];
              continue;
            }
            if (selected < 0) {
              throw std::logic_error(
                  "intent teacher market root candidate is unavailable");
            }
            rows[row].push_back(IntentRolloutRow{
                .observation = std::move(market_root),
                .force_commit = 0,
                .episode_index = row,
                .turn_index = turn_index,
                .selected = selected,
            });
            session->Select(selected);
            if (immediate) continue;
            if (quantity < 1) {
              throw std::out_of_range(
                  "intent teacher market quantity is invalid");
            }
            intents::Observation quantities = session->Observe(engine, player);
            int quantity_choice = FindIntentTeacherCandidate(
                quantities,
                {{0, static_cast<int64_t>(
                         intents::ChoiceKind::kSelectMarketQuantity)},
                 {2, item},
                 {7, quantity}});
            if (quantity_choice < 0) {
              int64_t best = 0;
              for (const auto& candidate : quantities.candidates) {
                if (candidate.kind ==
                        intents::ChoiceKind::kSelectMarketQuantity &&
                    candidate.fields[2] == item &&
                    candidate.fields[7] <= quantity) {
                  best = std::max(best, candidate.fields[7]);
                }
              }
              if (best < 1) {
                throw std::logic_error(
                    "intent teacher market quantity has no successor");
              }
              quantity_choice = FindIntentTeacherCandidate(
                  quantities,
                  {{0, static_cast<int64_t>(
                           intents::ChoiceKind::kSelectMarketQuantity)},
                   {2, item},
                   {7, best}});
              ++clipped_market[row];
            }
            rows[row].push_back(IntentRolloutRow{
                .observation = std::move(quantities),
                .force_commit = 0,
                .episode_index = row,
                .turn_index = turn_index,
                .selected = quantity_choice,
            });
            session->Select(quantity_choice);
          }
          SelectIntentTeacherCandidate(
              session, engine, player,
              {{0, static_cast<int64_t>(intents::ChoiceKind::kCommit)}},
              row, turn_index, &rows[row]);
          if (session->phase() != intents::Phase::kDone) {
            throw std::logic_error(
                "intent teacher transaction ended before COMMIT");
          }
          decisions[row] = static_cast<int64_t>(rows[row].size());
          if (decisions[row] > maximum_steps) {
            throw std::out_of_range(
                "intent teacher transaction exceeds configured capacity");
          }
        } catch (...) {
          std::lock_guard<std::mutex> lock(error_mutex);
          if (!first_error) first_error = std::current_exception();
        }
      }
    }
    if (first_error) std::rethrow_exception(first_error);
    for (int row = 0; row < batch; ++row) {
      transaction_steps_[row] = static_cast<int>(decisions[row]);
      auto& lane = rows[row];
      tape_.insert(tape_.end(), std::make_move_iterator(lane.begin()),
                   std::make_move_iterator(lane.end()));
    }
    py::array_t<int64_t> decision_output(batch);
    py::array_t<int64_t> clipped_output(batch);
    py::array_t<int64_t> omitted_output(batch);
    py::array_t<int64_t> replaced_output(batch);
    std::copy(decisions.begin(), decisions.end(),
              decision_output.mutable_data());
    std::copy(clipped_market.begin(), clipped_market.end(),
              clipped_output.mutable_data());
    std::copy(omitted_sell.begin(), omitted_sell.end(),
              omitted_output.mutable_data());
    std::copy(replaced_sell.begin(), replaced_sell.end(),
              replaced_output.mutable_data());
    py::dict result;
    result["decision_counts"] = std::move(decision_output);
    result["clipped_market_quantities"] = std::move(clipped_output);
    result["omitted_sell_orders"] = std::move(omitted_output);
    result["replaced_unavailable_sell_slots"] = std::move(replaced_output);
    return result;
  }

 private:
  py::dict ExportRows(
      const std::vector<std::vector<std::size_t>>& episode_rows) const {
    std::vector<const intents::Observation*> observations;
    std::vector<uint8_t> force_commit;
    std::vector<std::size_t> flat_indices;
    const std::size_t row_count = std::accumulate(
        episode_rows.begin(), episode_rows.end(), std::size_t{0},
        [](std::size_t total, const std::vector<std::size_t>& rows) {
          return total + rows.size();
        });
    observations.reserve(row_count);
    force_commit.reserve(row_count);
    flat_indices.reserve(row_count);
    for (const auto& rows : episode_rows) {
      for (const std::size_t index : rows) {
        observations.push_back(&tape_[index].observation);
        force_commit.push_back(tape_[index].force_commit);
        flat_indices.push_back(index);
      }
    }
    py::dict result = IntentObservationPointersToPy<int32_t>(
        observations, force_commit, false, workers_);
    const py::ssize_t rows = static_cast<py::ssize_t>(row_count);
    py::array_t<int64_t> selected(rows);
    py::array_t<uint64_t> selected_canonical_id(rows);
    py::array_t<int64_t> behavior_index(rows);
    py::array_t<float> old_log_probability(rows);
    py::array_t<float> old_value(rows);
    py::array_t<bool> policy_mask(rows);
    py::array_t<int64_t> episode_index(rows);
    py::array_t<int64_t> turn_index(rows);
    const int worker_count = std::max(
        1, std::min(workers_, static_cast<int>(flat_indices.size())));
    {
      py::gil_scoped_release release;
#ifdef _OPENMP
#pragma omp parallel for schedule(static) num_threads(worker_count)
#endif
      for (py::ssize_t output = 0; output < rows; ++output) {
        const IntentRolloutRow& row = tape_[flat_indices[output]];
        selected.mutable_at(output) = row.selected;
        selected_canonical_id.mutable_at(output) =
            row.observation.candidates[row.selected].canonical_id;
        behavior_index.mutable_at(output) = row.behavior_index;
        old_log_probability.mutable_at(output) = row.log_probability;
        old_value.mutable_at(output) = row.value;
        policy_mask.mutable_at(output) =
            !row.force_commit && row.observation.candidates.size() > 1;
        episode_index.mutable_at(output) = row.episode_index;
        turn_index.mutable_at(output) = row.turn_index;
      }
    }
    result["selected"] = std::move(selected);
    result["selected_canonical_id"] = std::move(selected_canonical_id);
    result["behavior_index"] = std::move(behavior_index);
    result["old_log_probability"] = std::move(old_log_probability);
    result["old_value"] = std::move(old_value);
    result["policy_mask"] = std::move(policy_mask);
    result["episode_index"] = std::move(episode_index);
    result["turn_index"] = std::move(turn_index);
    return result;
  }

 public:

  py::list ExportRolloutBuckets() {
    if (tape_.empty()) {
      throw py::value_error("intent rollout tape is empty");
    }
    std::map<int, std::vector<std::vector<std::size_t>>> buckets;
    for (std::size_t index = 0; index < tape_.size(); ++index) {
      const IntentRolloutRow& row = tape_[index];
      if (row.episode_index < 0 || row.episode_index >= batch_size()) {
        throw std::logic_error("intent rollout row escaped its episode batch");
      }
      const int width = IntentWidthBucket(row.observation.candidates.size());
      auto bucket = buckets
                        .try_emplace(width,
                                     static_cast<std::size_t>(batch_size()))
                        .first;
      bucket->second[static_cast<std::size_t>(row.episode_index)].push_back(
          index);
    }
    py::list result;
    for (const auto& bucket : buckets) {
      result.append(ExportRows(bucket.second));
    }
    {
      py::gil_scoped_release release;
      tape_.clear();
    }
    return result;
  }

  py::dict ExportRollout() {
    if (tape_.empty()) {
      throw py::value_error("intent rollout tape is empty");
    }
    std::vector<const intents::Observation*> observations;
    std::vector<uint8_t> force_commit;
    observations.reserve(tape_.size());
    force_commit.reserve(tape_.size());
    for (const IntentRolloutRow& row : tape_) {
      observations.push_back(&row.observation);
      force_commit.push_back(row.force_commit);
    }
    py::dict result = IntentObservationPointersToPy<int64_t>(
        observations, force_commit, false, workers_);
    const py::ssize_t rows = static_cast<py::ssize_t>(tape_.size());
    py::array_t<int64_t> selected(rows);
    py::array_t<uint64_t> selected_canonical_id(rows);
    py::array_t<float> old_log_probability(rows);
    py::array_t<float> old_value(rows);
    py::array_t<bool> policy_mask(rows);
    py::array_t<int64_t> episode_index(rows);
    py::array_t<int64_t> turn_index(rows);
    for (py::ssize_t index = 0; index < rows; ++index) {
      const IntentRolloutRow& row = tape_[index];
      selected.mutable_at(index) = row.selected;
      selected_canonical_id.mutable_at(index) =
          row.observation.candidates[row.selected].canonical_id;
      old_log_probability.mutable_at(index) = row.log_probability;
      old_value.mutable_at(index) = row.value;
      policy_mask.mutable_at(index) =
          !row.force_commit && row.observation.candidates.size() > 1;
      episode_index.mutable_at(index) = row.episode_index;
      turn_index.mutable_at(index) = row.turn_index;
    }
    result["selected"] = std::move(selected);
    result["selected_canonical_id"] = std::move(selected_canonical_id);
    result["old_log_probability"] = std::move(old_log_probability);
    result["old_value"] = std::move(old_value);
    result["policy_mask"] = std::move(policy_mask);
    result["episode_index"] = std::move(episode_index);
    result["turn_index"] = std::move(turn_index);
    tape_.clear();
    return result;
  }

  py::array_t<int64_t> Select(IntArray active, IntArray candidate_indices) {
    const std::vector<int> rows =
        IntentActiveRows(std::move(active), batch_size());
    const py::buffer_info index_info = candidate_indices.request();
    if (index_info.ndim != 1 ||
        index_info.shape[0] != static_cast<py::ssize_t>(rows.size())) {
      throw py::value_error("intent selected indices must align with active rows");
    }
    const auto* indices = static_cast<const int64_t*>(index_info.ptr);
    py::array_t<int64_t> phases(rows.size());
    auto* phase_data = phases.mutable_data();
    std::exception_ptr first_error;
    std::mutex error_mutex;
    const int workers = std::min(workers_, static_cast<int>(rows.size()));
    {
      py::gil_scoped_release release;
#ifdef _OPENMP
#pragma omp parallel for schedule(static) num_threads(workers)
#endif
      for (int index = 0; index < static_cast<int>(rows.size()); ++index) {
        try {
          phase_data[index] = static_cast<int64_t>(
              owners_.sessions[rows[index]]->Select(indices[index]));
        } catch (...) {
          std::lock_guard<std::mutex> lock(error_mutex);
          if (!first_error) first_error = std::current_exception();
        }
      }
    }
    if (first_error) std::rethrow_exception(first_error);
    for (const int row : rows) ++transaction_steps_[row];
    return phases;
  }

  void ResetTransaction() {
    std::fill(transaction_steps_.begin(), transaction_steps_.end(), 0);
  }

  int batch_size() const {
    return static_cast<int>(owners_.sessions.size());
  }

 private:
  py::list session_owners_;
  py::list engine_owners_;
  IntentOwners owners_;
  int workers_;
  std::vector<int> transaction_steps_;
  std::vector<int> prepared_rows_;
  std::vector<intents::Observation> prepared_observations_;
  std::vector<uint8_t> prepared_force_commit_;
  std::vector<IntentRolloutRow> tape_;
};
