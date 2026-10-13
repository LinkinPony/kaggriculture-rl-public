// Included by bindings.cpp inside its private kagg namespace so this boundary
// can use the translation-unit-local PyEngine wrapper.

py::dict PlanSpec() {
  py::dict out;
  out["version"] = plans::kSpecVersion;
  out["production_line_count"] = plans::kProductionLineCount;
  out["line_field_count"] = plans::kLineFieldCount;
  out["global_field_count"] = plans::kGlobalFieldCount;
  out["mode_token_count"] = plans::kModeTokenCount;
  out["line_operation_token_count"] = plans::kLineOperationTokenCount;
  out["line_value_token_count"] = plans::kLineValueTokenCount;
  out["global_operation_token_count"] =
      plans::kGlobalOperationTokenCount;
  out["global_value_token_count"] = plans::kGlobalValueTokenCount;
  out["observation_feature_count"] = plans::kObservationFeatureCount;
  out["event_count"] = plans::kEventCount;
  out["journal_feature_count"] = plans::kJournalFeatureCount;
  out["line_fields"] = py::make_tuple(
      "target", "scale_mode", "priority", "output_reserve",
      "price_policy", "optional_yield");
  out["global_fields"] = py::make_tuple(
      "worker_ceiling", "land_ceiling", "cash_reserve", "spend_cap",
      "prevent_loss_priority", "harvest_priority", "supply_priority",
      "expand_priority", "optional_yield_priority",
      "return_inventory_priority");
  out["count_buckets"] = py::make_tuple(
      0, 1, 2, 3, 4, 6, 8, 12, 16, 24, 32, 48, 64, 80, 96, 128);
  py::dict modes;
  for (int token = 0; token < plans::kModeTokenCount; ++token) {
    modes[plans::ModeName(static_cast<plans::Mode>(token))] = token;
  }
  out["modes"] = std::move(modes);
  py::dict line_operations;
  for (int token = 0; token < plans::kLineOperationTokenCount; ++token) {
    line_operations[plans::LineOperationName(
        static_cast<plans::LineOperation>(token))] = token;
  }
  out["line_operations"] = std::move(line_operations);
  py::dict global_operations;
  for (int token = 0; token < plans::kGlobalOperationTokenCount; ++token) {
    global_operations[plans::GlobalOperationName(
        static_cast<plans::GlobalOperation>(token))] = token;
  }
  out["global_operations"] = std::move(global_operations);
  py::list production_lines;
  for (int crop = 0; crop < kNumCrops; ++crop) {
    production_lines.append(std::string("crop:") + kItemNames[crop]);
  }
  for (int animal = 0; animal < kNumAnimals; ++animal) {
    production_lines.append(std::string("animal:") +
                            kItemNames[item::kGoose + animal]);
  }
  out["production_lines"] = std::move(production_lines);
  py::list features;
  for (const std::string& name : plans::ObservationFeatureNames()) {
    features.append(name);
  }
  out["observation_features"] = std::move(features);
  py::list journal;
  for (const std::string& name : plans::JournalFeatureNames()) journal.append(name);
  out["journal_features"] = std::move(journal);
  py::list events;
  for (const std::string& name : plans::EventNames()) events.append(name);
  out["events"] = std::move(events);
  out["compiler_abi"] = "native-portfolio-executor-v7";
  return out;
}

struct PlanOwners {
  std::vector<plans::Session*> sessions;
  std::vector<const Engine*> engines;
  std::vector<int> players;
};

PlanOwners ParsePlanOwners(py::list session_owners, py::list engine_owners,
                           IntArray players, int workers) {
  const int batch = static_cast<int>(py::len(session_owners));
  if (batch < 1 || py::len(engine_owners) != static_cast<py::size_t>(batch)) {
    throw py::value_error(
        "structured-plan batch inputs must be nonempty and aligned");
  }
  if (workers < 1 || workers > 256) {
    throw py::value_error("structured-plan workers must be in [1, 256]");
  }
  const py::buffer_info info = players.request();
  if (info.ndim != 1 || info.shape[0] != batch) {
    throw py::value_error("structured-plan players must have shape [B]");
  }
  const auto* values = static_cast<const int64_t*>(info.ptr);
  PlanOwners result;
  result.sessions.reserve(static_cast<size_t>(batch));
  result.engines.reserve(static_cast<size_t>(batch));
  result.players.reserve(static_cast<size_t>(batch));
  for (int index = 0; index < batch; ++index) {
    const int player = static_cast<int>(values[index]);
    if (player < 0 || player > 1) {
      throw py::value_error("structured-plan player must be 0 or 1");
    }
    result.sessions.push_back(
        &py::cast<plans::Session&>(session_owners[index]));
    result.engines.push_back(
        &py::cast<const PyEngine&>(engine_owners[index]).raw_engine());
    result.players.push_back(player);
  }
  return result;
}

