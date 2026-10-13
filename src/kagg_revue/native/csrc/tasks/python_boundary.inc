// Included by bindings.cpp inside its private kagg namespace.

py::dict UnitTaskSpecForSession(const tasks::Session& session) {
  py::dict out;
  out["version"] = tasks::kAbiVersion;
  out["candidate_feature_count"] = tasks::kCandidateFeatureCount;
  out["root_feature_count"] = tasks::kRootFeatureCount;
  out["task_field_count"] = tasks::kTaskFieldCount;
  out["mode_count"] = tasks::kModeCount;
  out["candidate_count"] = session.candidate_count();
  out["prefix_capacity"] = session.prefix_capacity();
  out["time_token_count"] = session.config().turns_per_day + 1;
  out["maximum_quantity"] = session.maximum_quantity();
  out["unit_limit"] = session.unit_limit();
  out["board_size"] = session.config().board_size;
  py::list candidate_features;
  for (const std::string& name : tasks::CandidateFeatureNames()) {
    candidate_features.append(name);
  }
  out["candidate_features"] = std::move(candidate_features);
  py::list root_features;
  for (const std::string& name : tasks::RootFeatureNames()) {
    root_features.append(name);
  }
  out["root_features"] = std::move(root_features);
  py::list task_fields;
  for (const std::string& name : tasks::TaskFieldNames()) {
    task_fields.append(name);
  }
  out["task_fields"] = std::move(task_fields);
  py::dict operations;
  operations["END"] = static_cast<int64_t>(tasks::Operation::kEnd);
  operations["POSITION"] = static_cast<int64_t>(tasks::Operation::kPosition);
  operations["WAIT"] = static_cast<int64_t>(tasks::Operation::kWait);
  operations["PICKUP"] = static_cast<int64_t>(tasks::Operation::kPickup);
  operations["DROP"] = static_cast<int64_t>(tasks::Operation::kDrop);
  operations["PLACE"] = static_cast<int64_t>(tasks::Operation::kPlace);
  operations["PLANT"] = static_cast<int64_t>(tasks::Operation::kPlant);
  operations["WATER"] = static_cast<int64_t>(tasks::Operation::kWater);
  operations["HARVEST"] = static_cast<int64_t>(tasks::Operation::kHarvest);
  operations["FERTILIZE"] = static_cast<int64_t>(tasks::Operation::kFertilize);
  operations["DIG"] = static_cast<int64_t>(tasks::Operation::kDig);
  operations["BUILD_COOP"] =
      static_cast<int64_t>(tasks::Operation::kBuildCoop);
  operations["BUILD_PASTURE"] =
      static_cast<int64_t>(tasks::Operation::kBuildPasture);
  operations["FEED"] = static_cast<int64_t>(tasks::Operation::kFeed);
  operations["COLLECT_FERTILIZER"] =
      static_cast<int64_t>(tasks::Operation::kCollectFertilizer);
  operations["CARE"] = static_cast<int64_t>(tasks::Operation::kCare);
  out["operations"] = std::move(operations);
  py::dict modes;
  modes["CONTINUE"] = static_cast<int64_t>(tasks::SuffixMode::kContinue);
  modes["REWRITE"] = static_cast<int64_t>(tasks::SuffixMode::kRewrite);
  out["suffix_modes"] = std::move(modes);

  const int candidates = session.candidate_count();
  py::array_t<int64_t> candidate_operations(candidates);
  py::array_t<int64_t> candidate_arguments(candidates);
  py::array_t<int64_t> candidate_targets({candidates, 2});
  py::array_t<uint8_t> candidate_quantities(candidates);
  py::array_t<int64_t> candidate_operation_turns(candidates);
  for (int index = 0; index < candidates; ++index) {
    const tasks::Candidate& candidate = session.catalog()[index];
    candidate_operations.mutable_at(index) =
        static_cast<int64_t>(candidate.operation);
    candidate_arguments.mutable_at(index) = candidate.argument;
    candidate_targets.mutable_at(index, 0) = candidate.x;
    candidate_targets.mutable_at(index, 1) = candidate.y;
    candidate_quantities.mutable_at(index) =
        tasks::NeedsQuantity(candidate.operation) ? 1 : 0;
    candidate_operation_turns.mutable_at(index) =
        tasks::IsOfficial(candidate.operation) ? 1 : 0;
  }
  out["candidate_operations"] = std::move(candidate_operations);
  out["candidate_arguments"] = std::move(candidate_arguments);
  out["candidate_targets"] = std::move(candidate_targets);
  out["candidate_requires_quantity"] = std::move(candidate_quantities);
  out["candidate_operation_turns"] = std::move(candidate_operation_turns);
  out["compiler"] = "native-x-first-shortest-path-v1";
  return out;
}

