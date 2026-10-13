py::dict EffectObservationToPy(const effects::Observation& observation) {
  const int candidates = static_cast<int>(observation.candidates.size());
  py::array_t<int64_t> fields(
      {candidates, effects::kCandidateFieldCount});
  py::array_t<float> features(
      {candidates, effects::kCandidateFeatureCount});
  py::array_t<bool> mask(candidates);
  py::array_t<uint64_t> ids(candidates);
  for (int index = 0; index < candidates; ++index) {
    std::copy(observation.candidates[index].fields.begin(),
              observation.candidates[index].fields.end(),
              fields.mutable_data(index));
    std::copy(observation.candidates[index].features.begin(),
              observation.candidates[index].features.end(),
              features.mutable_data(index));
    mask.mutable_at(index) = observation.candidate_mask[index] != 0;
    ids.mutable_at(index) = observation.candidates[index].canonical_id;
  }
  const auto action_array = [](const auto& rows) {
    py::array_t<int64_t> result(
        {static_cast<int>(rows.size()), effects::kActionFieldCount});
    for (int index = 0; index < static_cast<int>(rows.size()); ++index) {
      std::copy(rows[index].begin(), rows[index].end(),
                result.mutable_data(index));
    }
    return result;
  };
  py::array_t<int64_t> jobs(
      {static_cast<int>(observation.jobs.size()), effects::kJobFieldCount});
  for (int index = 0; index < static_cast<int>(observation.jobs.size());
       ++index) {
    std::copy(observation.jobs[index].begin(), observation.jobs[index].end(),
              jobs.mutable_data(index));
  }
  py::dict result;
  result["version"] = effects::kSpecVersion;
  result["phase"] = static_cast<int64_t>(observation.phase);
  result["phase_name"] = effects::PhaseName(observation.phase);
  result["candidate_fields"] = std::move(fields);
  result["candidate_features"] = std::move(features);
  result["candidate_mask"] = std::move(mask);
  result["canonical_id"] = std::move(ids);
  result["candidate_count"] = candidates;
  result["jobs"] = std::move(jobs);
  result["work_prefix"] = action_array(observation.work_prefix);
  result["market_prefix"] = action_array(observation.market_prefix);
  result["previous_action"] = action_array(observation.previous_action);
  result["work_limit"] = observation.work_limit;
  return result;
}

py::dict EffectSpec() {
  py::dict result;
  result["version"] = effects::kSpecVersion;
  result["abi_version"] = effects::kAbiVersion;
  result["candidate_field_count"] = effects::kCandidateFieldCount;
  result["candidate_feature_count"] = effects::kCandidateFeatureCount;
  result["job_field_count"] = effects::kJobFieldCount;
  result["action_field_count"] = effects::kActionFieldCount;
  result["candidate_fields"] = py::make_tuple(
      "request_kind", "target", "item", "exact_quantity", "job_id",
      "unit", "resource_kind", "resource_item", "resource_required",
      "resource_available", "prefix_position");
  py::list feature_names;
  for (const std::string& name : effects::CandidateFeatureNames()) {
    feature_names.append(name);
  }
  result["candidate_features"] = std::move(feature_names);
  result["job_fields"] = py::make_tuple(
      "job_id", "request_kind", "target", "item", "unit",
      "created_step", "completion_steps", "exact_quantity");
  result["action_fields"] = py::make_tuple(
      "request_kind", "target", "item", "exact_quantity", "job_id",
      "unit");
  py::dict phases;
  for (int value = 0; value <= static_cast<int>(effects::Phase::kDone);
       ++value) {
    phases[effects::PhaseName(static_cast<effects::Phase>(value))] = value;
  }
  result["phases"] = std::move(phases);
  py::dict requests;
  for (int value = 0;
       value <= static_cast<int>(effects::RequestKind::kSkipMarketSlot);
       ++value) {
    requests[effects::RequestKindName(
        static_cast<effects::RequestKind>(value))] = value;
  }
  result["request_kinds"] = std::move(requests);
  py::dict resources;
  for (int value = 0;
       value <= static_cast<int>(effects::ResourceKind::kShedRoom); ++value) {
    resources[effects::ResourceKindName(
        static_cast<effects::ResourceKind>(value))] = value;
  }
  result["resource_kinds"] = std::move(resources);
  return result;
}

