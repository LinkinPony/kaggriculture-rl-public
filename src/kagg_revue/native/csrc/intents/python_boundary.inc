py::dict IntentObservationToPy(const intents::Observation& observation) {
  const int candidate_count = static_cast<int>(observation.candidates.size());
  const int cells = static_cast<int>(observation.ledger.size());
  py::array_t<int64_t> candidate_fields(
      {candidate_count, intents::kCandidateFieldCount});
  py::array_t<float> candidate_features(
      {candidate_count, intents::kCandidateFeatureCount});
  py::array_t<uint64_t> canonical_ids(candidate_count);
  for (int candidate = 0; candidate < candidate_count; ++candidate) {
    std::copy(observation.candidates[candidate].fields.begin(),
              observation.candidates[candidate].fields.end(),
              candidate_fields.mutable_data(candidate));
    std::copy(observation.candidates[candidate].features.begin(),
              observation.candidates[candidate].features.end(),
              candidate_features.mutable_data(candidate));
    canonical_ids.mutable_at(candidate) =
        observation.candidates[candidate].canonical_id;
  }
  py::array_t<int64_t> ledger({cells, intents::kLedgerFieldCount});
  py::array_t<int64_t> status({cells, intents::kStatusFieldCount});
  py::array_t<int64_t> work_priorities(
      {cells, static_cast<int>(intents::WorkKind::kStore)});
  py::array_t<int64_t> work_orders(
      {static_cast<int>(observation.work_orders.size()),
       intents::kWorkFieldCount});
  for (int target = 0; target < cells; ++target) {
    std::copy(observation.ledger[target].begin(),
              observation.ledger[target].end(), ledger.mutable_data(target));
    std::copy(observation.status[target].begin(),
              observation.status[target].end(), status.mutable_data(target));
    std::copy(observation.work_priorities[target].begin(),
              observation.work_priorities[target].end(),
              work_priorities.mutable_data(target));
  }
  for (int index = 0; index < static_cast<int>(observation.work_orders.size());
       ++index) {
    std::copy(observation.work_orders[index].begin(),
              observation.work_orders[index].end(),
              work_orders.mutable_data(index));
  }
  py::array_t<int64_t> positions({2, intents::kPositionFieldCount});
  for (int role = 0; role < 2; ++role) {
    std::copy(observation.positions[role].begin(),
              observation.positions[role].end(), positions.mutable_data(role));
  }
  py::array_t<int64_t> market_prefix(
      {static_cast<int>(observation.market_prefix.size()),
       intents::kMarketFieldCount});
  for (int order = 0;
       order < static_cast<int>(observation.market_prefix.size()); ++order) {
    std::copy(observation.market_prefix[order].begin(),
              observation.market_prefix[order].end(),
              market_prefix.mutable_data(order));
  }
  py::dict result;
  result["version"] = intents::kSpecVersion;
  result["phase"] = static_cast<int64_t>(observation.phase);
  result["phase_name"] = intents::PhaseName(observation.phase);
  result["candidate_fields"] = std::move(candidate_fields);
  result["candidate_features"] = std::move(candidate_features);
  result["canonical_id"] = std::move(canonical_ids);
  result["candidate_count"] = candidate_count;
  result["ledger"] = std::move(ledger);
  result["status"] = std::move(status);
  result["work_priorities"] = std::move(work_priorities);
  result["work_orders"] = std::move(work_orders);
  result["positions"] = std::move(positions);
  result["market_prefix"] = std::move(market_prefix);
  return result;
}

