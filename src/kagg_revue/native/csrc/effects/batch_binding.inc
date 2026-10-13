using EffectIntInput = py::array_t<int64_t, py::array::c_style>;
using EffectFloatInput = py::array_t<float, py::array::c_style>;
using EffectBoolOutput = py::array_t<bool, py::array::c_style>;

struct EffectRolloutRow {
  effects::Observation observation;
  int episode_index = 0;
  int turn_index = 0;
  int transaction_step = 0;
  int selected = 0;
  int64_t behavior_index = -1;
  float log_probability = 0.0F;
  float value = 0.0F;
  uint8_t value_mask = 0;
};

int EffectWidthBucket(std::size_t width) {
  int result = 1;
  while (static_cast<std::size_t>(result) < width) result <<= 1;
  return result;
}

std::vector<int> EffectActiveRows(IntArray active, int batch) {
  const py::buffer_info info = active.request();
  if (info.ndim != 1 || info.shape[0] < 1) {
    throw py::value_error("effect active rows must be a nonempty vector");
  }
  const auto* values = static_cast<const int64_t*>(info.ptr);
  std::vector<uint8_t> seen(static_cast<std::size_t>(batch), 0);
  std::vector<int> rows;
  rows.reserve(static_cast<std::size_t>(info.shape[0]));
  for (py::ssize_t index = 0; index < info.shape[0]; ++index) {
    const int row = static_cast<int>(values[index]);
    if (row < 0 || row >= batch || seen[row]) {
      throw py::value_error("effect active row is invalid or duplicated");
    }
    seen[row] = 1;
    rows.push_back(row);
  }
  return rows;
}

py::dict EffectObservationValuesToPy(
    const std::vector<effects::Observation>& observations, int workers) {
  const int batch = static_cast<int>(observations.size());
  if (batch < 1) {
    throw py::value_error("effect observation batch is empty");
  }
  int candidate_width = 0;
  int job_width = 0;
  int work_width = 0;
  int market_width = 0;
  int previous_width = 0;
  for (const effects::Observation& observation : observations) {
    candidate_width = std::max(
        candidate_width, static_cast<int>(observation.candidates.size()));
    job_width =
        std::max(job_width, static_cast<int>(observation.jobs.size()));
    work_width = std::max(
        work_width, static_cast<int>(observation.work_prefix.size()));
    market_width = std::max(
        market_width, static_cast<int>(observation.market_prefix.size()));
    previous_width = std::max(
        previous_width, static_cast<int>(observation.previous_action.size()));
  }
  py::array_t<int64_t> fields(
      {batch, candidate_width, effects::kCandidateFieldCount});
  py::array_t<float> features(
      {batch, candidate_width, effects::kCandidateFeatureCount});
  py::array_t<bool> mask({batch, candidate_width});
  py::array_t<uint64_t> ids({batch, candidate_width});
  py::array_t<int64_t> counts(batch);
  py::array_t<int64_t> phases(batch);
  py::array_t<int64_t> work_limits(batch);
  py::array_t<int64_t> jobs(
      {batch, job_width, effects::kJobFieldCount});
  py::array_t<int64_t> job_counts(batch);
  py::array_t<int64_t> work(
      {batch, work_width, effects::kActionFieldCount});
  py::array_t<int64_t> work_counts(batch);
  py::array_t<int64_t> market(
      {batch, market_width, effects::kActionFieldCount});
  py::array_t<int64_t> market_counts(batch);
  py::array_t<int64_t> previous(
      {batch, previous_width, effects::kActionFieldCount});
  py::array_t<int64_t> previous_counts(batch);
  std::fill_n(fields.mutable_data(), fields.size(), int64_t{0});
  std::fill_n(features.mutable_data(), features.size(), 0.0F);
  std::fill_n(mask.mutable_data(), mask.size(), false);
  std::fill_n(ids.mutable_data(), ids.size(), uint64_t{0});
  std::fill_n(jobs.mutable_data(), jobs.size(), int64_t{0});
  std::fill_n(work.mutable_data(), work.size(), int64_t{0});
  std::fill_n(market.mutable_data(), market.size(), int64_t{0});
  std::fill_n(previous.mutable_data(), previous.size(), int64_t{0});
  const int worker_count = std::max(1, std::min(workers, batch));
  {
    py::gil_scoped_release release;
#ifdef _OPENMP
#pragma omp parallel for schedule(static) num_threads(worker_count)
#endif
    for (int row = 0; row < batch; ++row) {
      const effects::Observation& observation = observations[row];
      counts.mutable_at(row) = observation.candidates.size();
      phases.mutable_at(row) = static_cast<int64_t>(observation.phase);
      work_limits.mutable_at(row) = observation.work_limit;
      job_counts.mutable_at(row) = observation.jobs.size();
      work_counts.mutable_at(row) = observation.work_prefix.size();
      market_counts.mutable_at(row) = observation.market_prefix.size();
      previous_counts.mutable_at(row) = observation.previous_action.size();
      for (int index = 0;
           index < static_cast<int>(observation.candidates.size()); ++index) {
        std::copy(observation.candidates[index].fields.begin(),
                  observation.candidates[index].fields.end(),
                  fields.mutable_data(row, index));
        std::copy(observation.candidates[index].features.begin(),
                  observation.candidates[index].features.end(),
                  features.mutable_data(row, index));
        mask.mutable_at(row, index) = observation.candidate_mask[index] != 0;
        ids.mutable_at(row, index) =
            observation.candidates[index].canonical_id;
      }
      for (int index = 0;
           index < static_cast<int>(observation.jobs.size()); ++index) {
        std::copy(observation.jobs[index].begin(),
                  observation.jobs[index].end(), jobs.mutable_data(row, index));
      }
      const auto copy_actions = [row](const auto& source, auto* destination) {
        for (int index = 0; index < static_cast<int>(source.size()); ++index) {
          std::copy(source[index].begin(), source[index].end(),
                    destination->mutable_data(row, index));
        }
      };
      copy_actions(observation.work_prefix, &work);
      copy_actions(observation.market_prefix, &market);
      copy_actions(observation.previous_action, &previous);
    }
  }
  py::dict result;
  result["candidate_fields"] = std::move(fields);
  result["candidate_features"] = std::move(features);
  result["candidate_mask"] = std::move(mask);
  result["canonical_id"] = std::move(ids);
  result["candidate_counts"] = std::move(counts);
  result["phase"] = std::move(phases);
  result["work_limit"] = std::move(work_limits);
  result["jobs"] = std::move(jobs);
  result["job_counts"] = std::move(job_counts);
  result["work_prefix"] = std::move(work);
  result["work_counts"] = std::move(work_counts);
  result["market_prefix"] = std::move(market);
  result["market_counts"] = std::move(market_counts);
  result["previous_action"] = std::move(previous);
  result["previous_counts"] = std::move(previous_counts);
  return result;
}

