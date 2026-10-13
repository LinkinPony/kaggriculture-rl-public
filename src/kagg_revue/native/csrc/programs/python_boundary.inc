// Included by bindings.cpp inside its private kagg namespace.

py::dict ConditionalProgramSpec(const programs::Session& session) {
  const int64_t maximum_exact_quantity = std::max<int64_t>(
      session.config().shed_capacity, kMaxMarketUnitsPerSlot);
  int exact_quantity_bits = 0;
  for (int64_t value = maximum_exact_quantity; value > 0; value >>= 1) {
    ++exact_quantity_bits;
  }
  py::dict out;
  out["version"] = programs::kAbiVersion;
  out["control_count"] = programs::kControlCount;
  out["direction_count"] = programs::kDirectionCount;
  out["task_count"] = programs::kTaskCount;
  out["raw_operation_count"] = programs::kRawOperationCount;
  out["market_order_count"] = programs::kMarketOrderCount;
  out["quantity_mode_count"] = programs::kQuantityModeCount;
  out["argument_count"] = programs::kArgumentCount;
  out["item_count"] = kNumItems;
  out["board_size"] = session.config().board_size;
  out["unit_limit"] = session.unit_limit();
  out["maximum_market_orders"] = session.config().max_market_orders;
  out["maximum_decisions"] = session.maximum_decisions();
  out["root_feature_count"] = programs::kRootFeatureCount;
  out["option_feature_count"] = programs::kOptionFeatureCount;
  out["maximum_exact_quantity"] = maximum_exact_quantity;
  out["exact_quantity_bits"] = exact_quantity_bits;
  py::list root_features;
  for (const char* name : programs::RootFeatureNames()) {
    root_features.append(name);
  }
  out["root_features"] = std::move(root_features);
  py::list option_features;
  for (const char* name : programs::OptionFeatureNames()) {
    option_features.append(name);
  }
  out["option_features"] = std::move(option_features);
  out["compiler"] = "native-conditional-shadow-v1";
  out["unit_order"] = "farmer-then-hands";
  out["market_projection"] = "own-orders-no-opponent-future";
  out["exact_quantity"] = "dynamic-bounded-integer";
  return out;
}