py::dict UnitTaskDecisionToPy(const tasks::Decision& decision,
                              const tasks::Session& session) {
  const int candidates = session.candidate_count();
  const int prefix = session.prefix_capacity();
  py::array_t<uint8_t> mode_mask(tasks::kModeCount);
  py::array_t<uint8_t> candidate_mask(candidates);
  py::array_t<int64_t> candidate_arrivals(candidates);
  py::array_t<int64_t> candidate_reasons(candidates);
  py::array_t<float> candidate_features(
      {candidates, tasks::kCandidateFeatureCount});
  py::array_t<int16_t> target_conflicts(decision.target_conflicts.size());
  py::array_t<int16_t> resource_conflicts(decision.resource_conflicts.size());
  py::array_t<int64_t> prefix_fields(
      {prefix, tasks::kTaskFieldCount});
  py::array_t<uint8_t> prefix_mask(prefix);
  py::array_t<float> root_features(tasks::kRootFeatureCount);
  std::copy(decision.mode_mask.begin(), decision.mode_mask.end(),
            mode_mask.mutable_data());
  std::copy(decision.candidate_mask.begin(), decision.candidate_mask.end(),
            candidate_mask.mutable_data());
  std::copy(decision.candidate_arrivals.begin(),
            decision.candidate_arrivals.end(),
            candidate_arrivals.mutable_data());
  std::copy(decision.candidate_reasons.begin(),
            decision.candidate_reasons.end(),
            candidate_reasons.mutable_data());
  std::copy(decision.candidate_features.begin(),
            decision.candidate_features.end(),
            candidate_features.mutable_data());
  std::copy(decision.target_conflicts.begin(), decision.target_conflicts.end(),
            target_conflicts.mutable_data());
  std::copy(decision.resource_conflicts.begin(),
            decision.resource_conflicts.end(),
            resource_conflicts.mutable_data());
  std::copy(decision.prefix_fields.begin(), decision.prefix_fields.end(),
            prefix_fields.mutable_data());
  std::copy(decision.prefix_mask.begin(), decision.prefix_mask.end(),
            prefix_mask.mutable_data());
  std::copy(decision.root_features.begin(), decision.root_features.end(),
            root_features.mutable_data());
  py::dict out;
  out["unit_index"] = decision.unit_index;
  out["current_x"] = decision.current_x;
  out["current_y"] = decision.current_y;
  out["available_at"] = decision.available_at;
  out["day_end"] = decision.day_end;
  out["replan_reason"] = decision.replan_reason;
  out["mode_mask"] = std::move(mode_mask);
  out["candidate_mask"] = std::move(candidate_mask);
  out["candidate_arrivals"] = std::move(candidate_arrivals);
  out["candidate_reasons"] = std::move(candidate_reasons);
  out["candidate_features"] = std::move(candidate_features);
  out["target_conflicts"] = std::move(target_conflicts);
  out["resource_conflicts"] = std::move(resource_conflicts);
  out["prefix_fields"] = std::move(prefix_fields);
  out["prefix_mask"] = std::move(prefix_mask);
  out["root_features"] = std::move(root_features);
  out["version"] = tasks::kAbiVersion;
  return out;
}

py::dict CompactUnitTaskDecisionToPy(const tasks::Decision& decision,
                                     const tasks::Session& session) {
  const int prefix = session.prefix_capacity();
  py::array_t<uint8_t> mode_mask(tasks::kModeCount);
  py::array_t<int16_t> target_conflicts(decision.target_conflicts.size());
  py::array_t<int16_t> resource_conflicts(decision.resource_conflicts.size());
  py::array_t<int64_t> prefix_fields({prefix, tasks::kTaskFieldCount});
  py::array_t<uint8_t> prefix_mask(prefix);
  py::array_t<float> root_features(tasks::kRootFeatureCount);
  std::copy(decision.mode_mask.begin(), decision.mode_mask.end(),
            mode_mask.mutable_data());
  std::copy(decision.target_conflicts.begin(), decision.target_conflicts.end(),
            target_conflicts.mutable_data());
  std::copy(decision.resource_conflicts.begin(),
            decision.resource_conflicts.end(),
            resource_conflicts.mutable_data());
  std::copy(decision.prefix_fields.begin(), decision.prefix_fields.end(),
            prefix_fields.mutable_data());
  std::copy(decision.prefix_mask.begin(), decision.prefix_mask.end(),
            prefix_mask.mutable_data());
  std::copy(decision.root_features.begin(), decision.root_features.end(),
            root_features.mutable_data());
  py::dict out;
  out["unit_index"] = decision.unit_index;
  out["current_x"] = decision.current_x;
  out["current_y"] = decision.current_y;
  out["available_at"] = decision.available_at;
  out["day_end"] = decision.day_end;
  out["replan_reason"] = decision.replan_reason;
  out["mode_mask"] = std::move(mode_mask);
  out["target_conflicts"] = std::move(target_conflicts);
  out["resource_conflicts"] = std::move(resource_conflicts);
  out["prefix_fields"] = std::move(prefix_fields);
  out["prefix_mask"] = std::move(prefix_mask);
  out["root_features"] = std::move(root_features);
  out["version"] = tasks::kAbiVersion;
  return out;
}