class AtomicEffectBatch {
 public:
  AtomicEffectBatch(py::list session_owners, py::list engine_owners,
                    IntArray players, int workers, bool record_rollout)
      : session_owners_(std::move(session_owners)),
        engine_owners_(std::move(engine_owners)),
        workers_(workers),
        record_rollout_(record_rollout) {
    owners_ = ParseEffectOwners(session_owners_, engine_owners_,
                                 std::move(players), workers_);
    factor_counts_.assign(owners_.sessions.size(), 0);
  }

  py::dict Observe(IntArray active) {
    Prepare(std::move(active));
    return EffectObservationValuesToPy(prepared_observations_, workers_);
  }

  py::tuple ObserveCompact(IntArray active) {
    Prepare(std::move(active));
    int candidates = 0;
    int jobs = 0;
    int work = 0;
    int market = 0;
    int previous = 0;
    int policy_rows = 0;
    for (const effects::Observation& observation : prepared_observations_) {
      candidates = std::max(
          candidates, static_cast<int>(observation.candidates.size()));
      jobs = std::max(jobs, static_cast<int>(observation.jobs.size()));
      work = std::max(work,
                      static_cast<int>(observation.work_prefix.size()));
      market = std::max(market,
                        static_cast<int>(observation.market_prefix.size()));
      previous =
          std::max(previous,
                   static_cast<int>(observation.previous_action.size()));
      policy_rows +=
          std::count(observation.candidate_mask.begin(),
                     observation.candidate_mask.end(), uint8_t{1}) > 1;
    }
    return py::make_tuple(candidates, jobs, work, market, previous,
                          policy_rows);
  }

 private:
  void Prepare(IntArray active) {
    prepared_rows_ = EffectActiveRows(std::move(active), batch_size());
    const int rows = static_cast<int>(prepared_rows_.size());
    prepared_observations_.resize(static_cast<std::size_t>(rows));
    std::exception_ptr first_error;
    std::mutex error_mutex;
    const int worker_count = std::max(1, std::min(workers_, rows));
    {
      py::gil_scoped_release release;
#ifdef _OPENMP
#pragma omp parallel for schedule(static) num_threads(worker_count)
#endif
      for (int index = 0; index < rows; ++index) {
        try {
          const int row = prepared_rows_[index];
          prepared_observations_[index] = owners_.sessions[row]->Observe(
              *owners_.engines[row], owners_.players[row]);
        } catch (...) {
          std::lock_guard<std::mutex> lock(error_mutex);
          if (!first_error) first_error = std::current_exception();
        }
      }
    }
    if (first_error) std::rethrow_exception(first_error);
  }