py::dict ConditionalProgramDecisionToPy(const programs::Decision& decision,
                                        const programs::Session& session) {
  const int tiles = session.config().board_size * session.config().board_size;
  py::array_t<uint8_t> control(programs::kControlCount);
  py::array_t<uint8_t> direction(programs::kDirectionCount);
  py::array_t<uint8_t> task(programs::kTaskCount);
  py::array_t<uint8_t> task_argument(
      {programs::kTaskCount, programs::kArgumentCount});
  py::array_t<uint8_t> task_target(
      {programs::kTaskCount, programs::kArgumentCount, tiles});
  py::array_t<uint8_t> task_quantity_mode(
      {programs::kTaskCount, programs::kArgumentCount,
       programs::kQuantityModeCount});
  py::array_t<int64_t> task_quantity_max(
      {programs::kTaskCount, programs::kArgumentCount});
  py::array_t<uint8_t> raw_operation(programs::kRawOperationCount);
  py::array_t<uint8_t> raw_argument(
      {programs::kRawOperationCount, programs::kArgumentCount});
  py::array_t<uint8_t> raw_quantity_mode(
      {programs::kRawOperationCount, programs::kArgumentCount,
       programs::kQuantityModeCount});
  py::array_t<int64_t> raw_quantity_max(
      {programs::kRawOperationCount, programs::kArgumentCount});
  py::array_t<uint8_t> market_order(programs::kMarketOrderCount);
  py::array_t<uint8_t> market_item(
      {programs::kMarketOrderCount, kNumItems});
  py::array_t<uint8_t> market_quantity_mode(
      {programs::kMarketOrderCount, kNumItems,
       programs::kQuantityModeCount});
  py::array_t<int64_t> market_quantity_max(
      {programs::kMarketOrderCount, kNumItems});
  py::array_t<int16_t> target_reservations(tiles);
  py::array_t<float> root_features(programs::kRootFeatureCount);
  py::array_t<int64_t> option_features(programs::kOptionFeatureCount);
  std::copy(decision.control_mask.begin(), decision.control_mask.end(),
            control.mutable_data());
  std::copy(decision.direction_mask.begin(), decision.direction_mask.end(),
            direction.mutable_data());
  std::copy(decision.task_mask.begin(), decision.task_mask.end(),
            task.mutable_data());
  std::copy(decision.task_argument_mask.begin(),
            decision.task_argument_mask.end(), task_argument.mutable_data());
  std::copy(decision.task_target_mask.begin(),
            decision.task_target_mask.end(), task_target.mutable_data());
  std::copy(decision.task_quantity_mode_mask.begin(),
            decision.task_quantity_mode_mask.end(),
            task_quantity_mode.mutable_data());
  std::copy(decision.task_quantity_max.begin(),
            decision.task_quantity_max.end(), task_quantity_max.mutable_data());
  std::copy(decision.raw_operation_mask.begin(),
            decision.raw_operation_mask.end(), raw_operation.mutable_data());
  std::copy(decision.raw_argument_mask.begin(),
            decision.raw_argument_mask.end(), raw_argument.mutable_data());
  std::copy(decision.raw_quantity_mode_mask.begin(),
            decision.raw_quantity_mode_mask.end(),
            raw_quantity_mode.mutable_data());
  std::copy(decision.raw_quantity_max.begin(),
            decision.raw_quantity_max.end(), raw_quantity_max.mutable_data());
  std::copy(decision.market_order_mask.begin(),
            decision.market_order_mask.end(), market_order.mutable_data());
  std::copy(decision.market_item_mask.begin(),
            decision.market_item_mask.end(), market_item.mutable_data());
  std::copy(decision.market_quantity_mode_mask.begin(),
            decision.market_quantity_mode_mask.end(),
            market_quantity_mode.mutable_data());
  std::copy(decision.market_quantity_max.begin(),
            decision.market_quantity_max.end(),
            market_quantity_max.mutable_data());
  std::copy(decision.target_reservations.begin(),
            decision.target_reservations.end(),
            target_reservations.mutable_data());
  std::copy(decision.root_features.begin(), decision.root_features.end(),
            root_features.mutable_data());
  std::copy(decision.option_features.begin(), decision.option_features.end(),
            option_features.mutable_data());
  py::dict out;
  out["version"] = programs::kAbiVersion;
  out["phase"] = static_cast<int64_t>(decision.phase);
  out["unit_index"] = decision.unit_index;
  out["market_slot"] = decision.market_slot;
  out["unit_count"] = decision.unit_count;
  out["current_x"] = decision.current_x;
  out["current_y"] = decision.current_y;
  out["forced"] = decision.forced;
  out["control_mask"] = std::move(control);
  out["direction_mask"] = std::move(direction);
  out["task_mask"] = std::move(task);
  out["task_argument_mask"] = std::move(task_argument);
  out["task_target_mask"] = std::move(task_target);
  out["task_quantity_mode_mask"] = std::move(task_quantity_mode);
  out["task_quantity_max"] = std::move(task_quantity_max);
  out["raw_operation_mask"] = std::move(raw_operation);
  out["raw_argument_mask"] = std::move(raw_argument);
  out["raw_quantity_mode_mask"] = std::move(raw_quantity_mode);
  out["raw_quantity_max"] = std::move(raw_quantity_max);
  out["market_order_mask"] = std::move(market_order);
  out["market_item_mask"] = std::move(market_item);
  out["market_quantity_mode_mask"] = std::move(market_quantity_mode);
  out["market_quantity_max"] = std::move(market_quantity_max);
  out["target_reservations"] = std::move(target_reservations);
  out["root_features"] = std::move(root_features);
  out["option_features"] = std::move(option_features);
  return out;
}

py::dict ConditionalProgramActionToPy(const programs::NumericAction& action) {
  py::array_t<int64_t> tokens(action.tokens.size());
  py::array_t<int64_t> quantities(action.quantities.size());
  std::copy(action.tokens.begin(), action.tokens.end(), tokens.mutable_data());
  std::copy(action.quantities.begin(), action.quantities.end(),
            quantities.mutable_data());
  py::dict out;
  out["tokens"] = std::move(tokens);
  out["quantities"] = std::move(quantities);
  out["decision_count"] = action.decision_count;
  out["unit_count"] = action.unit_count;
  out["requires_decision"] = action.requires_decision;
  out["action"] = pyconv::PlayerActionToPy(action.action);
  return out;
}

programs::Selection ParseConditionalProgramSelection(
    int64_t control, int64_t task, int64_t target, int64_t argument,
    int64_t direction, int64_t raw_operation, int64_t quantity_mode,
    int64_t exact_quantity) {
  return programs::Selection{control, task, target, argument, direction,
                             raw_operation, quantity_mode, exact_quantity};
}