py::dict UnitTaskActionToPy(const tasks::NumericUnitAction& action) {
  py::array_t<int64_t> tokens(action.tokens.size());
  py::array_t<int64_t> quantities(action.quantities.size());
  py::array_t<int64_t> task_results(action.task_results.size());
  std::copy(action.tokens.begin(), action.tokens.end(), tokens.mutable_data());
  std::copy(action.quantities.begin(), action.quantities.end(),
            quantities.mutable_data());
  std::copy(action.task_results.begin(), action.task_results.end(),
            task_results.mutable_data());
  py::dict out;
  out["tokens"] = std::move(tokens);
  out["quantities"] = std::move(quantities);
  out["task_results"] = std::move(task_results);
  out["unit_count"] = action.unit_count;
  out["requires_decision"] = action.requires_decision;
  return out;
}

tasks::VisibleState ParseUnitTaskVisibleState(const tasks::Session& session,
                                              const py::dict& observation) {
  tasks::VisibleState state;
  state.player = py::cast<int>(observation["player"]);
  state.step = py::cast<int>(observation["step"]);
  if (state.player < 0 || state.player > 1 || state.step < 0) {
    throw py::value_error("unit-task observation player or step is invalid");
  }
  const auto farms =
      py::reinterpret_borrow<py::list>(observation["farms"]);
  if (farms.size() != 2) {
    throw py::value_error("unit-task observation must contain two farms");
  }
  state.farm = pyconv::ParseFarm(
      py::reinterpret_borrow<py::dict>(farms[state.player]),
      session.config().board_size);
  state.priv = pyconv::ParsePrivate(
      py::reinterpret_borrow<py::dict>(observation["private"]));
  return state;
}

struct UnitTaskOwners {
  std::vector<tasks::Session*> sessions;
  std::vector<const Engine*> engines;
  std::vector<int> players;
};

UnitTaskOwners ParseUnitTaskOwners(py::list session_owners,
                                   py::list engine_owners, IntArray players,
                                   int workers) {
  const int batch = static_cast<int>(py::len(session_owners));
  if (batch < 1 || py::len(engine_owners) != static_cast<py::size_t>(batch)) {
    throw py::value_error("unit-task batch inputs must be nonempty and aligned");
  }
  if (workers < 1 || workers > 256) {
    throw py::value_error("unit-task batch workers must be in [1, 256]");
  }
  const py::buffer_info player_info = players.request();
  if (player_info.ndim != 1 || player_info.shape[0] != batch) {
    throw py::value_error("unit-task players must have shape [B]");
  }
  const auto* player_data = static_cast<const int64_t*>(player_info.ptr);
  UnitTaskOwners result;
  result.sessions.reserve(static_cast<size_t>(batch));
  result.engines.reserve(static_cast<size_t>(batch));
  result.players.reserve(static_cast<size_t>(batch));
  for (int index = 0; index < batch; ++index) {
    const int player = static_cast<int>(player_data[index]);
    if (player < 0 || player > 1) {
      throw py::value_error("unit-task player must be 0 or 1");
    }
    result.sessions.push_back(
        &py::cast<tasks::Session&>(session_owners[index]));
    result.engines.push_back(
        &py::cast<const PyEngine&>(engine_owners[index]).raw_engine());
    result.players.push_back(player);
  }
  const tasks::Session& first = *result.sessions.front();
  for (const tasks::Session* session : result.sessions) {
    if (session->candidate_count() != first.candidate_count() ||
        session->prefix_capacity() != first.prefix_capacity() ||
        session->unit_limit() != first.unit_limit() ||
        session->maximum_quantity() != first.maximum_quantity() ||
        session->config().turns_per_day != first.config().turns_per_day) {
      throw py::value_error("unit-task sessions in one batch must share an ABI");
    }
  }
  return result;
}