py::dict IntentSpec() {
  py::dict result;
  result["version"] = intents::kSpecVersion;
  result["abi_version"] = intents::kAbiVersion;
  result["candidate_field_count"] = intents::kCandidateFieldCount;
  result["candidate_feature_count"] = intents::kCandidateFeatureCount;
  result["ledger_field_count"] = intents::kLedgerFieldCount;
  result["status_field_count"] = intents::kStatusFieldCount;
  result["work_field_count"] = intents::kWorkFieldCount;
  result["candidate_fields"] = py::make_tuple(
      "choice_kind", "target", "item", "maintenance", "product_collection",
      "fertilizer_collection", "priority", "exact_quantity", "unit",
      "directive_operation");
  py::list feature_names;
  for (const std::string& name : intents::CandidateFeatureNames()) {
    feature_names.append(name);
  }
  result["candidate_features"] = std::move(feature_names);
  result["ledger_fields"] = py::make_tuple(
      "active", "asset_kind", "item", "maintenance", "product_collection",
      "fertilizer_collection", "priority", "bound");
  result["status_fields"] = py::make_tuple(
      "status", "block_reason", "shortfall_item", "day_deadline_slack");
  result["work_fields"] = py::make_tuple(
      "work_kind", "target", "item", "remaining_quantity", "priority",
      "status", "block_reason", "episode_deadline_slack", "unit");
  result["position_fields"] =
      py::make_tuple("active", "target", "priority", "role");
  result["market_fields"] =
      py::make_tuple("order_kind", "item", "exact_quantity");
  py::dict asset_kinds;
  asset_kinds["NONE"] = static_cast<int>(intents::AssetKind::kNone);
  asset_kinds["CROP"] = static_cast<int>(intents::AssetKind::kCrop);
  asset_kinds["ANIMAL"] = static_cast<int>(intents::AssetKind::kAnimal);
  result["asset_kinds"] = std::move(asset_kinds);
  py::dict maintenance;
  maintenance["NONE"] = static_cast<int>(intents::Maintenance::kNone);
  maintenance["SURVIVE"] = static_cast<int>(intents::Maintenance::kSurvive);
  maintenance["YIELD"] = static_cast<int>(intents::Maintenance::kYield);
  maintenance["CARED"] = static_cast<int>(intents::Maintenance::kCared);
  result["maintenance"] = std::move(maintenance);
  py::dict product_collection;
  product_collection["MANUAL"] =
      static_cast<int>(intents::ProductCollection::kManual);
  product_collection["BEFORE_CAP"] =
      static_cast<int>(intents::ProductCollection::kBeforeCap);
  result["product_collection"] = std::move(product_collection);
  py::dict fertilizer_collection;
  fertilizer_collection["MANUAL"] =
      static_cast<int>(intents::FertilizerCollection::kManual);
  fertilizer_collection["DAILY"] =
      static_cast<int>(intents::FertilizerCollection::kDaily);
  result["fertilizer_collection"] = std::move(fertilizer_collection);
  py::dict priorities;
  priorities["LOW"] = static_cast<int>(intents::Priority::kLow);
  priorities["NORMAL"] = static_cast<int>(intents::Priority::kNormal);
  priorities["HIGH"] = static_cast<int>(intents::Priority::kHigh);
  result["priorities"] = std::move(priorities);
  py::dict position_roles;
  position_roles["FARMER"] =
      static_cast<int>(intents::PositionRole::kFarmer);
  position_roles["ANY_HAND"] =
      static_cast<int>(intents::PositionRole::kAnyHand);
  result["position_roles"] = std::move(position_roles);
  py::dict directive_operations;
  directive_operations["NONE"] = 0;
  directive_operations["POSITION"] =
      static_cast<int>(intents::DirectiveOperation::kPosition);
  directive_operations["WAIT"] =
      static_cast<int>(intents::DirectiveOperation::kWait);
  directive_operations["PICKUP"] =
      static_cast<int>(intents::DirectiveOperation::kPickup);
  directive_operations["DROP"] =
      static_cast<int>(intents::DirectiveOperation::kDrop);
  directive_operations["PLACE"] =
      static_cast<int>(intents::DirectiveOperation::kPlace);
  directive_operations["PLANT"] =
      static_cast<int>(intents::DirectiveOperation::kPlant);
  directive_operations["WATER"] =
      static_cast<int>(intents::DirectiveOperation::kWater);
  directive_operations["HARVEST"] =
      static_cast<int>(intents::DirectiveOperation::kHarvest);
  directive_operations["FERTILIZE"] =
      static_cast<int>(intents::DirectiveOperation::kFertilize);
  directive_operations["DIG"] =
      static_cast<int>(intents::DirectiveOperation::kDig);
  directive_operations["BUILD_COOP"] =
      static_cast<int>(intents::DirectiveOperation::kBuildCoop);
  directive_operations["BUILD_PASTURE"] =
      static_cast<int>(intents::DirectiveOperation::kBuildPasture);
  directive_operations["FEED"] =
      static_cast<int>(intents::DirectiveOperation::kFeed);
  directive_operations["COLLECT_FERTILIZER"] =
      static_cast<int>(intents::DirectiveOperation::kCollectFertilizer);
  directive_operations["CARE"] =
      static_cast<int>(intents::DirectiveOperation::kCare);
  result["directive_operations"] = std::move(directive_operations);
  py::dict market_order_kinds;
  market_order_kinds["BUY_SEED"] = static_cast<int>(OrderKind::kBuySeed);
  market_order_kinds["BUY_PRODUCT"] =
      static_cast<int>(OrderKind::kBuyProduct);
  market_order_kinds["BUY_ANIMAL"] =
      static_cast<int>(OrderKind::kBuyAnimal);
  market_order_kinds["SELL"] = static_cast<int>(OrderKind::kSell);
  market_order_kinds["HIRE"] = static_cast<int>(OrderKind::kHire);
  market_order_kinds["BUY_LAND"] = static_cast<int>(OrderKind::kBuyLand);
  market_order_kinds["SKIP_SLOT"] = intents::kMarketSkipKind;
  result["market_order_kinds"] = std::move(market_order_kinds);
  py::dict phases;
  for (int phase = 0; phase <= static_cast<int>(intents::Phase::kDone);
       ++phase) {
    phases[intents::PhaseName(static_cast<intents::Phase>(phase))] = phase;
  }
  result["phases"] = std::move(phases);
  py::dict choices;
  for (int choice = 0;
       choice <= static_cast<int>(intents::ChoiceKind::kMarketSkipSlot);
       ++choice) {
    choices[intents::ChoiceKindName(static_cast<intents::ChoiceKind>(choice))] =
        choice;
  }
  result["choice_kinds"] = std::move(choices);
  py::dict work;
  for (int kind = 0;
       kind <= static_cast<int>(intents::WorkKind::kDirectiveCare);
       ++kind) {
    work[intents::WorkKindName(static_cast<intents::WorkKind>(kind))] = kind;
  }
  result["work_kinds"] = std::move(work);
  py::dict statuses;
  for (int status = 0; status <= static_cast<int>(intents::Status::kFailed);
       ++status) {
    statuses[intents::StatusName(static_cast<intents::Status>(status))] = status;
  }
  result["statuses"] = std::move(statuses);
  py::dict reasons;
  for (int reason = 0;
       reason <= static_cast<int>(intents::BlockReason::kShedItemShortfall);
       ++reason) {
    reasons[intents::BlockReasonName(
        static_cast<intents::BlockReason>(reason))] = reason;
  }
  result["block_reasons"] = std::move(reasons);
  return result;
}