 public:
  void WritePrepared(
      EffectIntInput candidate_fields, EffectFloatInput candidate_features,
      EffectBoolOutput candidate_mask, EffectIntInput jobs,
      EffectBoolOutput job_mask, EffectIntInput work_prefix,
      EffectBoolOutput work_mask, EffectIntInput market_prefix,
      EffectBoolOutput market_mask, EffectIntInput previous_action,
      EffectBoolOutput previous_mask, EffectIntInput phase,
      EffectIntInput work_limit, EffectIntInput model_rows) const {
    const int live_rows = static_cast<int>(prepared_observations_.size());
    if (live_rows < 1 || prepared_rows_.size() != prepared_observations_.size()) {
      throw py::value_error("effect batch has no prepared observation");
    }
    if (candidate_fields.ndim() != 3 || candidate_features.ndim() != 3 ||
        candidate_mask.ndim() != 2 || jobs.ndim() != 3 ||
        job_mask.ndim() != 2 || work_prefix.ndim() != 3 ||
        work_mask.ndim() != 2 || market_prefix.ndim() != 3 ||
        market_mask.ndim() != 2 || previous_action.ndim() != 3 ||
        previous_mask.ndim() != 2 || phase.ndim() != 1 ||
        work_limit.ndim() != 1 || model_rows.ndim() != 1) {
      throw py::value_error("effect prepared output buffers changed ABI");
    }
    const int rows = static_cast<int>(candidate_fields.shape(0));
    const int candidate_capacity =
        static_cast<int>(candidate_fields.shape(1));
    const int job_capacity = static_cast<int>(jobs.shape(1));
    const int work_capacity = static_cast<int>(work_prefix.shape(1));
    const int market_capacity = static_cast<int>(market_prefix.shape(1));
    const int previous_capacity =
        static_cast<int>(previous_action.shape(1));
    if (rows < live_rows ||
        candidate_fields.shape(2) != effects::kCandidateFieldCount ||
        candidate_features.shape(0) != rows ||
        candidate_features.shape(1) != candidate_capacity ||
        candidate_features.shape(2) != effects::kCandidateFeatureCount ||
        candidate_mask.ndim() != 2 || candidate_mask.shape(0) != rows ||
        candidate_mask.shape(1) != candidate_capacity ||
        jobs.shape(0) != rows ||
        jobs.shape(2) != effects::kJobFieldCount || job_mask.ndim() != 2 ||
        job_mask.shape(0) != rows || job_mask.shape(1) != job_capacity ||
        work_prefix.ndim() != 3 || work_prefix.shape(0) != rows ||
        work_prefix.shape(2) != effects::kActionFieldCount ||
        work_mask.ndim() != 2 || work_mask.shape(0) != rows ||
        work_mask.shape(1) != work_capacity || market_prefix.ndim() != 3 ||
        market_prefix.shape(0) != rows ||
        market_prefix.shape(2) != effects::kActionFieldCount ||
        market_mask.ndim() != 2 || market_mask.shape(0) != rows ||
        market_mask.shape(1) != market_capacity ||
        previous_action.ndim() != 3 || previous_action.shape(0) != rows ||
        previous_action.shape(2) != effects::kActionFieldCount ||
        previous_mask.ndim() != 2 || previous_mask.shape(0) != rows ||
        previous_mask.shape(1) != previous_capacity || phase.ndim() != 1 ||
        phase.shape(0) != rows || work_limit.ndim() != 1 ||
        work_limit.shape(0) != rows || model_rows.ndim() != 1 ||
        model_rows.shape(0) != rows) {
      throw py::value_error("effect prepared output buffers changed ABI");
    }
    for (const effects::Observation& observation : prepared_observations_) {
      if (observation.candidates.size() >
              static_cast<std::size_t>(candidate_capacity) ||
          observation.jobs.size() > static_cast<std::size_t>(job_capacity) ||
          observation.work_prefix.size() >
              static_cast<std::size_t>(work_capacity) ||
          observation.market_prefix.size() >
              static_cast<std::size_t>(market_capacity) ||
          observation.previous_action.size() >
              static_cast<std::size_t>(previous_capacity)) {
        throw py::value_error("effect observation exceeds its graph buffer");
      }
    }
    const int worker_count = std::max(1, std::min(workers_, rows));
    {
      py::gil_scoped_release release;
      std::fill_n(candidate_fields.mutable_data(), candidate_fields.size(),
                  int64_t{0});
      std::fill_n(candidate_features.mutable_data(), candidate_features.size(),
                  0.0F);
      std::fill_n(candidate_mask.mutable_data(), candidate_mask.size(), false);
      std::fill_n(jobs.mutable_data(), jobs.size(), int64_t{0});
      std::fill_n(job_mask.mutable_data(), job_mask.size(), false);
      std::fill_n(work_prefix.mutable_data(), work_prefix.size(), int64_t{0});
      std::fill_n(work_mask.mutable_data(), work_mask.size(), false);
      std::fill_n(market_prefix.mutable_data(), market_prefix.size(),
                  int64_t{0});
      std::fill_n(market_mask.mutable_data(), market_mask.size(), false);
      std::fill_n(previous_action.mutable_data(), previous_action.size(),
                  int64_t{0});
      std::fill_n(previous_mask.mutable_data(), previous_mask.size(), false);
#ifdef _OPENMP
#pragma omp parallel for schedule(static) num_threads(worker_count)
#endif
      for (int row = 0; row < live_rows; ++row) {
        const effects::Observation& observation = prepared_observations_[row];
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
              observation.candidate_mask[candidate] != 0;
        }
        for (int index = 0;
             index < static_cast<int>(observation.jobs.size()); ++index) {
          std::copy(observation.jobs[index].begin(),
                    observation.jobs[index].end(),
                    jobs.mutable_data(row, index));
          job_mask.mutable_at(row, index) = true;
        }
        const auto copy_actions = [row](const auto& source, auto* destination,
                                        EffectBoolOutput* mask) {
          for (int index = 0; index < static_cast<int>(source.size());
               ++index) {
            std::copy(source[index].begin(), source[index].end(),
                      destination->mutable_data(row, index));
            mask->mutable_at(row, index) = true;
          }
        };
        copy_actions(observation.work_prefix, &work_prefix, &work_mask);
        copy_actions(observation.market_prefix, &market_prefix, &market_mask);
        copy_actions(observation.previous_action, &previous_action,
                     &previous_mask);
        phase.mutable_at(row) = static_cast<int64_t>(observation.phase);
        work_limit.mutable_at(row) = observation.work_limit;
        model_rows.mutable_at(row) = prepared_rows_[row];
      }
      const int last = live_rows - 1;
#ifdef _OPENMP
#pragma omp parallel for schedule(static) num_threads(worker_count)
#endif
      for (int row = live_rows; row < rows; ++row) {
        std::copy_n(candidate_fields.data(last),
                    candidate_capacity * effects::kCandidateFieldCount,
                    candidate_fields.mutable_data(row));
        std::copy_n(candidate_features.data(last),
                    candidate_capacity * effects::kCandidateFeatureCount,
                    candidate_features.mutable_data(row));
        std::copy_n(candidate_mask.data(last), candidate_capacity,
                    candidate_mask.mutable_data(row));
        std::copy_n(jobs.data(last), job_capacity * effects::kJobFieldCount,
                    jobs.mutable_data(row));
        std::copy_n(job_mask.data(last), job_capacity,
                    job_mask.mutable_data(row));
        std::copy_n(work_prefix.data(last),
                    work_capacity * effects::kActionFieldCount,
                    work_prefix.mutable_data(row));
        std::copy_n(work_mask.data(last), work_capacity,
                    work_mask.mutable_data(row));
        std::copy_n(market_prefix.data(last),
                    market_capacity * effects::kActionFieldCount,
                    market_prefix.mutable_data(row));
        std::copy_n(market_mask.data(last), market_capacity,
                    market_mask.mutable_data(row));
        std::copy_n(previous_action.data(last),
                    previous_capacity * effects::kActionFieldCount,
                    previous_action.mutable_data(row));
        std::copy_n(previous_mask.data(last), previous_capacity,
                    previous_mask.mutable_data(row));
        phase.mutable_at(row) = phase.at(last);
        work_limit.mutable_at(row) = work_limit.at(last);
        model_rows.mutable_at(row) = prepared_rows_.back();
      }
    }
  }

  void WritePreparedMask(EffectBoolOutput candidate_mask,
                         EffectIntInput model_rows) const {
    const int live_rows = static_cast<int>(prepared_observations_.size());
    if (live_rows < 1 || prepared_rows_.size() != prepared_observations_.size() ||
        candidate_mask.ndim() != 2 || model_rows.ndim() != 1) {
      throw py::value_error("effect prepared mask buffers changed ABI");
    }
    const int rows = static_cast<int>(candidate_mask.shape(0));
    const int capacity = static_cast<int>(candidate_mask.shape(1));
    if (rows < live_rows || model_rows.shape(0) != rows) {
      throw py::value_error("effect prepared mask buffers changed ABI");
    }
    for (const effects::Observation& observation : prepared_observations_) {
      const auto& mask = observation.candidate_mask;
      if (mask.size() > static_cast<std::size_t>(capacity)) {
        throw py::value_error("effect candidate mask exceeds its graph buffer");
      }
    }
    const int worker_count = std::max(1, std::min(workers_, rows));
    {
      py::gil_scoped_release release;
      std::fill_n(candidate_mask.mutable_data(), candidate_mask.size(), false);
#ifdef _OPENMP
#pragma omp parallel for schedule(static) num_threads(worker_count)
#endif
      for (int row = 0; row < live_rows; ++row) {
        const auto& mask = prepared_observations_[row].candidate_mask;
        for (int candidate = 0; candidate < static_cast<int>(mask.size());
             ++candidate) {
          candidate_mask.mutable_at(row, candidate) = mask[candidate] != 0;
        }
        model_rows.mutable_at(row) = prepared_rows_[row];
      }
      const int last = live_rows - 1;
#ifdef _OPENMP
#pragma omp parallel for schedule(static) num_threads(worker_count)
#endif
      for (int row = live_rows; row < rows; ++row) {
        std::copy_n(candidate_mask.data(last), capacity,
                    candidate_mask.mutable_data(row));
        model_rows.mutable_at(row) = prepared_rows_.back();
      }
    }
  }

  void WritePreparedPrefix(EffectIntInput prefix, EffectBoolOutput mask) const {
    const int live = static_cast<int>(prepared_observations_.size());
    if (live < 1 || prefix.ndim() != 3 || mask.ndim() != 2 ||
        prefix.shape(0) < live || prefix.shape(2) != effects::kActionFieldCount ||
        mask.shape(0) != prefix.shape(0) || mask.shape(1) != prefix.shape(1)) {
      throw py::value_error("effect work prefix buffers changed ABI");
    }
    for (const auto& observation : prepared_observations_) {
      if (observation.work_prefix.size() > static_cast<std::size_t>(prefix.shape(1))) {
        throw py::value_error("effect work prefix exceeds graph capacity");
      }
    }
    const int rows = static_cast<int>(prefix.shape(0));
    const int workers = std::max(1, std::min(workers_, rows));
    py::gil_scoped_release release;
    std::fill_n(prefix.mutable_data(), prefix.size(), int64_t{0});
    std::fill_n(mask.mutable_data(), mask.size(), false);
#ifdef _OPENMP
#pragma omp parallel for schedule(static) num_threads(workers)
#endif
    for (int row = 0; row < rows; ++row) {
      const auto& actions = prepared_observations_[std::min(row, live - 1)].work_prefix;
      for (int i = 0; i < static_cast<int>(actions.size()); ++i) {
        std::copy(actions[i].begin(), actions[i].end(), prefix.mutable_data(row, i));
        mask.mutable_at(row, i) = true;
      }
    }
  }

  py::array_t<int64_t> Advance(EffectIntInput selected,
                               EffectFloatInput log_probability,
                               EffectFloatInput value, int turn_index) {
    const int rows = static_cast<int>(prepared_rows_.size());
    if (rows < 1 || prepared_observations_.size() != prepared_rows_.size() ||
        selected.ndim() != 1 || selected.shape(0) != rows ||
        log_probability.ndim() != 1 || log_probability.shape(0) != rows ||
        value.ndim() != 1 || value.shape(0) != rows || turn_index < 0) {
      throw py::value_error("effect behavior does not align with prepared rows");
    }
    return AdvancePrepared(selected.data(), log_probability.data(), value.data(),
                           -1, turn_index);
  }

  py::array_t<int64_t> AdvanceIndexed(EffectIntInput selected,
                                      int64_t behavior_offset,
                                      int turn_index) {
    const int rows = static_cast<int>(prepared_rows_.size());
    if (rows < 1 || prepared_observations_.size() != prepared_rows_.size() ||
        selected.ndim() != 1 || selected.shape(0) != rows ||
        behavior_offset < 0 || turn_index < 0) {
      throw py::value_error(
          "effect device behavior does not align with prepared rows");
    }
    return AdvancePrepared(selected.data(), nullptr, nullptr, behavior_offset,
                           turn_index);
  }

 private:
  py::array_t<int64_t> AdvancePrepared(const int64_t* selected,
                                       const float* log_probability,
                                       const float* value,
                                       int64_t behavior_offset,
                                       int turn_index) {
    const int rows = static_cast<int>(prepared_rows_.size());
    const bool indexed = behavior_offset >= 0;
    std::vector<EffectRolloutRow> records(
        record_rollout_ ? static_cast<std::size_t>(rows) : 0);
    py::array_t<int64_t> phases(rows);
    auto* phase_data = phases.mutable_data();
    std::exception_ptr first_error;
    std::mutex error_mutex;
    const int worker_count = std::max(1, std::min(workers_, rows));
    {
      py::gil_scoped_release release;
#ifdef _OPENMP
#pragma omp parallel for schedule(static) num_threads(worker_count)
#endif
      for (int index = 0; index < rows; ++index) {
        try {
          const int episode = prepared_rows_[index];
          effects::Observation observation =
              std::move(prepared_observations_[index]);
          const int choice = static_cast<int>(selected[index]);
          if (choice < 0 ||
              choice >= static_cast<int>(observation.candidates.size()) ||
              observation.candidate_mask[choice] == 0) {
            throw std::out_of_range(
                "effect selected candidate is unavailable");
          }
          const effects::Phase policy_phase = observation.phase;
          if (record_rollout_) {
            if (policy_phase == effects::Phase::kWork &&
                !owners_.sessions[episode]->task_conditioning()) {
              // All ranked work factors use the immutable root score.  Retain
              // the current hard mask but seal the root semantic state so the
              // learner reconstructs exactly that distribution.
              observation.work_prefix.clear();
            }
            records[index] = EffectRolloutRow{
                .observation = std::move(observation),
                .episode_index = episode,
                .turn_index = turn_index,
                .transaction_step = factor_counts_[episode],
                .selected = choice,
                .behavior_index = indexed ? behavior_offset + index : -1,
                .log_probability = indexed ? 0.0F : log_probability[index],
                .value = indexed ? 0.0F : value[index],
                .value_mask = static_cast<uint8_t>(factor_counts_[episode] == 0),
            };
          }
          phase_data[index] = static_cast<int64_t>(
              owners_.sessions[episode]->Select(*owners_.engines[episode],
                                                owners_.players[episode],
                                                choice));
        } catch (...) {
          std::lock_guard<std::mutex> lock(error_mutex);
          if (!first_error) first_error = std::current_exception();
        }
      }
    }
    if (first_error) std::rethrow_exception(first_error);
    for (int index = 0; index < rows; ++index) {
      ++factor_counts_[prepared_rows_[index]];
      if (record_rollout_) tape_.push_back(std::move(records[index]));
    }
    prepared_rows_.clear();
    prepared_observations_.clear();
    return phases;
  }

 public:
  py::dict Actions() const {
    const int batch = batch_size();
    std::vector<effects::NumericAction> actions(static_cast<std::size_t>(batch));
    std::exception_ptr first_error;
    std::mutex error_mutex;
    {
      py::gil_scoped_release release;
#ifdef _OPENMP
#pragma omp parallel for schedule(static) num_threads(workers_)
#endif
      for (int row = 0; row < batch; ++row) {
        try {
          actions[row] = owners_.sessions[row]->ActionNumeric(
              *owners_.engines[row], owners_.players[row]);
        } catch (...) {
          std::lock_guard<std::mutex> lock(error_mutex);
          if (!first_error) first_error = std::current_exception();
        }
      }
    }
    if (first_error) std::rethrow_exception(first_error);
    int width = 0;
    for (const auto& action : actions) {
      width = std::max(width, static_cast<int>(action.tokens.size()));
    }
    py::array_t<int64_t> tokens({batch, width});
    py::array_t<int64_t> quantities({batch, width});
    py::array_t<int64_t> decision_counts(batch);
    py::array_t<int64_t> unit_counts(batch);
    std::fill_n(tokens.mutable_data(), tokens.size(), int64_t{0});
    std::fill_n(quantities.mutable_data(), quantities.size(), int64_t{0});
    for (int row = 0; row < batch; ++row) {
      std::copy(actions[row].tokens.begin(), actions[row].tokens.end(),
                tokens.mutable_data(row));
      std::copy(actions[row].quantities.begin(), actions[row].quantities.end(),
                quantities.mutable_data(row));
      decision_counts.mutable_at(row) = actions[row].decision_count;
      unit_counts.mutable_at(row) = actions[row].unit_count;
    }
    py::dict result;
    result["tokens"] = std::move(tokens);
    result["quantities"] = std::move(quantities);
    result["decision_counts"] = std::move(decision_counts);
    result["unit_counts"] = std::move(unit_counts);
    return result;
  }

 private:
  py::dict ExportRows(const std::vector<std::size_t>& indices,
                      int candidate_width) const {
    const int rows = static_cast<int>(indices.size());
    int job_width = 0;
    int work_width = 0;
    int market_width = 0;
    int previous_width = 0;
    for (const std::size_t index : indices) {
      const effects::Observation& observation = tape_[index].observation;
      job_width =
          std::max(job_width, static_cast<int>(observation.jobs.size()));
      work_width = std::max(
          work_width, static_cast<int>(observation.work_prefix.size()));
      market_width = std::max(
          market_width, static_cast<int>(observation.market_prefix.size()));
      previous_width = std::max(
          previous_width, static_cast<int>(observation.previous_action.size()));
    }
    py::array_t<int64_t> fields(
        {rows, candidate_width, effects::kCandidateFieldCount});
    py::array_t<float> features(
        {rows, candidate_width, effects::kCandidateFeatureCount});
    py::array_t<bool> candidate_mask({rows, candidate_width});
    py::array_t<int64_t> jobs(
        {rows, job_width, effects::kJobFieldCount});
    py::array_t<int64_t> work(
        {rows, work_width, effects::kActionFieldCount});
    py::array_t<int64_t> market(
        {rows, market_width, effects::kActionFieldCount});
    py::array_t<int64_t> previous(
        {rows, previous_width, effects::kActionFieldCount});
    py::array_t<int64_t> candidate_counts(rows);
    py::array_t<int64_t> job_counts(rows);
    py::array_t<int64_t> work_counts(rows);
    py::array_t<int64_t> market_counts(rows);
    py::array_t<int64_t> previous_counts(rows);
    py::array_t<int64_t> phases(rows);
    py::array_t<int64_t> work_limits(rows);
    py::array_t<int64_t> selected(rows);
    py::array_t<uint64_t> selected_canonical_id(rows);
    py::array_t<int64_t> behavior_index(rows);
    py::array_t<float> old_log_probability(rows);
    py::array_t<float> old_value(rows);
    py::array_t<bool> policy_mask(rows);
    py::array_t<bool> value_mask(rows);
    py::array_t<int64_t> episode_index(rows);
    py::array_t<int64_t> turn_index(rows);
    py::array_t<int64_t> transaction_step(rows);
    const int worker_count = std::max(1, std::min(workers_, rows));
    {
      py::gil_scoped_release release;
#ifdef _OPENMP
#pragma omp parallel for schedule(static) num_threads(worker_count)
#endif
      for (int output = 0; output < rows; ++output) {
        const EffectRolloutRow& row = tape_[indices[output]];
        const effects::Observation& observation = row.observation;
        const int count = static_cast<int>(observation.candidates.size());
        // First-touch independent rows without the GIL. Live entries are
        // overwritten below; only masked padding needs initialization.
        if (count < candidate_width) {
          std::fill_n(fields.mutable_data(output, count),
                      (candidate_width - count) * effects::kCandidateFieldCount,
                      int64_t{0});
          std::fill_n(features.mutable_data(output, count),
                      (candidate_width - count) * effects::kCandidateFeatureCount,
                      0.0F);
          std::fill_n(candidate_mask.mutable_data(output, count),
                      candidate_width - count, false);
        }
        const int job_count = static_cast<int>(observation.jobs.size());
        if (job_count < job_width) {
          std::fill_n(jobs.mutable_data(output, job_count),
                      (job_width - job_count) * effects::kJobFieldCount,
                      int64_t{0});
        }
        candidate_counts.mutable_at(output) = count;
        job_counts.mutable_at(output) = observation.jobs.size();
        work_counts.mutable_at(output) = observation.work_prefix.size();
        market_counts.mutable_at(output) = observation.market_prefix.size();
        previous_counts.mutable_at(output) =
            observation.previous_action.size();
        phases.mutable_at(output) = static_cast<int64_t>(observation.phase);
        work_limits.mutable_at(output) = observation.work_limit;
        selected.mutable_at(output) = row.selected;
        selected_canonical_id.mutable_at(output) =
            observation.candidates[row.selected].canonical_id;
        behavior_index.mutable_at(output) = row.behavior_index;
        old_log_probability.mutable_at(output) = row.log_probability;
        old_value.mutable_at(output) = row.value;
        value_mask.mutable_at(output) = row.value_mask != 0;
        policy_mask.mutable_at(output) =
            std::count(observation.candidate_mask.begin(),
                       observation.candidate_mask.end(), uint8_t{1}) > 1;
        episode_index.mutable_at(output) = row.episode_index;
        turn_index.mutable_at(output) = row.turn_index;
        transaction_step.mutable_at(output) = row.transaction_step;
        for (int candidate = 0; candidate < count; ++candidate) {
          std::copy(observation.candidates[candidate].fields.begin(),
                    observation.candidates[candidate].fields.end(),
                    fields.mutable_data(output, candidate));
          std::copy(observation.candidates[candidate].features.begin(),
                    observation.candidates[candidate].features.end(),
                    features.mutable_data(output, candidate));
          candidate_mask.mutable_at(output, candidate) =
              observation.candidate_mask[candidate] != 0;
        }
        for (int index = 0;
             index < static_cast<int>(observation.jobs.size()); ++index) {
          std::copy(observation.jobs[index].begin(),
                    observation.jobs[index].end(),
                    jobs.mutable_data(output, index));
        }
        const auto copy_actions = [output](const auto& source,
                                            auto* destination) {
          const int count = static_cast<int>(source.size());
          const int width = static_cast<int>(destination->shape(1));
          if (count < width) {
            std::fill_n(destination->mutable_data(output, count),
                        (width - count) * effects::kActionFieldCount,
                        int64_t{0});
          }
          for (int index = 0; index < static_cast<int>(source.size()); ++index) {
            std::copy(source[index].begin(), source[index].end(),
                      destination->mutable_data(output, index));
          }
        };
        copy_actions(observation.work_prefix, &work);
        copy_actions(observation.market_prefix, &market);
        copy_actions(observation.previous_action, &previous);
      }
    }
    py::dict result;
    result["candidate_fields"] = std::move(fields);
    result["candidate_features"] = std::move(features);
    result["candidate_mask"] = std::move(candidate_mask);
    result["candidate_counts"] = std::move(candidate_counts);
    result["jobs"] = std::move(jobs);
    result["job_counts"] = std::move(job_counts);
    result["work_prefix"] = std::move(work);
    result["work_counts"] = std::move(work_counts);
    result["market_prefix"] = std::move(market);
    result["market_counts"] = std::move(market_counts);
    result["previous_action"] = std::move(previous);
    result["previous_counts"] = std::move(previous_counts);
    result["phase"] = std::move(phases);
    result["work_limit"] = std::move(work_limits);
    result["selected"] = std::move(selected);
    result["selected_canonical_id"] = std::move(selected_canonical_id);
    result["behavior_index"] = std::move(behavior_index);
    result["old_log_probability"] = std::move(old_log_probability);
    result["old_value"] = std::move(old_value);
    result["policy_mask"] = std::move(policy_mask);
    result["value_mask"] = std::move(value_mask);
    result["episode_index"] = std::move(episode_index);
    result["turn_index"] = std::move(turn_index);
    result["transaction_step"] = std::move(transaction_step);
    return result;
  }

 public:
  py::list ExportRolloutBuckets() {
    if (tape_.empty()) {
      throw py::value_error("effect rollout tape is empty");
    }
    std::map<int, std::vector<std::vector<std::size_t>>> buckets;
    for (std::size_t index = 0; index < tape_.size(); ++index) {
      const EffectRolloutRow& row = tape_[index];
      if (row.episode_index < 0 || row.episode_index >= batch_size()) {
        throw std::logic_error("effect rollout row escaped its batch");
      }
      const int width =
          EffectWidthBucket(row.observation.candidates.size());
      auto bucket = buckets
                        .try_emplace(width,
                                     static_cast<std::size_t>(batch_size()))
                        .first;
      bucket->second[static_cast<std::size_t>(row.episode_index)].push_back(
          index);
    }
    py::list result;
    for (const auto& [width, episode_rows] : buckets) {
      std::vector<std::size_t> indices;
      for (const auto& rows : episode_rows) {
        indices.insert(indices.end(), rows.begin(), rows.end());
      }
      result.append(ExportRows(indices, width));
    }
    {
      py::gil_scoped_release release;
      tape_.clear();
    }
    return result;
  }

  void ResetTransaction() {
    std::fill(factor_counts_.begin(), factor_counts_.end(), 0);
    prepared_rows_.clear();
    prepared_observations_.clear();
  }

  int batch_size() const {
    return static_cast<int>(owners_.sessions.size());
  }

 private:
  py::list session_owners_;
  py::list engine_owners_;
  EffectOwners owners_;
  int workers_;
  bool record_rollout_;
  std::vector<int> factor_counts_;
  std::vector<int> prepared_rows_;
  std::vector<effects::Observation> prepared_observations_;
  std::vector<EffectRolloutRow> tape_;
};