struct EffectOwners {
  std::vector<effects::Session*> sessions;
  std::vector<const Engine*> engines;
  std::vector<int> players;
};

EffectOwners ParseEffectOwners(py::list session_owners,
                               py::list engine_owners, IntArray players,
                               int workers) {
  const int batch = static_cast<int>(py::len(session_owners));
  if (batch < 1 ||
      py::len(engine_owners) != static_cast<py::size_t>(batch) || workers < 1 ||
      workers > 256) {
    throw py::value_error("effect batch inputs are invalid");
  }
  const py::buffer_info info = players.request();
  if (info.ndim != 1 || info.shape[0] != batch) {
    throw py::value_error("effect batch players must have shape [B]");
  }
  const auto* values = static_cast<const int64_t*>(info.ptr);
  EffectOwners result;
  result.sessions.reserve(batch);
  result.engines.reserve(batch);
  result.players.reserve(batch);
  for (int index = 0; index < batch; ++index) {
    if (values[index] < 0 || values[index] > 1) {
      throw py::value_error("effect player must be 0 or 1");
    }
    auto* session = &py::cast<effects::Session&>(session_owners[index]);
    if (std::find(result.sessions.begin(), result.sessions.end(), session) !=
        result.sessions.end()) {
      throw py::value_error("effect batch requires distinct sessions");
    }
    result.sessions.push_back(session);
    result.engines.push_back(
        &py::cast<const PyEngine&>(engine_owners[index]).raw_engine());
    result.players.push_back(static_cast<int>(values[index]));
  }
  return result;
}