py::dict MakeUnitTaskSnapshots(const UnitTaskOwners& owners, int workers) {
  const int batch = static_cast<int>(owners.sessions.size());
  const int prefix = owners.sessions.front()->prefix_capacity();
  const int units = owners.sessions.front()->unit_limit();
  std::vector<tasks::PlanningSnapshot> snapshots(static_cast<size_t>(batch));
  std::exception_ptr first_error;
  std::mutex error_mutex;
  {
    py::gil_scoped_release release;
#ifdef _OPENMP
#pragma omp parallel for schedule(static) num_threads(workers)
#endif
    for (int index = 0; index < batch; ++index) {
      try {
        snapshots[index] = owners.sessions[index]->Snapshot(
            *owners.engines[index], owners.players[index]);
      } catch (...) {
        std::lock_guard<std::mutex> lock(error_mutex);
        if (!first_error) first_error = std::current_exception();
      }
    }
  }
  if (first_error) std::rethrow_exception(first_error);

  py::array_t<uint8_t> required(batch);
  py::array_t<int16_t> hour(batch);
  py::array_t<int16_t> day(batch);
  py::array_t<int16_t> days(batch);
  py::array_t<int16_t> unit_counts(batch);
  py::array_t<int16_t> history_counts(batch);
  py::array_t<int32_t> successful(batch);
  py::array_t<int32_t> failed(batch);
  py::array_t<int32_t> forced(batch);
  py::array_t<int16_t> prefix_fields(
      {batch, prefix, tasks::kTaskFieldCount});
  py::array_t<uint8_t> replan_mask({batch, units});
  py::array_t<uint8_t> optional_mask({batch, units});
  py::array_t<int16_t> replan_reasons({batch, units});
  py::array_t<int16_t> tape_sizes({batch, units});
  for (int index = 0; index < batch; ++index) {
    const tasks::PlanningSnapshot& snapshot = snapshots[index];
    required.mutable_at(index) = snapshot.requires_decision ? 1 : 0;
    hour.mutable_at(index) = static_cast<int16_t>(snapshot.hour);
    day.mutable_at(index) = static_cast<int16_t>(snapshot.day);
    days.mutable_at(index) = static_cast<int16_t>(snapshot.days);
    unit_counts.mutable_at(index) =
        static_cast<int16_t>(snapshot.unit_count);
    history_counts.mutable_at(index) =
        static_cast<int16_t>(snapshot.history_count);
    successful.mutable_at(index) = snapshot.successful_tasks;
    failed.mutable_at(index) = snapshot.failed_tasks;
    forced.mutable_at(index) = snapshot.forced_ends;
    std::copy(snapshot.prefix_fields.begin(), snapshot.prefix_fields.end(),
              prefix_fields.mutable_data() +
                  static_cast<size_t>(index) * prefix *
                      tasks::kTaskFieldCount);
    std::copy(snapshot.replan_mask.begin(), snapshot.replan_mask.end(),
              replan_mask.mutable_data() +
                  static_cast<size_t>(index) * units);
    std::copy(snapshot.optional_mask.begin(), snapshot.optional_mask.end(),
              optional_mask.mutable_data() +
                  static_cast<size_t>(index) * units);
    std::copy(snapshot.replan_reasons.begin(),
              snapshot.replan_reasons.end(),
              replan_reasons.mutable_data() +
                  static_cast<size_t>(index) * units);
    std::copy(snapshot.tape_sizes.begin(), snapshot.tape_sizes.end(),
              tape_sizes.mutable_data() +
                  static_cast<size_t>(index) * units);
  }
  py::dict out;
  out["requires_decision"] = std::move(required);
  out["hour"] = std::move(hour);
  out["day"] = std::move(day);
  out["days"] = std::move(days);
  out["unit_counts"] = std::move(unit_counts);
  out["history_counts"] = std::move(history_counts);
  out["successful_tasks"] = std::move(successful);
  out["failed_tasks"] = std::move(failed);
  out["forced_ends"] = std::move(forced);
  out["prefix_fields"] = std::move(prefix_fields);
  out["replan_mask"] = std::move(replan_mask);
  out["optional_mask"] = std::move(optional_mask);
  out["replan_reasons"] = std::move(replan_reasons);
  out["tape_sizes"] = std::move(tape_sizes);
  out["version"] = tasks::kAbiVersion;
  return out;
}

void ApplyUnitTaskSequences(
    const UnitTaskOwners& owners,
    py::array_t<int16_t,
                py::array::c_style | py::array::forcecast> selections,
    py::array_t<int16_t,
                py::array::c_style | py::array::forcecast> counts,
    int workers) {
  const int batch = static_cast<int>(owners.sessions.size());
  const py::buffer_info selection_info = selections.request();
  const py::buffer_info count_info = counts.request();
  if (selection_info.ndim != 3 || selection_info.shape[0] != batch ||
      selection_info.shape[2] != 5 || count_info.ndim != 1 ||
      count_info.shape[0] != batch) {
    throw py::value_error(
        "unit-task sequences must have shapes [B,S,5] and [B]");
  }
  const int capacity = static_cast<int>(selection_info.shape[1]);
  const auto* selection_data =
      static_cast<const int16_t*>(selection_info.ptr);
  const auto* count_data = static_cast<const int16_t*>(count_info.ptr);
  std::exception_ptr first_error;
  std::mutex error_mutex;
  {
    py::gil_scoped_release release;
#ifdef _OPENMP
#pragma omp parallel for schedule(static) num_threads(workers)
#endif
    for (int index = 0; index < batch; ++index) {
      try {
        const int count = count_data[index];
        if (count < 0 || count > capacity) {
          throw std::invalid_argument(
              "unit-task sequence count is outside its capacity");
        }
        std::vector<tasks::Selection> row;
        row.reserve(static_cast<size_t>(count));
        const int16_t* values = selection_data +
                                static_cast<size_t>(index) * capacity * 5;
        for (int decision = 0; decision < count; ++decision) {
          const int16_t* fields = values + static_cast<size_t>(decision) * 5;
          row.push_back(tasks::Selection{
              static_cast<tasks::SuffixMode>(fields[0]), fields[1],
              fields[2], fields[3], fields[4]});
        }
        owners.sessions[index]->ApplySelections(
            *owners.engines[index], owners.players[index], row.data(), count);
      } catch (...) {
        std::lock_guard<std::mutex> lock(error_mutex);
        if (!first_error) first_error = std::current_exception();
      }
    }
  }
  if (first_error) std::rethrow_exception(first_error);
}