py::dict PlanObservationToPy(const plans::Observation& observation) {
  py::array_t<float> features(plans::kObservationFeatureCount);
  py::array_t<float> journal(plans::kJournalFeatureCount);
  py::array_t<int64_t> active_lines(
      {plans::kProductionLineCount, plans::kLineFieldCount});
  py::array_t<uint8_t> active_line_mask(plans::kProductionLineCount);
  py::array_t<int64_t> global_plan(plans::kGlobalFieldCount);
  std::copy(observation.features.begin(), observation.features.end(),
            features.mutable_data());
  std::copy(observation.journal.begin(), observation.journal.end(),
            journal.mutable_data());
  for (int line = 0; line < plans::kProductionLineCount; ++line) {
    std::copy(observation.active_lines[line].begin(),
              observation.active_lines[line].end(),
              active_lines.mutable_data() +
                  static_cast<size_t>(line) * plans::kLineFieldCount);
  }
  std::copy(observation.active_line_mask.begin(),
            observation.active_line_mask.end(),
            active_line_mask.mutable_data());
  std::copy(observation.global_plan.begin(), observation.global_plan.end(),
            global_plan.mutable_data());
  py::dict out;
  out["features"] = std::move(features);
  out["journal"] = std::move(journal);
  out["event_mask"] = observation.event_mask;
  out["active_lines"] = std::move(active_lines);
  out["active_line_mask"] = std::move(active_line_mask);
  out["global_plan"] = std::move(global_plan);
  out["version"] = plans::kSpecVersion;
  return out;
}

py::dict PlanObservationRowsToPy(
    const std::vector<plans::Observation>& rows,
    const std::vector<int64_t>* source_indices = nullptr) {
  const int batch = static_cast<int>(rows.size());
  py::array_t<float> features({batch, plans::kObservationFeatureCount});
  py::array_t<float> journal({batch, plans::kJournalFeatureCount});
  py::array_t<uint64_t> event_mask(batch);
  py::array_t<int64_t> active_lines(
      {batch, plans::kProductionLineCount, plans::kLineFieldCount});
  py::array_t<uint8_t> active_line_mask(
      {batch, plans::kProductionLineCount});
  py::array_t<int64_t> global_plan(
      {batch, plans::kGlobalFieldCount});
  for (int index = 0; index < batch; ++index) {
    const plans::Observation& row = rows[index];
    std::copy(row.features.begin(), row.features.end(),
              features.mutable_data() +
                  static_cast<size_t>(index) * plans::kObservationFeatureCount);
    std::copy(row.journal.begin(), row.journal.end(),
              journal.mutable_data() +
                  static_cast<size_t>(index) * plans::kJournalFeatureCount);
    event_mask.mutable_at(index) = row.event_mask;
    for (int line = 0; line < plans::kProductionLineCount; ++line) {
      std::copy(row.active_lines[line].begin(),
                row.active_lines[line].end(),
                active_lines.mutable_data() +
                    (static_cast<size_t>(index) *
                         plans::kProductionLineCount +
                     line) *
                        plans::kLineFieldCount);
      active_line_mask.mutable_at(index, line) =
          row.active_line_mask[line];
    }
    std::copy(row.global_plan.begin(), row.global_plan.end(),
              global_plan.mutable_data() +
                  static_cast<size_t>(index) * plans::kGlobalFieldCount);
  }
  py::dict out;
  out["features"] = std::move(features);
  out["journal"] = std::move(journal);
  out["event_mask"] = std::move(event_mask);
  out["active_lines"] = std::move(active_lines);
  out["active_line_mask"] = std::move(active_line_mask);
  out["global_plan"] = std::move(global_plan);
  out["version"] = plans::kSpecVersion;
  if (source_indices != nullptr) {
    py::array_t<int64_t> indices(batch);
    std::copy(source_indices->begin(), source_indices->end(),
              indices.mutable_data());
    out["indices"] = std::move(indices);
  }
  return out;
}