struct IntentOwners {
  std::vector<intents::Session*> sessions;
  std::vector<const Engine*> engines;
  std::vector<int> players;
};

IntentOwners ParseIntentOwners(py::list session_owners, py::list engine_owners,
                               IntArray players, int workers) {
  const int batch = static_cast<int>(py::len(session_owners));
  if (batch < 1 || py::len(engine_owners) !=
                       static_cast<py::size_t>(batch)) {
    throw py::value_error("intent batch inputs must be nonempty and aligned");
  }
  if (workers < 1 || workers > 256) {
    throw py::value_error("intent batch workers must be in [1, 256]");
  }
  const py::buffer_info player_info = players.request();
  if (player_info.ndim != 1 || player_info.shape[0] != batch) {
    throw py::value_error("intent batch players must have shape [B]");
  }
  const auto* player_data = static_cast<const int64_t*>(player_info.ptr);
  IntentOwners result;
  result.sessions.reserve(batch);
  result.engines.reserve(batch);
  result.players.reserve(batch);
  for (int index = 0; index < batch; ++index) {
    const int player = static_cast<int>(player_data[index]);
    if (player < 0 || player > 1) {
      throw py::value_error("intent player must be 0 or 1");
    }
    auto* session = &py::cast<intents::Session&>(session_owners[index]);
    if (std::find(result.sessions.begin(), result.sessions.end(), session) !=
        result.sessions.end()) {
      throw py::value_error("intent batch requires distinct sessions");
    }
    result.sessions.push_back(session);
    result.engines.push_back(
        &py::cast<const PyEngine&>(engine_owners[index]).raw_engine());
    result.players.push_back(player);
  }
  return result;
}