py::dict MakeUnitTaskDecisions(const UnitTaskOwners& owners, int workers) {
  const int batch = static_cast<int>(owners.sessions.size());
  const int candidates = owners.sessions.front()->candidate_count();
  const int prefix = owners.sessions.front()->prefix_capacity();
  std::vector<tasks::Decision> decisions(static_cast<size_t>(batch));
  std::exception_ptr first_error;
  std::mutex error_mutex;
  {
    py::gil_scoped_release release;
#ifdef _OPENMP
#pragma omp parallel for schedule(static) num_threads(workers)
#endif
    for (int index = 0; index < batch; ++index) {
      try {
        decisions[index] = owners.sessions[index]->Observe(
            *owners.engines[index], owners.players[index]);
      } catch (...) {
        std::lock_guard<std::mutex> lock(error_mutex);
        if (!first_error) first_error = std::current_exception();
      }
    }
  }
  if (first_error) std::rethrow_exception(first_error);
  py::array_t<int16_t> unit_indices(batch);
  py::array_t<int16_t> current_x(batch);
  py::array_t<int16_t> current_y(batch);
  py::array_t<int16_t> available_at(batch);
  py::array_t<int16_t> day_end(batch);
  py::array_t<int16_t> replan_reasons(batch);
  py::array_t<uint8_t> mode_mask({batch, tasks::kModeCount});
  py::array_t<uint8_t> candidate_mask({batch, candidates});
  py::array_t<int16_t> candidate_arrivals({batch, candidates});
  py::array_t<int16_t> candidate_reasons({batch, candidates});
  py::array_t<float> candidate_features(
      {batch, candidates, tasks::kCandidateFeatureCount});
  const int targets = static_cast<int>(decisions.front().target_conflicts.size());
  const int resources =
      static_cast<int>(decisions.front().resource_conflicts.size());
  py::array_t<int16_t> target_conflicts({batch, targets});
  py::array_t<int16_t> resource_conflicts({batch, resources});
  py::array_t<int32_t> prefix_fields(
      {batch, prefix, tasks::kTaskFieldCount});
  py::array_t<uint8_t> prefix_mask({batch, prefix});
  py::array_t<float> root_features(
      {batch, tasks::kRootFeatureCount});
  for (int index = 0; index < batch; ++index) {
    const tasks::Decision& decision = decisions[index];
    unit_indices.mutable_at(index) = decision.unit_index;
    current_x.mutable_at(index) = decision.current_x;
    current_y.mutable_at(index) = decision.current_y;
    available_at.mutable_at(index) = decision.available_at;
    day_end.mutable_at(index) = decision.day_end;
    replan_reasons.mutable_at(index) = decision.replan_reason;
    std::copy(decision.mode_mask.begin(), decision.mode_mask.end(),
              mode_mask.mutable_data() +
                  static_cast<size_t>(index) * tasks::kModeCount);
    std::copy(decision.candidate_mask.begin(), decision.candidate_mask.end(),
              candidate_mask.mutable_data() +
                  static_cast<size_t>(index) * candidates);
    std::copy(decision.candidate_arrivals.begin(),
              decision.candidate_arrivals.end(),
              candidate_arrivals.mutable_data() +
                  static_cast<size_t>(index) * candidates);
    std::copy(decision.candidate_reasons.begin(),
              decision.candidate_reasons.end(),
              candidate_reasons.mutable_data() +
                  static_cast<size_t>(index) * candidates);
    std::copy(decision.candidate_features.begin(),
              decision.candidate_features.end(),
              candidate_features.mutable_data() +
                  static_cast<size_t>(index) * candidates *
                      tasks::kCandidateFeatureCount);
    std::copy(decision.target_conflicts.begin(),
              decision.target_conflicts.end(),
              target_conflicts.mutable_data() +
                  static_cast<size_t>(index) * targets);
    std::copy(decision.resource_conflicts.begin(),
              decision.resource_conflicts.end(),
              resource_conflicts.mutable_data() +
                  static_cast<size_t>(index) * resources);
    std::copy(decision.prefix_fields.begin(), decision.prefix_fields.end(),
              prefix_fields.mutable_data() +
                  static_cast<size_t>(index) * prefix *
                      tasks::kTaskFieldCount);
    std::copy(decision.prefix_mask.begin(), decision.prefix_mask.end(),
              prefix_mask.mutable_data() +
                  static_cast<size_t>(index) * prefix);
    std::copy(decision.root_features.begin(), decision.root_features.end(),
              root_features.mutable_data() +
                  static_cast<size_t>(index) * tasks::kRootFeatureCount);
  }
  py::dict out;
  out["unit_indices"] = std::move(unit_indices);
  out["current_x"] = std::move(current_x);
  out["current_y"] = std::move(current_y);
  out["available_at"] = std::move(available_at);
  out["day_end"] = std::move(day_end);
  out["replan_reasons"] = std::move(replan_reasons);
  out["mode_mask"] = std::move(mode_mask);
  out["candidate_mask"] = std::move(candidate_mask);
  out["candidate_arrivals"] = std::move(candidate_arrivals);
  out["candidate_reasons"] = std::move(candidate_reasons);
  out["candidate_features"] = std::move(candidate_features);
  out["target_conflicts"] = std::move(target_conflicts);
  out["resource_conflicts"] = std::move(resource_conflicts);
  out["prefix_fields"] = std::move(prefix_fields);
  out["prefix_mask"] = std::move(prefix_mask);
  out["root_features"] = std::move(root_features);
  out["version"] = tasks::kAbiVersion;
  return out;
}