py::dict MakePlanObservations(const PlanOwners& owners, int workers) {
  const int batch = static_cast<int>(owners.sessions.size());
  std::vector<plans::Observation> rows(static_cast<size_t>(batch));
  std::exception_ptr first_error;
  std::mutex error_mutex;
  {
    py::gil_scoped_release release;
#ifdef _OPENMP
#pragma omp parallel for schedule(static) num_threads(workers)
#endif
    for (int index = 0; index < batch; ++index) {
      try {
        rows[index] = owners.sessions[index]->Observe(
            *owners.engines[index], owners.players[index]);
      } catch (...) {
        std::lock_guard<std::mutex> lock(error_mutex);
        if (!first_error) first_error = std::current_exception();
      }
    }
  }
  if (first_error) std::rethrow_exception(first_error);
  return PlanObservationRowsToPy(rows);
}

py::dict MakeReadyPlanObservations(const PlanOwners& owners, int workers) {
  const int batch = static_cast<int>(owners.sessions.size());
  std::vector<plans::Observation> candidates(static_cast<size_t>(batch));
  std::vector<uint8_t> ready(static_cast<size_t>(batch), uint8_t{0});
  std::exception_ptr first_error;
  std::mutex error_mutex;
  {
    py::gil_scoped_release release;
#ifdef _OPENMP
#pragma omp parallel for schedule(static) num_threads(workers)
#endif
    for (int index = 0; index < batch; ++index) {
      try {
        if (owners.engines[index]->done()) continue;
        if (owners.sessions[index]->DecisionRequired(
                *owners.engines[index], owners.players[index])) {
          candidates[index] = owners.sessions[index]->Observe(
              *owners.engines[index], owners.players[index]);
          ready[index] = 1;
        }
      } catch (...) {
        std::lock_guard<std::mutex> lock(error_mutex);
        if (!first_error) first_error = std::current_exception();
      }
    }
  }
  if (first_error) std::rethrow_exception(first_error);
  std::vector<plans::Observation> rows;
  std::vector<int64_t> indices;
  rows.reserve(static_cast<size_t>(batch));
  indices.reserve(static_cast<size_t>(batch));
  for (int index = 0; index < batch; ++index) {
    if (ready[index] == 0) continue;
    rows.push_back(std::move(candidates[index]));
    indices.push_back(index);
  }
  return PlanObservationRowsToPy(rows, &indices);
}

void ApplyPlanBatch(const PlanOwners& owners, IntArray modes,
                    IntArray line_operations, IntArray line_values,
                    IntArray global_operations, IntArray global_values,
                    int workers) {
  const int batch = static_cast<int>(owners.sessions.size());
  const py::buffer_info mode_info = modes.request();
  const py::buffer_info line_operation_info = line_operations.request();
  const py::buffer_info line_value_info = line_values.request();
  const py::buffer_info global_operation_info = global_operations.request();
  const py::buffer_info global_value_info = global_values.request();
  if (mode_info.ndim != 1 || mode_info.shape[0] != batch ||
      line_operation_info.ndim != 2 ||
      line_operation_info.shape[0] != batch ||
      line_operation_info.shape[1] != plans::kProductionLineCount ||
      line_value_info.ndim != 3 || line_value_info.shape[0] != batch ||
      line_value_info.shape[1] != plans::kProductionLineCount ||
      line_value_info.shape[2] != plans::kLineFieldCount ||
      global_operation_info.ndim != 1 ||
      global_operation_info.shape[0] != batch ||
      global_value_info.ndim != 2 ||
      global_value_info.shape[0] != batch ||
      global_value_info.shape[1] != plans::kGlobalFieldCount) {
    throw py::value_error(
        "structured-plan apply expects mode/global operation [B], "
        "line operations [B,8], line values [B,8,6], and global "
        "values [B,10]");
  }
  const auto* mode_data = static_cast<const int64_t*>(mode_info.ptr);
  const auto* line_operation_data =
      static_cast<const int64_t*>(line_operation_info.ptr);
  const auto* line_value_data =
      static_cast<const int64_t*>(line_value_info.ptr);
  const auto* global_operation_data =
      static_cast<const int64_t*>(global_operation_info.ptr);
  const auto* global_value_data =
      static_cast<const int64_t*>(global_value_info.ptr);
  std::exception_ptr first_error;
  std::mutex error_mutex;
  {
    py::gil_scoped_release release;
#ifdef _OPENMP
#pragma omp parallel for schedule(static) num_threads(workers)
#endif
    for (int index = 0; index < batch; ++index) {
      try {
        owners.sessions[index]->Apply(
            *owners.engines[index], owners.players[index],
            static_cast<plans::Mode>(mode_data[index]),
            line_operation_data +
                static_cast<size_t>(index) *
                    plans::kProductionLineCount,
            line_value_data +
                static_cast<size_t>(index) *
                    plans::kProductionLineCount * plans::kLineFieldCount,
            static_cast<plans::GlobalOperation>(
                global_operation_data[index]),
            global_value_data +
                static_cast<size_t>(index) * plans::kGlobalFieldCount);
      } catch (...) {
        std::lock_guard<std::mutex> lock(error_mutex);
        if (!first_error) first_error = std::current_exception();
      }
    }
  }
  if (first_error) std::rethrow_exception(first_error);
}