std::vector<intents::Observation> IntentObservationValues(
    const IntentOwners& owners, int workers) {
  const int batch = static_cast<int>(owners.sessions.size());
  std::vector<intents::Observation> observations(batch);
  std::exception_ptr first_error;
  std::mutex error_mutex;
  {
    py::gil_scoped_release release;
#ifdef _OPENMP
#pragma omp parallel for schedule(static) num_threads(workers)
#endif
    for (int index = 0; index < batch; ++index) {
      try {
        observations[index] = owners.sessions[index]->Observe(
            *owners.engines[index], owners.players[index]);
      } catch (...) {
        std::lock_guard<std::mutex> lock(error_mutex);
        if (!first_error) first_error = std::current_exception();
      }
    }
  }
  if (first_error) std::rethrow_exception(first_error);
  return observations;
}

template <typename Integer>
py::dict IntentObservationPointersToPy(
    const std::vector<const intents::Observation*>& observations,
    const std::vector<uint8_t>& force_commit, bool include_canonical_ids,
    int workers) {
  const int batch = static_cast<int>(observations.size());
  if (batch < 1 ||
      (!force_commit.empty() &&
       static_cast<int>(force_commit.size()) != batch)) {
    throw py::value_error("intent forced-commit rows do not align");
  }
  int max_candidates = 0;
  int max_market = 0;
  int max_work = 0;
  for (const intents::Observation* raw_observation : observations) {
    const intents::Observation& observation = *raw_observation;
    max_candidates = std::max(
        max_candidates, static_cast<int>(observation.candidates.size()));
    max_market = std::max(
        max_market, static_cast<int>(observation.market_prefix.size()));
    max_work =
        std::max(max_work, static_cast<int>(observation.work_orders.size()));
  }
  const int cells = static_cast<int>(observations[0]->ledger.size());
  for (const intents::Observation* raw_observation : observations) {
    const intents::Observation& observation = *raw_observation;
    if (static_cast<int>(observation.ledger.size()) != cells) {
      throw py::value_error(
          "intent observation batch requires one board shape");
    }
  }
  py::array_t<Integer> fields(
      {batch, max_candidates, intents::kCandidateFieldCount});
  py::array_t<float> features(
      {batch, max_candidates, intents::kCandidateFeatureCount});
  py::array_t<uint64_t> ids;
  if (include_canonical_ids) {
    ids = py::array_t<uint64_t>({batch, max_candidates});
  }
  py::array_t<bool> mask({batch, max_candidates});
  py::array_t<Integer> counts(batch);
  py::array_t<Integer> phases(batch);
  py::array_t<Integer> ledger(
      {batch, cells, intents::kLedgerFieldCount});
  py::array_t<Integer> status(
      {batch, cells, intents::kStatusFieldCount});
  py::array_t<Integer> work(
      {batch, cells, static_cast<int>(intents::WorkKind::kStore)});
  py::array_t<Integer> work_orders(
      {batch, max_work, intents::kWorkFieldCount});
  py::array_t<bool> work_mask({batch, max_work});
  py::array_t<Integer> work_counts(batch);
  py::array_t<Integer> positions(
      {batch, 2, intents::kPositionFieldCount});
  py::array_t<Integer> market(
      {batch, max_market, intents::kMarketFieldCount});
  py::array_t<Integer> market_counts(batch);
  const int worker_count = std::max(1, std::min(workers, batch));
  {
    py::gil_scoped_release release;
#ifdef _OPENMP
#pragma omp parallel for schedule(static) num_threads(worker_count)
#endif
    for (int index = 0; index < batch; ++index) {
      const intents::Observation& observation = *observations[index];
      std::fill_n(fields.mutable_data(index),
                  max_candidates * intents::kCandidateFieldCount,
                  Integer{0});
      std::fill_n(features.mutable_data(index),
                  max_candidates * intents::kCandidateFeatureCount, 0.0F);
      std::fill_n(mask.mutable_data(index), max_candidates, false);
      if (include_canonical_ids) {
        std::fill_n(ids.mutable_data(index), max_candidates, uint64_t{0});
      }
      if (max_work > 0) {
        std::fill_n(work_orders.mutable_data(index),
                    max_work * intents::kWorkFieldCount, Integer{0});
        std::fill_n(work_mask.mutable_data(index), max_work, false);
      }
      if (max_market > 0) {
        std::fill_n(market.mutable_data(index),
                    max_market * intents::kMarketFieldCount, Integer{0});
      }
      const int commit_count = static_cast<int>(std::count_if(
          observation.candidates.begin(), observation.candidates.end(),
          [](const intents::Candidate& candidate) {
            return candidate.kind == intents::ChoiceKind::kCommit;
          }));
      const bool force = !force_commit.empty() && force_commit[index] != 0 &&
                         commit_count == 1;
      counts.mutable_at(index) = observation.candidates.size();
      phases.mutable_at(index) = static_cast<int64_t>(observation.phase);
      market_counts.mutable_at(index) = observation.market_prefix.size();
      work_counts.mutable_at(index) = observation.work_orders.size();
      for (int candidate = 0;
           candidate < static_cast<int>(observation.candidates.size());
           ++candidate) {
        std::copy(observation.candidates[candidate].fields.begin(),
                  observation.candidates[candidate].fields.end(),
                  fields.mutable_data(index, candidate));
        std::copy(observation.candidates[candidate].features.begin(),
                  observation.candidates[candidate].features.end(),
                  features.mutable_data(index, candidate));
        if (include_canonical_ids) {
          ids.mutable_at(index, candidate) =
              observation.candidates[candidate].canonical_id;
        }
        mask.mutable_at(index, candidate) =
            !force || observation.candidates[candidate].kind ==
                          intents::ChoiceKind::kCommit;
      }
      for (int order = 0;
           order < static_cast<int>(observation.work_orders.size()); ++order) {
        std::copy(observation.work_orders[order].begin(),
                  observation.work_orders[order].end(),
                  work_orders.mutable_data(index, order));
        work_mask.mutable_at(index, order) = 1;
      }
      for (int target = 0; target < cells; ++target) {
        std::copy(observation.ledger[target].begin(),
                  observation.ledger[target].end(),
                  ledger.mutable_data(index, target));
        std::copy(observation.status[target].begin(),
                  observation.status[target].end(),
                  status.mutable_data(index, target));
        std::copy(observation.work_priorities[target].begin(),
                  observation.work_priorities[target].end(),
                  work.mutable_data(index, target));
      }
      for (int role = 0; role < 2; ++role) {
        std::copy(observation.positions[role].begin(),
                  observation.positions[role].end(),
                  positions.mutable_data(index, role));
      }
      for (int order = 0;
           order < static_cast<int>(observation.market_prefix.size());
           ++order) {
        std::copy(observation.market_prefix[order].begin(),
                  observation.market_prefix[order].end(),
                  market.mutable_data(index, order));
      }
    }
  }
  py::dict result;
  result["candidate_fields"] = std::move(fields);
  result["candidate_features"] = std::move(features);
  if (include_canonical_ids) {
    result["canonical_id"] = std::move(ids);
  }
  result["candidate_mask"] = std::move(mask);
  result["candidate_counts"] = std::move(counts);
  result["phase"] = std::move(phases);
  result["ledger"] = std::move(ledger);
  result["status"] = std::move(status);
  result["work_priorities"] = std::move(work);
  result["work_orders"] = std::move(work_orders);
  result["work_mask"] = std::move(work_mask);
  result["work_counts"] = std::move(work_counts);
  result["positions"] = std::move(positions);
  result["market_prefix"] = std::move(market);
  result["market_counts"] = std::move(market_counts);
  return result;
}