void SelectUnitTaskBatch(const UnitTaskOwners& owners, IntArray modes,
                         IntArray candidate_indices, IntArray quantities,
                         IntArray earliest, IntArray deadlines, int workers) {
  const int batch = static_cast<int>(owners.sessions.size());
  const py::buffer_info mode_info = modes.request();
  const py::buffer_info candidate_info = candidate_indices.request();
  const py::buffer_info quantity_info = quantities.request();
  const py::buffer_info earliest_info = earliest.request();
  const py::buffer_info deadline_info = deadlines.request();
  const auto vector_shape = [batch](const py::buffer_info& info) {
    return info.ndim == 1 && info.shape[0] == batch;
  };
  if (!vector_shape(mode_info) || !vector_shape(candidate_info) ||
      !vector_shape(quantity_info) || !vector_shape(earliest_info) ||
      !vector_shape(deadline_info)) {
    throw py::value_error("unit-task selections must be aligned vectors");
  }
  const auto* mode_data = static_cast<const int64_t*>(mode_info.ptr);
  const auto* candidate_data = static_cast<const int64_t*>(candidate_info.ptr);
  const auto* quantity_data = static_cast<const int64_t*>(quantity_info.ptr);
  const auto* earliest_data = static_cast<const int64_t*>(earliest_info.ptr);
  const auto* deadline_data = static_cast<const int64_t*>(deadline_info.ptr);
  std::exception_ptr first_error;
  std::mutex error_mutex;
  {
    py::gil_scoped_release release;
#ifdef _OPENMP
#pragma omp parallel for schedule(static) num_threads(workers)
#endif
    for (int index = 0; index < batch; ++index) {
      try {
        owners.sessions[index]->Select(
            *owners.engines[index], owners.players[index],
            static_cast<tasks::SuffixMode>(mode_data[index]),
            static_cast<int>(candidate_data[index]), quantity_data[index],
            static_cast<int>(earliest_data[index]),
            static_cast<int>(deadline_data[index]));
      } catch (...) {
        std::lock_guard<std::mutex> lock(error_mutex);
        if (!first_error) first_error = std::current_exception();
      }
    }
  }
  if (first_error) std::rethrow_exception(first_error);
}