programs::VisibleState ParseConditionalProgramVisibleState(
    const programs::Session& session, const py::dict& observation) {
  programs::VisibleState state;
  state.player = py::cast<int>(observation["player"]);
  state.step = py::cast<int>(observation["step"]);
  if (state.player < 0 || state.player > 1 || state.step < 0) {
    throw py::value_error("conditional program observation identity is invalid");
  }
  const auto farms = py::reinterpret_borrow<py::list>(observation["farms"]);
  if (farms.size() != 2) {
    throw py::value_error("conditional program observation needs two farms");
  }
  state.farm = pyconv::ParseFarm(
      py::reinterpret_borrow<py::dict>(farms[state.player]),
      session.config().board_size);
  state.priv = pyconv::ParsePrivate(
      py::reinterpret_borrow<py::dict>(observation["private"]));
  const auto market =
      py::reinterpret_borrow<py::dict>(observation["market"]);
  const auto inventory =
      py::reinterpret_borrow<py::dict>(market["inventory"]);
  const auto prices = py::reinterpret_borrow<py::dict>(market["prices"]);
  for (int product = 0; product < kNumProducts; ++product) {
    state.market.inventory[product] =
        py::cast<int64_t>(inventory[kItemNames[product]]);
    state.market.prices[product] =
        py::cast<int64_t>(prices[kItemNames[product]]);
  }
  return state;
}

struct ConditionalProgramOwners {
  std::vector<programs::Session*> sessions;
  std::vector<const Engine*> engines;
  std::vector<int> players;
};

bool ConditionalProgramConfigsMatch(const Config& left, const Config& right) {
  if (left.episode_steps != right.episode_steps ||
      left.board_size != right.board_size ||
      left.starting_money != right.starting_money ||
      left.max_market_orders != right.max_market_orders ||
      left.turns_per_day != right.turns_per_day ||
      left.shed_capacity != right.shed_capacity ||
      left.weed_spawn_chance != right.weed_spawn_chance ||
      left.shop_unlock_interval != right.shop_unlock_interval ||
      left.shop_sell_interval != right.shop_sell_interval ||
      left.center_sell_interval != right.center_sell_interval ||
      left.farm_hand_cost_mult != right.farm_hand_cost_mult) {
    return false;
  }
  for (int product = 0; product < kNumProducts; ++product) {
    const MarketParams& lhs = left.market_params[product];
    const MarketParams& rhs = right.market_params[product];
    if (lhs.base != rhs.base || lhs.i0 != rhs.i0 || lhs.t != rhs.t ||
        lhs.below_func != rhs.below_func ||
        lhs.below_target != rhs.below_target ||
        lhs.above_func != rhs.above_func ||
        lhs.above_target != rhs.above_target) {
      return false;
    }
  }
  return true;
}

ConditionalProgramOwners ParseConditionalProgramOwners(
    py::list session_owners, py::list engine_owners, IntArray players,
    int workers) {
  const int batch = static_cast<int>(py::len(session_owners));
  if (batch < 1 || static_cast<int>(py::len(engine_owners)) != batch ||
      workers < 1 ||
      workers > 256) {
    throw py::value_error(
        "conditional program batch inputs must be nonempty and aligned");
  }
  const py::buffer_info info = players.request();
  if (info.ndim != 1 || info.shape[0] != batch) {
    throw py::value_error("conditional program players must have shape [B]");
  }
  const auto* values = static_cast<const int64_t*>(info.ptr);
  ConditionalProgramOwners result;
  result.sessions.reserve(static_cast<size_t>(batch));
  result.engines.reserve(static_cast<size_t>(batch));
  result.players.reserve(static_cast<size_t>(batch));
  for (int index = 0; index < batch; ++index) {
    if (values[index] < 0 || values[index] > 1) {
      throw py::value_error("conditional program player must be 0 or 1");
    }
    auto* session = py::cast<programs::Session*>(session_owners[index]);
    const auto* engine_owner =
        py::cast<const PyEngine*>(engine_owners[index]);
    const Engine& engine = engine_owner->raw_engine();
    if (!ConditionalProgramConfigsMatch(session->config(), engine.config())) {
      throw py::value_error(
          "conditional program session and engine configurations differ");
    }
    if (index > 0 &&
        (session->config().board_size !=
             result.sessions.front()->config().board_size ||
         session->maximum_decisions() !=
             result.sessions.front()->maximum_decisions())) {
      throw py::value_error(
          "conditional program batch sessions have incompatible shapes");
    }
    result.sessions.push_back(session);
    result.engines.push_back(&engine);
    result.players.push_back(static_cast<int>(values[index]));
  }
  return result;
}