py::dict IntentObservationsToPy(
    const std::vector<intents::Observation>& observations,
    const std::vector<uint8_t>& force_commit, int workers) {
  std::vector<const intents::Observation*> pointers;
  pointers.reserve(observations.size());
  for (const intents::Observation& observation : observations) {
    pointers.push_back(&observation);
  }
  return IntentObservationPointersToPy<int64_t>(pointers, force_commit, true,
                                                workers);
}

py::dict IntentObservations(const IntentOwners& owners, int workers,
                            const std::vector<uint8_t>& force_commit) {
  return IntentObservationsToPy(
      IntentObservationValues(owners, workers), force_commit, workers);
}

py::dict IntentObservationsBatch(py::list session_owners,
                                 py::list engine_owners, IntArray players,
                                 int workers) {
  const IntentOwners owners = ParseIntentOwners(
      session_owners, engine_owners, std::move(players), workers);
  return IntentObservations(owners, workers, {});
}

py::array_t<int64_t> IntentSelectBatch(py::list session_owners,
                                       IntArray candidate_indices,
                                       IntArray active, int workers) {
  const int batch = static_cast<int>(py::len(session_owners));
  if (batch < 1 || workers < 1 || workers > 256) {
    throw py::value_error("intent select batch or worker count is invalid");
  }
  const py::buffer_info index_info = candidate_indices.request();
  const py::buffer_info active_info = active.request();
  if (index_info.ndim != 1 || index_info.shape[0] != batch ||
      active_info.ndim != 1 || active_info.shape[0] != batch) {
    throw py::value_error("intent indices and active must have shape [B]");
  }
  std::vector<intents::Session*> sessions;
  sessions.reserve(batch);
  for (py::handle owner : session_owners) {
    auto* session = &py::cast<intents::Session&>(owner);
    if (std::find(sessions.begin(), sessions.end(), session) !=
        sessions.end()) {
      throw py::value_error("intent select batch requires distinct sessions");
    }
    sessions.push_back(session);
  }
  const auto* indices = static_cast<const int64_t*>(index_info.ptr);
  const auto* active_data = static_cast<const int64_t*>(active_info.ptr);
  py::array_t<int64_t> phases(batch);
  auto* phase_data = phases.mutable_data();
  std::exception_ptr first_error;
  std::mutex error_mutex;
  {
    py::gil_scoped_release release;
#ifdef _OPENMP
#pragma omp parallel for schedule(static) num_threads(workers)
#endif
    for (int index = 0; index < batch; ++index) {
      try {
        phase_data[index] = active_data[index]
                                ? static_cast<int64_t>(
                                      sessions[index]->Select(indices[index]))
                                : static_cast<int64_t>(sessions[index]->phase());
      } catch (...) {
        std::lock_guard<std::mutex> lock(error_mutex);
        if (!first_error) first_error = std::current_exception();
      }
    }
  }
  if (first_error) std::rethrow_exception(first_error);
  return phases;
}