py::dict MakeUnitTaskActions(const UnitTaskOwners& owners, int workers) {
  const int batch = static_cast<int>(owners.sessions.size());
  const int width = owners.sessions.front()->unit_limit();
  std::vector<tasks::NumericUnitAction> actions(static_cast<size_t>(batch));
  std::exception_ptr first_error;
  std::mutex error_mutex;
  {
    py::gil_scoped_release release;
#ifdef _OPENMP
#pragma omp parallel for schedule(static) num_threads(workers)
#endif
    for (int index = 0; index < batch; ++index) {
      try {
        actions[index] = owners.sessions[index]->Action(
            *owners.engines[index], owners.players[index]);
      } catch (...) {
        std::lock_guard<std::mutex> lock(error_mutex);
        if (!first_error) first_error = std::current_exception();
      }
    }
  }
  if (first_error) std::rethrow_exception(first_error);
  py::array_t<int64_t> tokens({batch, width});
  py::array_t<int64_t> quantities({batch, width});
  py::array_t<int64_t> task_results({batch, width});
  py::array_t<int64_t> unit_counts(batch);
  py::array_t<uint8_t> requires_decision(batch);
  std::fill_n(tokens.mutable_data(), tokens.size(), int64_t{0});
  std::fill_n(quantities.mutable_data(), quantities.size(), int64_t{0});
  std::fill_n(task_results.mutable_data(), task_results.size(), int64_t{-1});
  for (int index = 0; index < batch; ++index) {
    const tasks::NumericUnitAction& action = actions[index];
    if (action.unit_count > width) {
      throw py::value_error("unit-task action exceeds the actor unit limit");
    }
    std::copy(action.tokens.begin(), action.tokens.end(),
              tokens.mutable_data() + static_cast<size_t>(index) * width);
    std::copy(action.quantities.begin(), action.quantities.end(),
              quantities.mutable_data() + static_cast<size_t>(index) * width);
    std::copy(action.task_results.begin(), action.task_results.end(),
              task_results.mutable_data() +
                  static_cast<size_t>(index) * width);
    unit_counts.mutable_at(index) = action.unit_count;
    requires_decision.mutable_at(index) = action.requires_decision ? 1 : 0;
  }
  py::dict out;
  out["tokens"] = std::move(tokens);
  out["quantities"] = std::move(quantities);
  out["task_results"] = std::move(task_results);
  out["unit_counts"] = std::move(unit_counts);
  out["requires_decision"] = std::move(requires_decision);
  return out;
}

py::array_t<uint8_t> UnitTaskDecisionRequired(const UnitTaskOwners& owners,
                                               int workers) {
  const int batch = static_cast<int>(owners.sessions.size());
  py::array_t<uint8_t> required(batch);
  std::exception_ptr first_error;
  std::mutex error_mutex;
  {
    py::gil_scoped_release release;
#ifdef _OPENMP
#pragma omp parallel for schedule(static) num_threads(workers)
#endif
    for (int index = 0; index < batch; ++index) {
      try {
        required.mutable_data()[index] =
            owners.sessions[index]->DecisionRequired(
                *owners.engines[index], owners.players[index])
                ? 1
                : 0;
      } catch (...) {
        std::lock_guard<std::mutex> lock(error_mutex);
        if (!first_error) first_error = std::current_exception();
      }
    }
  }
  if (first_error) std::rethrow_exception(first_error);
  return required;
}