py::dict PlanActionToPy(const plans::NumericAction& action) {
  py::array_t<int64_t> tokens(action.decision_count);
  py::array_t<int64_t> quantities(action.decision_count);
  py::array_t<int64_t> unit_sources(action.unit_count);
  py::array_t<int64_t> unit_reasons(action.unit_count);
  py::array_t<int64_t> market_sources(action.market_sources.size());
  std::copy(action.tokens.begin(), action.tokens.end(), tokens.mutable_data());
  std::copy(action.quantities.begin(), action.quantities.end(),
            quantities.mutable_data());
  std::copy(action.unit_sources.begin(), action.unit_sources.end(),
            unit_sources.mutable_data());
  std::copy(action.unit_reasons.begin(), action.unit_reasons.end(),
            unit_reasons.mutable_data());
  std::copy(action.market_sources.begin(), action.market_sources.end(),
            market_sources.mutable_data());
  py::dict out;
  out["tokens"] = std::move(tokens);
  out["quantities"] = std::move(quantities);
  out["decision_count"] = action.decision_count;
  out["unit_count"] = action.unit_count;
  out["requires_decision"] = action.requires_decision;
  out["unit_sources"] = std::move(unit_sources);
  out["unit_reasons"] = std::move(unit_reasons);
  out["market_sources"] = std::move(market_sources);
  return out;
}

py::dict MakePlanActions(const PlanOwners& owners, int workers) {
  const int batch = static_cast<int>(owners.sessions.size());
  std::vector<plans::NumericAction> actions(static_cast<size_t>(batch));
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
  int width = 1;
  int units = 1;
  int markets = 1;
  for (const plans::NumericAction& action : actions) {
    width = std::max(width, static_cast<int>(action.decision_count));
    units = std::max(units, static_cast<int>(action.unit_count));
    markets =
        std::max(markets, static_cast<int>(action.market_sources.size()));
  }
  py::array_t<int64_t> tokens({batch, width});
  py::array_t<int64_t> quantities({batch, width});
  py::array_t<int64_t> decision_counts(batch);
  py::array_t<int64_t> unit_counts(batch);
  py::array_t<uint8_t> requires_decision(batch);
  py::array_t<int64_t> unit_sources({batch, units});
  py::array_t<int64_t> unit_reasons({batch, units});
  py::array_t<int64_t> market_sources({batch, markets});
  std::fill_n(tokens.mutable_data(), tokens.size(), int64_t{0});
  std::fill_n(quantities.mutable_data(), quantities.size(), int64_t{0});
  std::fill_n(unit_sources.mutable_data(), unit_sources.size(), int64_t{-1});
  std::fill_n(unit_reasons.mutable_data(), unit_reasons.size(), int64_t{0});
  std::fill_n(market_sources.mutable_data(), market_sources.size(),
              int64_t{-1});
  for (int index = 0; index < batch; ++index) {
    const plans::NumericAction& action = actions[index];
    std::copy(action.tokens.begin(), action.tokens.end(),
              tokens.mutable_data() + static_cast<size_t>(index) * width);
    std::copy(action.quantities.begin(), action.quantities.end(),
              quantities.mutable_data() +
                  static_cast<size_t>(index) * width);
    std::copy(action.unit_sources.begin(), action.unit_sources.end(),
              unit_sources.mutable_data() +
                  static_cast<size_t>(index) * units);
    std::copy(action.unit_reasons.begin(), action.unit_reasons.end(),
              unit_reasons.mutable_data() +
                  static_cast<size_t>(index) * units);
    std::copy(action.market_sources.begin(), action.market_sources.end(),
              market_sources.mutable_data() +
                  static_cast<size_t>(index) * markets);
    decision_counts.mutable_at(index) = action.decision_count;
    unit_counts.mutable_at(index) = action.unit_count;
    requires_decision.mutable_at(index) = action.requires_decision ? 1 : 0;
  }
  py::dict out;
  out["tokens"] = std::move(tokens);
  out["quantities"] = std::move(quantities);
  out["decision_counts"] = std::move(decision_counts);
  out["unit_counts"] = std::move(unit_counts);
  out["requires_decision"] = std::move(requires_decision);
  out["unit_sources"] = std::move(unit_sources);
  out["unit_reasons"] = std::move(unit_reasons);
  out["market_sources"] = std::move(market_sources);
  return out;
}