py::dict IntentActionsBatch(py::list session_owners, py::list engine_owners,
                            IntArray players, int workers) {
  const IntentOwners owners = ParseIntentOwners(
      session_owners, engine_owners, std::move(players), workers);
  const int batch = static_cast<int>(owners.sessions.size());
  std::vector<intents::NumericAction> actions(batch);
  std::exception_ptr first_error;
  std::mutex error_mutex;
  {
    py::gil_scoped_release release;
#ifdef _OPENMP
#pragma omp parallel for schedule(static) num_threads(workers)
#endif
    for (int index = 0; index < batch; ++index) {
      try {
        actions[index] = owners.sessions[index]->ActionNumeric(
            *owners.engines[index], owners.players[index]);
      } catch (...) {
        std::lock_guard<std::mutex> lock(error_mutex);
        if (!first_error) first_error = std::current_exception();
      }
    }
  }
  if (first_error) std::rethrow_exception(first_error);
  int width = 0;
  for (const intents::NumericAction& action : actions) {
    width = std::max(width, static_cast<int>(action.tokens.size()));
  }
  py::array_t<int64_t> tokens({batch, width});
  py::array_t<int64_t> quantities({batch, width});
  py::array_t<int64_t> decision_counts(batch);
  py::array_t<int64_t> unit_counts(batch);
  std::fill_n(tokens.mutable_data(), tokens.size(), int64_t{0});
  std::fill_n(quantities.mutable_data(), quantities.size(), int64_t{0});
  for (int index = 0; index < batch; ++index) {
    std::copy(actions[index].tokens.begin(), actions[index].tokens.end(),
              tokens.mutable_data(index));
    std::copy(actions[index].quantities.begin(), actions[index].quantities.end(),
              quantities.mutable_data(index));
    decision_counts.mutable_at(index) = actions[index].decision_count;
    unit_counts.mutable_at(index) = actions[index].unit_count;
  }
  py::dict result;
  result["tokens"] = std::move(tokens);
  result["quantities"] = std::move(quantities);
  result["decision_counts"] = std::move(decision_counts);
  result["unit_counts"] = std::move(unit_counts);
  return result;
}