py::dict EffectObservationsBatch(py::list session_owners,
                                 py::list engine_owners, IntArray players,
                                 int workers) {
  const EffectOwners owners = ParseEffectOwners(
      session_owners, engine_owners, std::move(players), workers);
  const int batch = static_cast<int>(owners.sessions.size());
  std::vector<effects::Observation> observations(batch);
  std::exception_ptr first_error;
  std::mutex error_mutex;
  {
    py::gil_scoped_release release;
#ifdef _OPENMP
#pragma omp parallel for schedule(static) num_threads(workers)
#endif
    for (int row = 0; row < batch; ++row) {
      try {
        observations[row] = owners.sessions[row]->Observe(
            *owners.engines[row], owners.players[row]);
      } catch (...) {
        std::lock_guard<std::mutex> lock(error_mutex);
        if (!first_error) first_error = std::current_exception();
      }
    }
  }
  if (first_error) std::rethrow_exception(first_error);
  int candidate_width = 0;
  int job_width = 0;
  int work_width = 0;
  int market_width = 0;
  int previous_width = 0;
  for (const effects::Observation& observation : observations) {
    candidate_width = std::max(
        candidate_width, static_cast<int>(observation.candidates.size()));
    job_width = std::max(job_width, static_cast<int>(observation.jobs.size()));
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
  py::array_t<bool> job_mask({batch, job_width});
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
  std::fill_n(job_mask.mutable_data(), job_mask.size(), false);
  std::fill_n(work.mutable_data(), work.size(), int64_t{0});
  std::fill_n(market.mutable_data(), market.size(), int64_t{0});
  std::fill_n(previous.mutable_data(), previous.size(), int64_t{0});
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
    for (int index = 0; index < static_cast<int>(observation.jobs.size());
         ++index) {
      std::copy(observation.jobs[index].begin(), observation.jobs[index].end(),
                jobs.mutable_data(row, index));
      job_mask.mutable_at(row, index) = true;
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
  py::dict result;
  result["candidate_fields"] = std::move(fields);
  result["candidate_features"] = std::move(features);
  result["candidate_mask"] = std::move(mask);
  result["canonical_id"] = std::move(ids);
  result["candidate_counts"] = std::move(counts);
  result["phase"] = std::move(phases);
  result["work_limit"] = std::move(work_limits);
  result["jobs"] = std::move(jobs);
  result["job_mask"] = std::move(job_mask);
  result["job_counts"] = std::move(job_counts);
  result["work_prefix"] = std::move(work);
  result["work_counts"] = std::move(work_counts);
  result["market_prefix"] = std::move(market);
  result["market_counts"] = std::move(market_counts);
  result["previous_action"] = std::move(previous);
  result["previous_counts"] = std::move(previous_counts);
  return result;
}

py::array_t<int64_t> EffectSelectBatch(py::list session_owners,
                                       py::list engine_owners,
                                       IntArray players,
                                       IntArray candidate_indices,
                                       IntArray active, int workers) {
  const EffectOwners owners = ParseEffectOwners(
      session_owners, engine_owners, std::move(players), workers);
  const int batch = static_cast<int>(owners.sessions.size());
  const py::buffer_info candidate_info = candidate_indices.request();
  const py::buffer_info active_info = active.request();
  if (candidate_info.ndim != 1 || candidate_info.shape[0] != batch ||
      active_info.ndim != 1 || active_info.shape[0] != batch) {
    throw py::value_error("effect selections must have shape [B]");
  }
  const auto* selected = static_cast<const int64_t*>(candidate_info.ptr);
  const auto* enabled = static_cast<const int64_t*>(active_info.ptr);
  py::array_t<int64_t> phases(batch);
  std::exception_ptr first_error;
  std::mutex error_mutex;
  {
    py::gil_scoped_release release;
#ifdef _OPENMP
#pragma omp parallel for schedule(static) num_threads(workers)
#endif
    for (int row = 0; row < batch; ++row) {
      try {
        phases.mutable_at(row) =
            enabled[row]
                ? static_cast<int64_t>(owners.sessions[row]->Select(
                      *owners.engines[row], owners.players[row], selected[row]))
                : static_cast<int64_t>(owners.sessions[row]->phase());
      } catch (...) {
        std::lock_guard<std::mutex> lock(error_mutex);
        if (!first_error) first_error = std::current_exception();
      }
    }
  }
  if (first_error) std::rethrow_exception(first_error);
  return phases;
}

py::dict EffectActionsBatch(py::list session_owners, py::list engine_owners,
                            IntArray players, int workers) {
  const EffectOwners owners = ParseEffectOwners(
      session_owners, engine_owners, std::move(players), workers);
  const int batch = static_cast<int>(owners.sessions.size());
  std::vector<effects::NumericAction> actions(batch);
  std::exception_ptr first_error;
  std::mutex error_mutex;
  {
    py::gil_scoped_release release;
#ifdef _OPENMP
#pragma omp parallel for schedule(static) num_threads(workers)
#endif
    for (int row = 0; row < batch; ++row) {
      try {
        actions[row] = owners.sessions[row]->ActionNumeric(
            *owners.engines[row], owners.players[row]);
      } catch (...) {
        std::lock_guard<std::mutex> lock(error_mutex);
        if (!first_error) first_error = std::current_exception();
      }
    }
  }
  if (first_error) std::rethrow_exception(first_error);
  int width = 0;
  for (const effects::NumericAction& action : actions) {
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

#include "effects/batch_binding.inc"

void BindAtomicEffects(py::module_& module) {
  py::class_<effects::Session>(module, "AtomicEffectSession")
      .def(py::init([](py::object configuration, int unit_limit,
                       int maximum_quantity, bool task_conditioning,
                       py::object destination_tasks) {
             return std::make_unique<effects::Session>(
                 pyconv::ParseConfig(configuration), unit_limit,
                 maximum_quantity, task_conditioning,
                 destination_tasks.is_none() ? task_conditioning
                                             : destination_tasks.cast<bool>());
           }),
           py::arg("configuration") = py::none(), py::arg("unit_limit") = 32,
           py::arg("maximum_quantity") = 128,
           py::arg("task_conditioning") = false,
           py::arg("destination_tasks") = py::none())
      .def("observe", [](effects::Session& session, const PyEngine& owner,
                         int player) {
        effects::Observation observation;
        {
          py::gil_scoped_release release;
          observation = session.Observe(owner.raw_engine(), player);
        }
        return EffectObservationToPy(observation);
      }, py::arg("engine"), py::arg("player"))
      .def("select", [](effects::Session& session, const PyEngine& owner,
                        int player, int candidate_index) {
        effects::Phase phase;
        {
          py::gil_scoped_release release;
          phase = session.Select(owner.raw_engine(), player, candidate_index);
        }
        return static_cast<int64_t>(phase);
      }, py::arg("engine"), py::arg("player"), py::arg("candidate_index"))
      .def("action", [](effects::Session& session, const PyEngine& owner,
                        int player) {
        PlayerAction action;
        {
          py::gil_scoped_release release;
          action = session.Action(owner.raw_engine(), player);
        }
        return pyconv::PlayerActionToPy(action);
      }, py::arg("engine"), py::arg("player"))
      .def("action_numeric", [](effects::Session& session,
                                const PyEngine& owner, int player) {
        effects::NumericAction action;
        {
          py::gil_scoped_release release;
          action = session.ActionNumeric(owner.raw_engine(), player);
        }
        py::array_t<int64_t> tokens(action.tokens.size());
        py::array_t<int64_t> quantities(action.quantities.size());
        std::copy(action.tokens.begin(), action.tokens.end(),
                  tokens.mutable_data());
        std::copy(action.quantities.begin(), action.quantities.end(),
                  quantities.mutable_data());
        py::dict result;
        result["tokens"] = std::move(tokens);
        result["quantities"] = std::move(quantities);
        result["decision_count"] = action.decision_count;
        result["unit_count"] = action.unit_count;
        return result;
      }, py::arg("engine"), py::arg("player"))
      .def("decision_required", &effects::Session::DecisionRequired,
           py::arg("engine"), py::arg("player"))
      .def("reset", &effects::Session::Reset)
      .def_property_readonly("phase", [](const effects::Session& session) {
        return static_cast<int64_t>(session.phase());
      })
      .def_property_readonly("candidate_count",
                             &effects::Session::candidate_count)
      .def_property_readonly("step", &effects::Session::step)
      .def_property_readonly("unit_limit", &effects::Session::unit_limit)
      .def_property_readonly("maximum_quantity",
                             &effects::Session::maximum_quantity);
  py::class_<AtomicEffectBatch>(module, "AtomicEffectBatch")
      .def(py::init<py::list, py::list, IntArray, int, bool>(),
           py::arg("sessions"), py::arg("engines"), py::arg("players"),
           py::arg("workers"), py::arg("record_rollout") = true)
      .def("observe", &AtomicEffectBatch::Observe, py::arg("active"))
      .def("observe_compact", &AtomicEffectBatch::ObserveCompact,
           py::arg("active"))
      .def("write_prepared", &AtomicEffectBatch::WritePrepared,
           py::arg("candidate_fields"), py::arg("candidate_features"),
           py::arg("candidate_mask"), py::arg("jobs"),
           py::arg("job_mask"), py::arg("work_prefix"),
           py::arg("work_mask"), py::arg("market_prefix"),
           py::arg("market_mask"), py::arg("previous_action"),
           py::arg("previous_mask"), py::arg("phase"),
           py::arg("work_limit"), py::arg("model_rows"))
      .def("write_prepared_prefix", &AtomicEffectBatch::WritePreparedPrefix,
           py::arg("prefix"), py::arg("mask"))
      .def("write_prepared_mask", &AtomicEffectBatch::WritePreparedMask,
           py::arg("candidate_mask"), py::arg("model_rows"))
      .def("advance", &AtomicEffectBatch::Advance, py::arg("selected"),
           py::arg("log_probability"), py::arg("value"),
           py::arg("turn_index"))
      .def("advance_indexed", &AtomicEffectBatch::AdvanceIndexed,
           py::arg("selected"), py::arg("behavior_offset"),
           py::arg("turn_index"))
      .def("actions", &AtomicEffectBatch::Actions)
      .def("export_rollout_buckets",
           &AtomicEffectBatch::ExportRolloutBuckets)
      .def("reset_transaction", &AtomicEffectBatch::ResetTransaction)
      .def_property_readonly("batch_size", &AtomicEffectBatch::batch_size);
  module.def("effect_policy_spec", &EffectSpec);
  module.def("effect_policy_observations_batch", &EffectObservationsBatch,
             py::arg("sessions"), py::arg("engines"), py::arg("players"),
             py::arg("workers"));
  module.def("effect_policy_select_batch", &EffectSelectBatch,
             py::arg("sessions"), py::arg("engines"), py::arg("players"),
             py::arg("candidate_indices"), py::arg("active"),
             py::arg("workers"));
  module.def("effect_policy_actions_batch", &EffectActionsBatch,
             py::arg("sessions"), py::arg("engines"), py::arg("players"),
             py::arg("workers"));
}