py::array_t<uint8_t> PlanDecisionRequired(const PlanOwners& owners,
                                           int workers) {
  const int batch = static_cast<int>(owners.sessions.size());
  py::array_t<uint8_t> required(batch);
  auto* values = required.mutable_data();
  std::exception_ptr first_error;
  std::mutex error_mutex;
  {
    py::gil_scoped_release release;
#ifdef _OPENMP
#pragma omp parallel for schedule(static) num_threads(workers)
#endif
    for (int index = 0; index < batch; ++index) {
      try {
        values[index] = owners.sessions[index]->DecisionRequired(
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

PlayerAction DecodePlanAction(const plans::NumericAction& encoded,
                              const Engine& engine) {
  if (encoded.requires_decision) {
    throw std::logic_error(
        "structured-plan native tick reached an unapplied decision");
  }
  if (encoded.unit_count < 1 || encoded.decision_count < encoded.unit_count ||
      encoded.decision_count != static_cast<int64_t>(encoded.tokens.size()) ||
      encoded.quantities.size() != encoded.tokens.size()) {
    throw std::logic_error("structured-plan compiler emitted an invalid action");
  }
  return policy::DecodePlayerAction(
      encoded.tokens.data(), encoded.quantities.data(),
      static_cast<int>(encoded.decision_count),
      static_cast<int>(encoded.unit_count),
      engine.config().max_market_orders);
}

template <typename OpponentSession>
py::array_t<uint8_t> StepPlanOpponentBatch(
    py::list engine_owners, IntArray candidate_players,
    py::list plan_owners, py::list opponent_owners, int workers) {
  const int batch = static_cast<int>(py::len(engine_owners));
  if (batch < 1 || py::len(plan_owners) != static_cast<py::size_t>(batch) ||
      py::len(opponent_owners) != static_cast<py::size_t>(batch)) {
    throw py::value_error(
        "structured-plan opponent tick inputs must be nonempty and aligned");
  }
  if (workers < 1 || workers > 256) {
    throw py::value_error(
        "structured-plan opponent tick workers must be in [1, 256]");
  }
  const py::buffer_info player_info = candidate_players.request();
  if (player_info.ndim != 1 || player_info.shape[0] != batch) {
    throw py::value_error(
        "structured-plan opponent tick players must have shape [B]");
  }
  const auto* players = static_cast<const int64_t*>(player_info.ptr);
  std::vector<Engine*> engines;
  std::vector<plans::Session*> plan_sessions;
  std::vector<OpponentSession*> opponent_sessions;
  engines.reserve(static_cast<size_t>(batch));
  plan_sessions.reserve(static_cast<size_t>(batch));
  opponent_sessions.reserve(static_cast<size_t>(batch));
  for (int index = 0; index < batch; ++index) {
    engines.push_back(
        &py::cast<PyEngine&>(engine_owners[index]).mutable_engine());
    plan_sessions.push_back(&py::cast<plans::Session&>(plan_owners[index]));
    opponent_sessions.push_back(
        &py::cast<OpponentSession&>(opponent_owners[index]));
  }
  py::array_t<uint8_t> done(batch);
  auto* done_data = done.mutable_data();
  std::exception_ptr first_error;
  std::mutex error_mutex;
  {
    py::gil_scoped_release release;
#ifdef _OPENMP
#pragma omp parallel for schedule(static) num_threads(workers)
#endif
    for (int index = 0; index < batch; ++index) {
      try {
        const int candidate = static_cast<int>(players[index]);
        if (candidate < 0 || candidate > 1) {
          throw std::invalid_argument("candidate player must be 0 or 1");
        }
        Engine& engine = *engines[index];
        std::array<PlayerAction, 2> actions;
        actions[candidate] = DecodePlanAction(
            plan_sessions[index]->Action(engine, candidate), engine);
        actions[1 - candidate] =
            opponent_sessions[index]->Act(engine, 1 - candidate);
        engine.Step(actions[0], actions[1]);
        done_data[index] = engine.done() ? 1 : 0;
      } catch (...) {
        std::lock_guard<std::mutex> lock(error_mutex);
        if (!first_error) first_error = std::current_exception();
      }
    }
  }
  if (first_error) std::rethrow_exception(first_error);
  return done;
}

py::array_t<uint8_t> StepPlanSelfPlayBatch(
    py::list engine_owners, IntArray candidate_players,
    py::list candidate_plan_owners, py::list opponent_plan_owners,
    int workers) {
  const int batch = static_cast<int>(py::len(engine_owners));
  if (batch < 1 ||
      py::len(candidate_plan_owners) != static_cast<py::size_t>(batch) ||
      py::len(opponent_plan_owners) != static_cast<py::size_t>(batch)) {
    throw py::value_error(
        "structured-plan self-play tick inputs must be nonempty and aligned");
  }
  if (workers < 1 || workers > 256) {
    throw py::value_error(
        "structured-plan self-play tick workers must be in [1, 256]");
  }
  const py::buffer_info player_info = candidate_players.request();
  if (player_info.ndim != 1 || player_info.shape[0] != batch) {
    throw py::value_error(
        "structured-plan self-play tick players must have shape [B]");
  }
  const auto* players = static_cast<const int64_t*>(player_info.ptr);
  std::vector<Engine*> engines;
  std::vector<plans::Session*> candidate_plans;
  std::vector<plans::Session*> opponent_plans;
  engines.reserve(static_cast<size_t>(batch));
  candidate_plans.reserve(static_cast<size_t>(batch));
  opponent_plans.reserve(static_cast<size_t>(batch));
  for (int index = 0; index < batch; ++index) {
    engines.push_back(
        &py::cast<PyEngine&>(engine_owners[index]).mutable_engine());
    candidate_plans.push_back(
        &py::cast<plans::Session&>(candidate_plan_owners[index]));
    opponent_plans.push_back(
        &py::cast<plans::Session&>(opponent_plan_owners[index]));
  }
  py::array_t<uint8_t> done(batch);
  auto* done_data = done.mutable_data();
  std::exception_ptr first_error;
  std::mutex error_mutex;
  {
    py::gil_scoped_release release;
#ifdef _OPENMP
#pragma omp parallel for schedule(static) num_threads(workers)
#endif
    for (int index = 0; index < batch; ++index) {
      try {
        const int candidate = static_cast<int>(players[index]);
        if (candidate < 0 || candidate > 1) {
          throw std::invalid_argument("candidate player must be 0 or 1");
        }
        Engine& engine = *engines[index];
        std::array<PlayerAction, 2> actions;
        actions[candidate] = DecodePlanAction(
            candidate_plans[index]->Action(engine, candidate), engine);
        actions[1 - candidate] = DecodePlanAction(
            opponent_plans[index]->Action(engine, 1 - candidate), engine);
        engine.Step(actions[0], actions[1]);
        done_data[index] = engine.done() ? 1 : 0;
      } catch (...) {
        std::lock_guard<std::mutex> lock(error_mutex);
        if (!first_error) first_error = std::current_exception();
      }
    }
  }
  if (first_error) std::rethrow_exception(first_error);
  return done;
}

py::dict AdvancePlanSelfPlayBatch(
    py::list engine_owners, IntArray candidate_players,
    py::list candidate_plan_owners, py::list opponent_plan_owners,
    int workers) {
  const int batch = static_cast<int>(py::len(engine_owners));
  if (batch < 1 ||
      py::len(candidate_plan_owners) != static_cast<py::size_t>(batch) ||
      py::len(opponent_plan_owners) != static_cast<py::size_t>(batch)) {
    throw py::value_error(
        "structured-plan self-play advance inputs must be nonempty and "
        "aligned");
  }
  if (workers < 1 || workers > 256) {
    throw py::value_error(
        "structured-plan self-play advance workers must be in [1, 256]");
  }
  const py::buffer_info player_info = candidate_players.request();
  if (player_info.ndim != 1 || player_info.shape[0] != batch) {
    throw py::value_error(
        "structured-plan self-play advance players must have shape [B]");
  }
  const auto* players = static_cast<const int64_t*>(player_info.ptr);
  std::vector<Engine*> engines;
  std::vector<plans::Session*> candidate_plans;
  std::vector<plans::Session*> opponent_plans;
  engines.reserve(static_cast<size_t>(batch));
  candidate_plans.reserve(static_cast<size_t>(batch));
  opponent_plans.reserve(static_cast<size_t>(batch));
  for (int index = 0; index < batch; ++index) {
    engines.push_back(
        &py::cast<PyEngine&>(engine_owners[index]).mutable_engine());
    candidate_plans.push_back(
        &py::cast<plans::Session&>(candidate_plan_owners[index]));
    opponent_plans.push_back(
        &py::cast<plans::Session&>(opponent_plan_owners[index]));
  }
  py::array_t<uint8_t> done(batch);
  py::array_t<int64_t> advanced_turns(batch);
  auto* done_data = done.mutable_data();
  auto* advanced_data = advanced_turns.mutable_data();
  std::exception_ptr first_error;
  std::mutex error_mutex;
  {
    py::gil_scoped_release release;
#ifdef _OPENMP
#pragma omp parallel for schedule(static) num_threads(workers)
#endif
    for (int index = 0; index < batch; ++index) {
      try {
        const int candidate = static_cast<int>(players[index]);
        if (candidate < 0 || candidate > 1) {
          throw std::invalid_argument("candidate player must be 0 or 1");
        }
        Engine& engine = *engines[index];
        int64_t advanced = 0;
        while (!engine.done()) {
          const bool candidate_ready =
              candidate_plans[index]->DecisionRequired(engine, candidate);
          const bool opponent_ready =
              opponent_plans[index]->DecisionRequired(engine, 1 - candidate);
          if (candidate_ready || opponent_ready) break;
          std::array<PlayerAction, 2> actions;
          actions[candidate] = DecodePlanAction(
              candidate_plans[index]->Action(engine, candidate), engine);
          actions[1 - candidate] = DecodePlanAction(
              opponent_plans[index]->Action(engine, 1 - candidate), engine);
          engine.Step(actions[0], actions[1]);
          ++advanced;
        }
        advanced_data[index] = advanced;
        done_data[index] = engine.done() ? 1 : 0;
      } catch (...) {
        std::lock_guard<std::mutex> lock(error_mutex);
        if (!first_error) first_error = std::current_exception();
      }
    }
  }
  if (first_error) std::rethrow_exception(first_error);
  py::dict result;
  result["done"] = std::move(done);
  result["advanced_turns"] = std::move(advanced_turns);
  return result;
}

void BindStructuredPlans(py::module_& module) {
  py::class_<plans::Session>(module, "StructuredPlanSession")
      .def(py::init([](py::object configuration) {
             return std::make_unique<plans::Session>(
                 pyconv::ParseConfig(configuration));
           }),
           py::arg("configuration") = py::none())
      .def(
          "observation",
          [](plans::Session& session, const PyEngine& owner, int player) {
            return PlanObservationToPy(
                session.Observe(owner.raw_engine(), player));
          },
          py::arg("engine"), py::arg("player"))
      .def(
          "apply",
          [](plans::Session& session, const PyEngine& owner, int player,
             int64_t mode, IntArray line_operations, IntArray line_values,
             int64_t global_operation, IntArray global_values) {
            const py::buffer_info operation_info =
                line_operations.request();
            const py::buffer_info line_value_info = line_values.request();
            const py::buffer_info global_value_info = global_values.request();
            if (operation_info.ndim != 1 ||
                operation_info.shape[0] != plans::kProductionLineCount ||
                line_value_info.ndim != 2 ||
                line_value_info.shape[0] != plans::kProductionLineCount ||
                line_value_info.shape[1] != plans::kLineFieldCount ||
                global_value_info.ndim != 1 ||
                global_value_info.shape[0] != plans::kGlobalFieldCount) {
              throw py::value_error(
                  "structured-plan patch requires line operations [8], "
                  "line values [8,6], and global values [10]");
            }
            session.Apply(
                owner.raw_engine(), player,
                static_cast<plans::Mode>(mode),
                static_cast<const int64_t*>(operation_info.ptr),
                static_cast<const int64_t*>(line_value_info.ptr),
                static_cast<plans::GlobalOperation>(global_operation),
                static_cast<const int64_t*>(global_value_info.ptr));
          },
          py::arg("engine"), py::arg("player"), py::arg("mode"),
          py::arg("line_operations"), py::arg("line_values"),
          py::arg("global_operation"), py::arg("global_values"))
      .def(
          "action_numeric",
          [](plans::Session& session, const PyEngine& owner, int player) {
            return PlanActionToPy(
                session.Action(owner.raw_engine(), player));
          },
          py::arg("engine"), py::arg("player"))
      .def(
          "decision_required",
          [](plans::Session& session, const PyEngine& owner, int player) {
            return session.DecisionRequired(owner.raw_engine(), player);
          },
          py::arg("engine"), py::arg("player"))
      .def("reset", &plans::Session::Reset)
      .def_property_readonly("active", &plans::Session::active)
      .def_property_readonly("paused", &plans::Session::paused)
      .def_property_readonly("active_line_count",
                             &plans::Session::active_line_count)
      .def_property_readonly("pending_events",
                             &plans::Session::pending_events)
      .def_property_readonly(
          "selected_mode", [](const plans::Session& session) {
            return static_cast<int64_t>(session.selected_mode());
          });
  module.def("structured_plan_spec", &PlanSpec,
             "Return the structured-plan language and executor ABI.");
  module.def(
      "structured_plan_observations_batch",
      [](py::list sessions, py::list engines, IntArray players, int workers) {
        return MakePlanObservations(
            ParsePlanOwners(sessions, engines, std::move(players), workers),
            workers);
      },
      py::arg("sessions"), py::arg("engines"), py::arg("players"),
      py::arg("workers"));
  module.def(
      "structured_plan_ready_observations_batch",
      [](py::list sessions, py::list engines, IntArray players, int workers) {
        return MakeReadyPlanObservations(
            ParsePlanOwners(sessions, engines, std::move(players), workers),
            workers);
      },
      py::arg("sessions"), py::arg("engines"), py::arg("players"),
      py::arg("workers"));
  module.def(
      "structured_plan_apply_batch",
      [](py::list sessions, py::list engines, IntArray players,
         IntArray modes, IntArray line_operations, IntArray line_values,
         IntArray global_operations, IntArray global_values, int workers) {
        ApplyPlanBatch(
            ParsePlanOwners(sessions, engines, std::move(players), workers),
            std::move(modes), std::move(line_operations),
            std::move(line_values), std::move(global_operations),
            std::move(global_values), workers);
      },
      py::arg("sessions"), py::arg("engines"), py::arg("players"),
      py::arg("modes"), py::arg("line_operations"),
      py::arg("line_values"), py::arg("global_operations"),
      py::arg("global_values"), py::arg("workers"));
  module.def(
      "structured_plan_actions_batch",
      [](py::list sessions, py::list engines, IntArray players, int workers) {
        return MakePlanActions(
            ParsePlanOwners(sessions, engines, std::move(players), workers),
            workers);
      },
      py::arg("sessions"), py::arg("engines"), py::arg("players"),
      py::arg("workers"));
  module.def(
      "structured_plan_decision_required_batch",
      [](py::list sessions, py::list engines, IntArray players, int workers) {
        return PlanDecisionRequired(
            ParsePlanOwners(sessions, engines, std::move(players), workers),
            workers);
      },
      py::arg("sessions"), py::arg("engines"), py::arg("players"),
      py::arg("workers"));
  module.def(
      "structured_plan_step_self_play_batch", &StepPlanSelfPlayBatch,
      py::arg("engines"), py::arg("candidate_players"),
      py::arg("candidate_sessions"), py::arg("opponent_sessions"),
      py::arg("workers"));
  module.def(
      "structured_plan_advance_self_play_batch", &AdvancePlanSelfPlayBatch,
      py::arg("engines"), py::arg("candidate_players"),
      py::arg("candidate_sessions"), py::arg("opponent_sessions"),
      py::arg("workers"));
  module.def(
      "structured_plan_step_boatlee_v21_batch",
      [](py::list engines, IntArray players, py::list plan_sessions,
         py::list opponent_sessions, int workers) {
        return StepPlanOpponentBatch<boatlee::Session>(
            engines, std::move(players), plan_sessions, opponent_sessions,
            workers);
      },
      py::arg("engines"), py::arg("candidate_players"),
      py::arg("candidate_sessions"), py::arg("opponent_sessions"),
      py::arg("workers"));
  module.def(
      "structured_plan_step_mugundh_v21_batch",
      [](py::list engines, IntArray players, py::list plan_sessions,
         py::list opponent_sessions, int workers) {
        return StepPlanOpponentBatch<mugundh::Session>(
            engines, std::move(players), plan_sessions, opponent_sessions,
            workers);
      },
      py::arg("engines"), py::arg("candidate_players"),
      py::arg("candidate_sessions"), py::arg("opponent_sessions"),
      py::arg("workers"));
  module.def(
      "structured_plan_step_kaito_v39_batch",
      [](py::list engines, IntArray players, py::list plan_sessions,
         py::list opponent_sessions, int workers) {
        return StepPlanOpponentBatch<kaito_v39::Session>(
            engines, std::move(players), plan_sessions, opponent_sessions,
            workers);
      },
      py::arg("engines"), py::arg("candidate_players"),
      py::arg("candidate_sessions"), py::arg("opponent_sessions"),
      py::arg("workers"));
  module.def(
      "structured_plan_step_kaito_v48_batch",
      [](py::list engines, IntArray players, py::list plan_sessions,
         py::list opponent_sessions, int workers) {
        return StepPlanOpponentBatch<kaito::Session>(
            engines, std::move(players), plan_sessions, opponent_sessions,
            workers);
      },
      py::arg("engines"), py::arg("candidate_players"),
      py::arg("candidate_sessions"), py::arg("opponent_sessions"),
      py::arg("workers"));
}