std::vector<int> IntentActiveRows(IntArray active, int batch) {
  const py::buffer_info info = active.request();
  if (info.ndim != 1 || info.shape[0] < 1 || info.shape[0] > batch) {
    throw py::value_error("intent active rows must be a nonempty batch subset");
  }
  const auto* data = static_cast<const int64_t*>(info.ptr);
  std::vector<uint8_t> seen(batch, 0);
  std::vector<int> rows;
  rows.reserve(info.shape[0]);
  for (py::ssize_t index = 0; index < info.shape[0]; ++index) {
    const int row = static_cast<int>(data[index]);
    if (row < 0 || row >= batch || seen[row]) {
      throw py::value_error("intent active row is invalid or duplicated");
    }
    seen[row] = 1;
    rows.push_back(row);
  }
  return rows;
}

IntentOwners IntentOwnerSubset(const IntentOwners& owners,
                               const std::vector<int>& rows) {
  IntentOwners subset;
  subset.sessions.reserve(rows.size());
  subset.engines.reserve(rows.size());
  subset.players.reserve(rows.size());
  for (const int row : rows) {
    subset.sessions.push_back(owners.sessions[row]);
    subset.engines.push_back(owners.engines[row]);
    subset.players.push_back(owners.players[row]);
  }
  return subset;
}

#include "intents/batch_binding.inc"