std::vector<programs::Decision> MakeConditionalProgramDecisions(
    const ConditionalProgramOwners& owners, int workers) {
  const int batch = static_cast<int>(owners.sessions.size());
  std::vector<programs::Decision> output(static_cast<size_t>(batch));
  for (int index = 0; index < batch; ++index) {
    const int tiles = owners.sessions[index]->config().board_size *
                      owners.sessions[index]->config().board_size;
    programs::Decision& decision = output[index];
    decision.phase = programs::Phase::kDone;
    decision.task_argument_mask.assign(
        static_cast<size_t>(programs::kTaskCount) * programs::kArgumentCount,
        0);
    decision.task_target_mask.assign(
        static_cast<size_t>(programs::kTaskCount) * programs::kArgumentCount *
            tiles,
        0);
    decision.task_quantity_mode_mask.assign(
        static_cast<size_t>(programs::kTaskCount) * programs::kArgumentCount *
            programs::kQuantityModeCount,
        0);
    decision.task_quantity_max.assign(
        static_cast<size_t>(programs::kTaskCount) * programs::kArgumentCount,
        0);
    decision.raw_argument_mask.assign(
        static_cast<size_t>(programs::kRawOperationCount) *
            programs::kArgumentCount,
        0);
    decision.raw_quantity_mode_mask.assign(
        static_cast<size_t>(programs::kRawOperationCount) *
            programs::kArgumentCount * programs::kQuantityModeCount,
        0);
    decision.raw_quantity_max.assign(
        static_cast<size_t>(programs::kRawOperationCount) *
            programs::kArgumentCount,
        0);
    decision.market_item_mask.assign(
        static_cast<size_t>(programs::kMarketOrderCount) * kNumItems, 0);
    decision.market_quantity_mode_mask.assign(
        static_cast<size_t>(programs::kMarketOrderCount) * kNumItems *
            programs::kQuantityModeCount,
        0);
    decision.market_quantity_max.assign(
        static_cast<size_t>(programs::kMarketOrderCount) * kNumItems, 0);
    decision.target_reservations.assign(static_cast<size_t>(tiles), 0);
  }
  std::exception_ptr first_error;
  std::mutex error_mutex;
  {
    py::gil_scoped_release release;
#ifdef _OPENMP
#pragma omp parallel for schedule(static) num_threads(workers)
#endif
    for (int index = 0; index < batch; ++index) {
      try {
        if (owners.sessions[index]->DecisionRequired(
                *owners.engines[index], owners.players[index])) {
          output[index] = owners.sessions[index]->Observe(
              *owners.engines[index], owners.players[index]);
        }
      } catch (...) {
        std::lock_guard<std::mutex> lock(error_mutex);
        if (!first_error) first_error = std::current_exception();
      }
    }
  }
  if (first_error) std::rethrow_exception(first_error);
  return output;
}

struct ConditionalProgramActiveDecisions {
  std::vector<int64_t> rows;
  std::vector<programs::Decision> decisions;
};