void BindUnitTasks(py::module_& module) {
  py::class_<tasks::VisibleState>(module, "UnitTaskVisibleState");
  py::class_<tasks::Session>(module, "UnitTaskSession")
      .def(py::init([](py::object configuration, int unit_limit,
                       int maximum_quantity) {
             return std::make_unique<tasks::Session>(
                 pyconv::ParseConfig(configuration), unit_limit,
                 maximum_quantity);
           }),
           py::arg("configuration") = py::none(), py::arg("unit_limit") = 16,
           py::arg("maximum_quantity") = 128)
      .def(
          "visible_state",
          [](const tasks::Session& session, const py::dict& observation) {
            return ParseUnitTaskVisibleState(session, observation);
          },
          py::arg("observation"))
      .def(
          "observation_visible",
          [](tasks::Session& session, const tasks::VisibleState& state) {
            return UnitTaskDecisionToPy(
                session.Observe(state.farm, state.priv, state.step,
                                state.player),
                session);
          },
          py::arg("state"))
      .def(
          "compact_observation_visible",
          [](tasks::Session& session, const tasks::VisibleState& state) {
            return CompactUnitTaskDecisionToPy(
                session.ObserveCompact(state.farm, state.priv, state.step,
                                       state.player),
                session);
          },
          py::arg("state"))
      .def(
          "select_visible",
          [](tasks::Session& session, const tasks::VisibleState& state,
             int64_t mode, int candidate_index, int64_t quantity,
             int earliest, int deadline) {
            session.Select(state.farm, state.priv, state.step, state.player,
                           static_cast<tasks::SuffixMode>(mode),
                           candidate_index, quantity, earliest, deadline);
          },
          py::arg("state"), py::arg("mode"),
          py::arg("candidate_index"), py::arg("quantity"),
          py::arg("earliest"), py::arg("deadline"))
      .def(
          "action_numeric_visible",
          [](tasks::Session& session, const tasks::VisibleState& state) {
            return UnitTaskActionToPy(session.Action(
                state.farm, state.priv, state.step, state.player));
          },
          py::arg("state"))
      .def(
          "decision_required_visible",
          [](tasks::Session& session, const tasks::VisibleState& state) {
            return session.DecisionRequired(
                state.farm, state.priv, state.step, state.player);
          },
          py::arg("state"))
      .def(
          "observation",
          [](tasks::Session& session, const PyEngine& owner, int player) {
            return UnitTaskDecisionToPy(
                session.Observe(owner.raw_engine(), player), session);
          },
          py::arg("engine"), py::arg("player"))
      .def(
          "compact_observation",
          [](tasks::Session& session, const PyEngine& owner, int player) {
            return CompactUnitTaskDecisionToPy(
                session.ObserveCompact(owner.raw_engine(), player), session);
          },
          py::arg("engine"), py::arg("player"))
      .def(
          "select",
          [](tasks::Session& session, const PyEngine& owner, int player,
             int64_t mode, int candidate_index, int64_t quantity,
             int earliest, int deadline) {
            session.Select(owner.raw_engine(), player,
                           static_cast<tasks::SuffixMode>(mode),
                           candidate_index, quantity, earliest, deadline);
          },
          py::arg("engine"), py::arg("player"), py::arg("mode"),
          py::arg("candidate_index"), py::arg("quantity"),
          py::arg("earliest"), py::arg("deadline"))
      .def(
          "action_numeric",
          [](tasks::Session& session, const PyEngine& owner, int player) {
            return UnitTaskActionToPy(
                session.Action(owner.raw_engine(), player));
          },
          py::arg("engine"), py::arg("player"))
      .def(
          "decision_required",
          [](tasks::Session& session, const PyEngine& owner, int player) {
            return session.DecisionRequired(owner.raw_engine(), player);
          },
          py::arg("engine"), py::arg("player"))
      .def("spec", &UnitTaskSpecForSession)
      .def("reset", &tasks::Session::Reset)
      .def_property_readonly("candidate_count",
                             &tasks::Session::candidate_count)
      .def_property_readonly("prefix_capacity",
                             &tasks::Session::prefix_capacity)
      .def_property_readonly("unit_limit", &tasks::Session::unit_limit)
      .def_property_readonly("maximum_quantity",
                             &tasks::Session::maximum_quantity);
  module.def(
      "unit_task_spec",
      [](py::object configuration, int unit_limit, int maximum_quantity) {
        const tasks::Session session(pyconv::ParseConfig(configuration),
                                     unit_limit, maximum_quantity);
        return UnitTaskSpecForSession(session);
      },
      py::arg("configuration") = py::none(), py::arg("unit_limit") = 16,
      py::arg("maximum_quantity") = 128);
  module.def(
      "unit_task_snapshots_batch",
      [](py::list sessions, py::list engines, IntArray players, int workers) {
        return MakeUnitTaskSnapshots(
            ParseUnitTaskOwners(sessions, engines, std::move(players), workers),
            workers);
      },
      py::arg("sessions"), py::arg("engines"), py::arg("players"),
      py::arg("workers"));
  module.def(
      "unit_task_apply_sequences_batch",
      [](py::list sessions, py::list engines, IntArray players,
         py::array_t<int16_t,
                     py::array::c_style | py::array::forcecast> selections,
         py::array_t<int16_t,
                     py::array::c_style | py::array::forcecast> counts,
         int workers) {
        ApplyUnitTaskSequences(
            ParseUnitTaskOwners(sessions, engines, std::move(players), workers),
            std::move(selections), std::move(counts), workers);
      },
      py::arg("sessions"), py::arg("engines"), py::arg("players"),
      py::arg("selections"), py::arg("counts"), py::arg("workers"));
  module.def(
      "unit_task_observations_batch",
      [](py::list sessions, py::list engines, IntArray players, int workers) {
        return MakeUnitTaskDecisions(
            ParseUnitTaskOwners(sessions, engines, std::move(players), workers),
            workers);
      },
      py::arg("sessions"), py::arg("engines"), py::arg("players"),
      py::arg("workers"));
  module.def(
      "unit_task_select_batch",
      [](py::list sessions, py::list engines, IntArray players,
         IntArray modes, IntArray candidate_indices, IntArray quantities,
         IntArray earliest, IntArray deadlines, int workers) {
        SelectUnitTaskBatch(
            ParseUnitTaskOwners(sessions, engines, std::move(players), workers),
            std::move(modes), std::move(candidate_indices),
            std::move(quantities), std::move(earliest),
            std::move(deadlines), workers);
      },
      py::arg("sessions"), py::arg("engines"), py::arg("players"),
      py::arg("modes"), py::arg("candidate_indices"),
      py::arg("quantities"), py::arg("earliest"), py::arg("deadlines"),
      py::arg("workers"));
  module.def(
      "unit_task_actions_batch",
      [](py::list sessions, py::list engines, IntArray players, int workers) {
        return MakeUnitTaskActions(
            ParseUnitTaskOwners(sessions, engines, std::move(players), workers),
            workers);
      },
      py::arg("sessions"), py::arg("engines"), py::arg("players"),
      py::arg("workers"));
  module.def(
      "unit_task_decision_required_batch",
      [](py::list sessions, py::list engines, IntArray players, int workers) {
        return UnitTaskDecisionRequired(
            ParseUnitTaskOwners(sessions, engines, std::move(players), workers),
            workers);
      },
      py::arg("sessions"), py::arg("engines"), py::arg("players"),
      py::arg("workers"));
}