void BindIntentLedgers(py::module_& module) {
  py::class_<intents::Session>(module, "IntentLedgerSession")
      .def(py::init([](py::object configuration) {
             return std::make_unique<intents::Session>(
                 pyconv::ParseConfig(configuration));
           }),
           py::arg("configuration") = py::none())
      .def(
          "observe",
          [](intents::Session& session, const PyEngine& owner, int player) {
            intents::Observation observation;
            {
              py::gil_scoped_release release;
              observation = session.Observe(owner.raw_engine(), player);
            }
            return IntentObservationToPy(observation);
          },
          py::arg("engine"), py::arg("player"))
      .def(
          "select",
          [](intents::Session& session, int candidate_index) {
            return static_cast<int64_t>(session.Select(candidate_index));
          },
          py::arg("candidate_index"))
      .def(
          "action",
          [](intents::Session& session, const PyEngine& owner, int player) {
            PlayerAction action;
            {
              py::gil_scoped_release release;
              action = session.Action(owner.raw_engine(), player);
            }
            return pyconv::PlayerActionToPy(action);
          },
          py::arg("engine"), py::arg("player"))
      .def(
          "action_numeric",
          [](intents::Session& session, const PyEngine& owner, int player) {
            intents::NumericAction action;
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
          },
          py::arg("engine"), py::arg("player"))
      .def(
          "decision_required",
          [](intents::Session& session, const PyEngine& owner, int player) {
            return session.DecisionRequired(owner.raw_engine(), player);
          },
          py::arg("engine"), py::arg("player"))
      .def("reset", &intents::Session::Reset)
      .def_property_readonly("phase", [](const intents::Session& session) {
        return static_cast<int64_t>(session.phase());
      })
      .def_property_readonly("candidate_count",
                             &intents::Session::candidate_count)
      .def_property_readonly("step", &intents::Session::step);
  py::class_<IntentLedgerBatch>(module, "IntentLedgerBatch")
      .def(py::init<py::list, py::list, IntArray, int>(),
           py::arg("sessions"), py::arg("engines"), py::arg("players"),
           py::arg("workers"))
      .def("observe", &IntentLedgerBatch::Observe, py::arg("active"),
           py::arg("maximum_steps"))
      .def("observe_compact", &IntentLedgerBatch::ObserveCompact,
           py::arg("active"), py::arg("maximum_steps"))
      .def("device_auxiliary", &IntentLedgerBatch::DeviceAuxiliary)
      .def("write_prepared", &IntentLedgerBatch::WritePrepared,
           py::arg("candidate_fields"), py::arg("candidate_features"),
           py::arg("candidate_mask"), py::arg("ledger"), py::arg("status"),
           py::arg("work_priorities"), py::arg("work_orders"),
           py::arg("work_mask"), py::arg("positions"),
           py::arg("market_prefix"), py::arg("market_mask"),
           py::arg("phase"), py::arg("model_rows"))
      .def("record_prepared", &IntentLedgerBatch::RecordPrepared,
           py::arg("selected"), py::arg("log_probability"),
           py::arg("value"), py::arg("turn_index"))
      .def("record_prepared_indexed", &IntentLedgerBatch::RecordPreparedIndexed,
           py::arg("selected"), py::arg("behavior_offset"),
           py::arg("turn_index"))
      .def("replay_transaction", &IntentLedgerBatch::ReplayTransaction,
           py::arg("selected"), py::arg("selected_fields"), py::arg("counts"),
           py::arg("behavior_offset"), py::arg("turn_index"),
           py::arg("maximum_steps"))
      .def("apply_teacher_plans", &IntentLedgerBatch::ApplyTeacherPlans,
           py::arg("directive_operations"), py::arg("directive_targets"),
           py::arg("directive_items"), py::arg("directive_quantities"),
           py::arg("directive_counts"), py::arg("market_choices"),
           py::arg("market_items"), py::arg("market_quantities"),
           py::arg("market_counts"), py::arg("turn_index"),
           py::arg("maximum_steps"))
      .def("export_rollout", &IntentLedgerBatch::ExportRollout)
      .def("export_rollout_buckets", &IntentLedgerBatch::ExportRolloutBuckets)
      .def("select", &IntentLedgerBatch::Select, py::arg("active"),
           py::arg("candidate_indices"))
      .def("reset_transaction", &IntentLedgerBatch::ResetTransaction)
      .def_property_readonly("batch_size", &IntentLedgerBatch::batch_size);
  module.def("intent_ledger_spec", &IntentSpec);
  module.def("intent_ledger_observations_batch", &IntentObservationsBatch,
             py::arg("sessions"), py::arg("engines"), py::arg("players"),
             py::arg("workers"));
  module.def("intent_ledger_select_batch", &IntentSelectBatch,
             py::arg("sessions"), py::arg("candidate_indices"),
             py::arg("active"), py::arg("workers"));
  module.def("intent_ledger_actions_batch", &IntentActionsBatch,
             py::arg("sessions"), py::arg("engines"), py::arg("players"),
             py::arg("workers"));
}