ConditionalProgramActiveDecisions MakeConditionalProgramActiveDecisions(
    const ConditionalProgramOwners& owners, int workers) {
  const int batch = static_cast<int>(owners.sessions.size());
  std::vector<uint8_t> active(static_cast<size_t>(batch), 0);
  std::exception_ptr first_error;
  std::mutex error_mutex;
  {
    py::gil_scoped_release release;
#ifdef _OPENMP
#pragma omp parallel for schedule(static) num_threads(workers)
#endif
    for (int index = 0; index < batch; ++index) {
      try {
        active[index] = owners.sessions[index]->DecisionRequired(
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

  ConditionalProgramActiveDecisions output;
  output.rows.reserve(static_cast<size_t>(batch));
  for (int index = 0; index < batch; ++index) {
    if (active[index]) output.rows.push_back(index);
  }
  output.decisions.resize(output.rows.size());
  first_error = nullptr;
  {
    py::gil_scoped_release release;
    const int active_count = static_cast<int>(output.rows.size());
#ifdef _OPENMP
#pragma omp parallel for schedule(static) num_threads(workers)
#endif
    for (int offset = 0; offset < active_count; ++offset) {
      const int row = static_cast<int>(output.rows[offset]);
      try {
        output.decisions[offset] = owners.sessions[row]->Observe(
            *owners.engines[row], owners.players[row]);
      } catch (...) {
        std::lock_guard<std::mutex> lock(error_mutex);
        if (!first_error) first_error = std::current_exception();
      }
    }
  }
  if (first_error) std::rethrow_exception(first_error);
  return output;
}

py::dict StackConditionalProgramDecisions(
    const std::vector<programs::Decision>& decisions,
    const programs::Session& exemplar) {
  const int batch = static_cast<int>(decisions.size());
  const int tiles = exemplar.config().board_size * exemplar.config().board_size;
  py::array_t<int64_t> scalars({batch, 7});
  py::array_t<uint8_t> control({batch, programs::kControlCount});
  py::array_t<uint8_t> direction({batch, programs::kDirectionCount});
  py::array_t<uint8_t> task({batch, programs::kTaskCount});
  py::array_t<uint8_t> task_argument(
      {batch, programs::kTaskCount, programs::kArgumentCount});
  py::array_t<uint8_t> task_target(
      {batch, programs::kTaskCount, programs::kArgumentCount, tiles});
  py::array_t<uint8_t> task_quantity_mode(
      {batch, programs::kTaskCount, programs::kArgumentCount,
       programs::kQuantityModeCount});
  py::array_t<int64_t> task_quantity_max(
      {batch, programs::kTaskCount, programs::kArgumentCount});
  py::array_t<uint8_t> raw_operation(
      {batch, programs::kRawOperationCount});
  py::array_t<uint8_t> raw_argument(
      {batch, programs::kRawOperationCount, programs::kArgumentCount});
  py::array_t<uint8_t> raw_quantity_mode(
      {batch, programs::kRawOperationCount, programs::kArgumentCount,
       programs::kQuantityModeCount});
  py::array_t<int64_t> raw_quantity_max(
      {batch, programs::kRawOperationCount, programs::kArgumentCount});
  py::array_t<uint8_t> market_order(
      {batch, programs::kMarketOrderCount});
  py::array_t<uint8_t> market_item(
      {batch, programs::kMarketOrderCount, kNumItems});
  py::array_t<uint8_t> market_quantity_mode(
      {batch, programs::kMarketOrderCount, kNumItems,
       programs::kQuantityModeCount});
  py::array_t<int64_t> market_quantity_max(
      {batch, programs::kMarketOrderCount, kNumItems});
  py::array_t<int16_t> reservations({batch, tiles});
  py::array_t<float> root({batch, programs::kRootFeatureCount});
  py::array_t<int64_t> option({batch, programs::kOptionFeatureCount});
  for (int row = 0; row < batch; ++row) {
    const programs::Decision& value = decisions[row];
    const std::array<int64_t, 7> scalar_values = {
        static_cast<int64_t>(value.phase), value.unit_index, value.market_slot,
        value.unit_count, value.current_x, value.current_y, value.forced};
    std::copy(scalar_values.begin(), scalar_values.end(),
              scalars.mutable_data(row, 0));
    std::copy(value.control_mask.begin(), value.control_mask.end(),
              control.mutable_data(row, 0));
    std::copy(value.direction_mask.begin(), value.direction_mask.end(),
              direction.mutable_data(row, 0));
    std::copy(value.task_mask.begin(), value.task_mask.end(),
              task.mutable_data(row, 0));
    std::copy(value.task_argument_mask.begin(),
              value.task_argument_mask.end(), task_argument.mutable_data(row, 0, 0));
    std::copy(value.task_target_mask.begin(), value.task_target_mask.end(),
              task_target.mutable_data(row, 0, 0, 0));
    std::copy(value.task_quantity_mode_mask.begin(),
              value.task_quantity_mode_mask.end(),
              task_quantity_mode.mutable_data(row, 0, 0, 0));
    std::copy(value.task_quantity_max.begin(), value.task_quantity_max.end(),
              task_quantity_max.mutable_data(row, 0, 0));
    std::copy(value.raw_operation_mask.begin(), value.raw_operation_mask.end(),
              raw_operation.mutable_data(row, 0));
    std::copy(value.raw_argument_mask.begin(), value.raw_argument_mask.end(),
              raw_argument.mutable_data(row, 0, 0));
    std::copy(value.raw_quantity_mode_mask.begin(),
              value.raw_quantity_mode_mask.end(),
              raw_quantity_mode.mutable_data(row, 0, 0, 0));
    std::copy(value.raw_quantity_max.begin(), value.raw_quantity_max.end(),
              raw_quantity_max.mutable_data(row, 0, 0));
    std::copy(value.market_order_mask.begin(), value.market_order_mask.end(),
              market_order.mutable_data(row, 0));
    std::copy(value.market_item_mask.begin(), value.market_item_mask.end(),
              market_item.mutable_data(row, 0, 0));
    std::copy(value.market_quantity_mode_mask.begin(),
              value.market_quantity_mode_mask.end(),
              market_quantity_mode.mutable_data(row, 0, 0, 0));
    std::copy(value.market_quantity_max.begin(),
              value.market_quantity_max.end(),
              market_quantity_max.mutable_data(row, 0, 0));
    std::copy(value.target_reservations.begin(),
              value.target_reservations.end(), reservations.mutable_data(row, 0));
    std::copy(value.root_features.begin(), value.root_features.end(),
              root.mutable_data(row, 0));
    std::copy(value.option_features.begin(), value.option_features.end(),
              option.mutable_data(row, 0));
  }
  py::dict out;
  out["scalars"] = std::move(scalars);
  out["control_mask"] = std::move(control);
  out["direction_mask"] = std::move(direction);
  out["task_mask"] = std::move(task);
  out["task_argument_mask"] = std::move(task_argument);
  out["task_target_mask"] = std::move(task_target);
  out["task_quantity_mode_mask"] = std::move(task_quantity_mode);
  out["task_quantity_max"] = std::move(task_quantity_max);
  out["raw_operation_mask"] = std::move(raw_operation);
  out["raw_argument_mask"] = std::move(raw_argument);
  out["raw_quantity_mode_mask"] = std::move(raw_quantity_mode);
  out["raw_quantity_max"] = std::move(raw_quantity_max);
  out["market_order_mask"] = std::move(market_order);
  out["market_item_mask"] = std::move(market_item);
  out["market_quantity_mode_mask"] = std::move(market_quantity_mode);
  out["market_quantity_max"] = std::move(market_quantity_max);
  out["target_reservations"] = std::move(reservations);
  out["root_features"] = std::move(root);
  out["option_features"] = std::move(option);
  return out;
}

py::dict StackConditionalProgramActiveDecisions(
    const ConditionalProgramActiveDecisions& active,
    const programs::Session& exemplar) {
  py::dict out = StackConditionalProgramDecisions(active.decisions, exemplar);
  py::array_t<int64_t> rows(active.rows.size());
  std::copy(active.rows.begin(), active.rows.end(), rows.mutable_data());
  out["active_rows"] = std::move(rows);
  return out;
}

void BindConditionalPrograms(py::module_& module) {
  py::class_<programs::Session>(module, "ConditionalProgramSession")
      .def(py::init([](py::object configuration, int unit_limit) {
             return programs::Session(pyconv::ParseConfig(configuration),
                                      unit_limit);
           }),
           py::arg("configuration") = py::none(), py::arg("unit_limit") = 65)
      .def("reset", &programs::Session::Reset)
      .def("decision_required",
           [](programs::Session& session, const PyEngine& engine, int player) {
             return session.DecisionRequired(engine.raw_engine(), player);
           },
           py::arg("engine"), py::arg("player"))
      .def("observation",
           [](programs::Session& session, const PyEngine& engine, int player) {
             return ConditionalProgramDecisionToPy(
                 session.Observe(engine.raw_engine(), player), session);
           },
           py::arg("engine"), py::arg("player"))
      .def("select",
           [](programs::Session& session, const PyEngine& engine, int player,
              int64_t control, int64_t task, int64_t target, int64_t argument,
              int64_t direction, int64_t raw_operation, int64_t quantity_mode,
              int64_t exact_quantity) {
             session.Select(
                 engine.raw_engine(), player,
                 ParseConditionalProgramSelection(
                     control, task, target, argument, direction, raw_operation,
                     quantity_mode, exact_quantity));
           },
           py::arg("engine"), py::arg("player"), py::arg("control"),
           py::arg("task"), py::arg("target"), py::arg("argument"),
           py::arg("direction"), py::arg("raw_operation"),
           py::arg("quantity_mode"), py::arg("exact_quantity"))
      .def("action_numeric",
           [](programs::Session& session, const PyEngine& engine, int player) {
             return ConditionalProgramActionToPy(
                 session.Action(engine.raw_engine(), player));
           },
           py::arg("engine"), py::arg("player"))
      .def("decision_required_visible",
           [](programs::Session& session, const py::dict& observation) {
             return session.DecisionRequiredVisible(
                 ParseConditionalProgramVisibleState(session, observation));
           })
      .def("observation_visible",
           [](programs::Session& session, const py::dict& observation) {
             return ConditionalProgramDecisionToPy(
                 session.ObserveVisible(
                     ParseConditionalProgramVisibleState(session, observation)),
                 session);
           })
      .def("select_visible",
           [](programs::Session& session, const py::dict& observation,
              int64_t control, int64_t task, int64_t target, int64_t argument,
              int64_t direction, int64_t raw_operation, int64_t quantity_mode,
              int64_t exact_quantity) {
             session.SelectVisible(
                 ParseConditionalProgramVisibleState(session, observation),
                 ParseConditionalProgramSelection(
                     control, task, target, argument, direction, raw_operation,
                     quantity_mode, exact_quantity));
           },
           py::arg("observation"), py::arg("control"), py::arg("task"),
           py::arg("target"), py::arg("argument"), py::arg("direction"),
           py::arg("raw_operation"), py::arg("quantity_mode"),
           py::arg("exact_quantity"))
      .def(
          "select_replay_unit_visible",
          [](programs::Session& session, const py::dict& observation,
             py::array_t<int64_t,
                         py::array::c_style | py::array::forcecast> fallback,
             py::object proposals) {
            const py::buffer_info fallback_info = fallback.request();
            if (fallback_info.ndim != 1 || fallback_info.shape[0] != 8) {
              throw py::value_error(
                  "conditional replay fallback must have shape [8]");
            }
            const auto parse = [](const int64_t* values) {
              return programs::Selection{
                  values[0], values[1], values[2], values[3],
                  values[4], values[5], values[6], values[7]};
            };
            std::vector<programs::Selection> parsed_proposals;
            if (!proposals.is_none()) {
              const auto values = py::cast<py::array_t<
                  int64_t, py::array::c_style | py::array::forcecast>>(
                  proposals);
              const py::buffer_info info = values.request();
              if (info.ndim != 2 || info.shape[1] != 8) {
                throw py::value_error(
                    "conditional replay proposals must have shape [N,8]");
              }
              const auto* data = static_cast<const int64_t*>(info.ptr);
              parsed_proposals.reserve(static_cast<size_t>(info.shape[0]));
              for (py::ssize_t row = 0; row < info.shape[0]; ++row) {
                parsed_proposals.emplace_back(parse(data + row * 8));
              }
            }
            const programs::Selection selected =
                session.SelectReplayUnitVisible(
                    ParseConditionalProgramVisibleState(session, observation),
                    parse(static_cast<const int64_t*>(fallback_info.ptr)),
                    parsed_proposals);
            py::array_t<int64_t> out(8);
            auto* data = out.mutable_data();
            data[0] = selected.control;
            data[1] = selected.task;
            data[2] = selected.target;
            data[3] = selected.argument;
            data[4] = selected.direction;
            data[5] = selected.raw_operation;
            data[6] = selected.quantity_mode;
            data[7] = selected.exact_quantity;
            return out;
          },
          py::arg("observation"), py::arg("fallback"),
          py::arg("proposals") = py::none())
      .def("action_numeric_visible",
           [](programs::Session& session, const py::dict& observation) {
             return ConditionalProgramActionToPy(session.ActionVisible(
                 ParseConditionalProgramVisibleState(session, observation)));
           })
      .def_property_readonly("phase", [](const programs::Session& session) {
        return static_cast<int64_t>(session.phase());
      });
  module.def(
      "conditional_program_spec",
      [](py::object configuration, int unit_limit) {
        const programs::Session session(pyconv::ParseConfig(configuration),
                                        unit_limit);
        return ConditionalProgramSpec(session);
      },
      py::arg("configuration") = py::none(), py::arg("unit_limit") = 65);
  module.def(
      "conditional_program_observations_batch",
      [](py::list sessions, py::list engines, IntArray players, int workers) {
        ConditionalProgramOwners owners = ParseConditionalProgramOwners(
            sessions, engines, std::move(players), workers);
        const programs::Session& exemplar = *owners.sessions.front();
        return StackConditionalProgramDecisions(
            MakeConditionalProgramDecisions(owners, workers), exemplar);
      },
      py::arg("sessions"), py::arg("engines"), py::arg("players"),
      py::arg("workers"));
  module.def(
      "conditional_program_active_observations_batch",
      [](py::list sessions, py::list engines, IntArray players, int workers) {
        ConditionalProgramOwners owners = ParseConditionalProgramOwners(
            sessions, engines, std::move(players), workers);
        const programs::Session& exemplar = *owners.sessions.front();
        return StackConditionalProgramActiveDecisions(
            MakeConditionalProgramActiveDecisions(owners, workers), exemplar);
      },
      py::arg("sessions"), py::arg("engines"), py::arg("players"),
      py::arg("workers"));
  module.def(
      "conditional_program_select_batch",
      [](py::list sessions, py::list engines, IntArray players,
         py::array_t<int64_t,
                     py::array::c_style | py::array::forcecast> selections,
         py::array_t<uint8_t,
                     py::array::c_style | py::array::forcecast> active,
         int workers) {
        ConditionalProgramOwners owners = ParseConditionalProgramOwners(
            sessions, engines, std::move(players), workers);
        const py::buffer_info selection_info = selections.request();
        const py::buffer_info active_info = active.request();
        const int batch = static_cast<int>(owners.sessions.size());
        if (selection_info.ndim != 2 || selection_info.shape[0] != batch ||
            selection_info.shape[1] != 8 || active_info.ndim != 1 ||
            active_info.shape[0] != batch) {
          throw py::value_error(
              "conditional program selections must have shape [B,8]");
        }
        const auto* values =
            static_cast<const int64_t*>(selection_info.ptr);
        const auto* enabled = static_cast<const uint8_t*>(active_info.ptr);
        std::exception_ptr first_error;
        std::mutex error_mutex;
        {
          py::gil_scoped_release release;
#ifdef _OPENMP
#pragma omp parallel for schedule(static) num_threads(workers)
#endif
          for (int index = 0; index < batch; ++index) {
            if (!enabled[index]) continue;
            try {
              const int64_t* row = values + static_cast<size_t>(index) * 8;
              owners.sessions[index]->Select(
                  *owners.engines[index], owners.players[index],
                  programs::Selection{row[0], row[1], row[2], row[3], row[4],
                                      row[5], row[6], row[7]});
            } catch (...) {
              std::lock_guard<std::mutex> lock(error_mutex);
              if (!first_error) first_error = std::current_exception();
            }
          }
        }
        if (first_error) std::rethrow_exception(first_error);
      },
      py::arg("sessions"), py::arg("engines"), py::arg("players"),
      py::arg("selections"), py::arg("active"), py::arg("workers"));
  module.def(
      "conditional_program_actions_batch",
      [](py::list sessions, py::list engines, IntArray players, int workers) {
        ConditionalProgramOwners owners = ParseConditionalProgramOwners(
            sessions, engines, std::move(players), workers);
        const int batch = static_cast<int>(owners.sessions.size());
        const int width = owners.sessions.front()->maximum_decisions();
        py::array_t<int64_t> tokens({batch, width});
        py::array_t<int64_t> quantities({batch, width});
        py::array_t<int64_t> counts(batch);
        py::array_t<int64_t> units(batch);
        auto* token_data = tokens.mutable_data();
        auto* quantity_data = quantities.mutable_data();
        auto* count_data = counts.mutable_data();
        auto* unit_data = units.mutable_data();
        std::exception_ptr first_error;
        std::mutex error_mutex;
        {
          py::gil_scoped_release release;
#ifdef _OPENMP
#pragma omp parallel for schedule(static) num_threads(workers)
#endif
          for (int index = 0; index < batch; ++index) {
            try {
              const programs::NumericAction action =
                  owners.sessions[index]->Action(
                      *owners.engines[index], owners.players[index]);
              const size_t offset = static_cast<size_t>(index) * width;
              std::copy(action.tokens.begin(), action.tokens.end(),
                        token_data + offset);
              std::copy(action.quantities.begin(), action.quantities.end(),
                        quantity_data + offset);
              count_data[index] = action.decision_count;
              unit_data[index] = action.unit_count;
            } catch (...) {
              std::lock_guard<std::mutex> lock(error_mutex);
              if (!first_error) first_error = std::current_exception();
            }
          }
        }
        if (first_error) std::rethrow_exception(first_error);
        py::dict out;
        out["tokens"] = std::move(tokens);
        out["quantities"] = std::move(quantities);
        out["decision_counts"] = std::move(counts);
        out["unit_counts"] = std::move(units);
        return out;
      },
      py::arg("sessions"), py::arg("engines"), py::arg("players"),
      py::arg("workers"));
}
