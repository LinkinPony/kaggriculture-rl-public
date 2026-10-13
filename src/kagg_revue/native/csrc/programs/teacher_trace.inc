// Included by bindings.cpp after programs/python_boundary.inc.

namespace teacher_trace {

inline constexpr int kTokenSpecWidth = 6;
inline constexpr int kUnitToken = 0;
inline constexpr int kMarketToken = 1;
inline constexpr int kSkipMarketToken = 2;
inline constexpr int kRepairCount = 4;
inline constexpr int kQuantityClipped = 0;
inline constexpr int kUnitToPass = 1;
inline constexpr int kMarketSkip = 2;
inline constexpr int kMarketOmitted = 3;

struct Buffers {
  py::array_t<int16_t> scalars;
  py::array_t<float> roots;
  py::array_t<int32_t> options;
  py::array_t<int16_t> reservations;
  py::array_t<int64_t> actions;
  py::array_t<uint8_t> masks;
  py::array_t<int64_t> quantity_max;
  py::array_t<int16_t> decision_counts;
  py::array_t<int64_t> repairs;
};

int CompactMaskWidth(int tiles) {
  return programs::kControlCount + programs::kDirectionCount +
         programs::kTaskCount + programs::kArgumentCount + tiles +
         programs::kRawOperationCount + programs::kQuantityModeCount +
         programs::kMarketOrderCount + kNumItems;
}

bool SelectQuantity(const uint8_t* mask, int64_t maximum, int64_t requested,
                    int64_t* mode, int64_t* exact, int64_t* repairs) {
  if (maximum < 1 || requested < 1) return false;
  const int64_t effective = std::min(requested, maximum);
  if (effective != requested) ++repairs[kQuantityClipped];
  if (effective == 1 && mask[static_cast<int>(programs::QuantityMode::kOne)]) {
    *mode = static_cast<int64_t>(programs::QuantityMode::kOne);
    *exact = 1;
    return true;
  }
  if (mask[static_cast<int>(programs::QuantityMode::kExact)]) {
    *mode = static_cast<int64_t>(programs::QuantityMode::kExact);
    *exact = effective;
    return true;
  }
  return false;
}

programs::Selection CancelSelection() {
  return programs::Selection{
      static_cast<int64_t>(programs::Control::kCancelPass), 0, -1,
      programs::kNoneArgument,
      static_cast<int64_t>(programs::Direction::kNorth),
      static_cast<int64_t>(programs::RawOperation::kDrop),
      static_cast<int64_t>(programs::QuantityMode::kOne), 1};
}

bool IsQuantityRaw(int operation) {
  return operation == static_cast<int>(programs::RawOperation::kPickup) ||
         operation == static_cast<int>(programs::RawOperation::kPlace);
}

bool IsArgumentRaw(int operation) {
  return IsQuantityRaw(operation) ||
         operation == static_cast<int>(programs::RawOperation::kPlant);
}

bool IsItemMarket(int order) {
  return order == static_cast<int>(programs::MarketOrderType::kSell) ||
         order == static_cast<int>(programs::MarketOrderType::kBuySeed) ||
         order == static_cast<int>(programs::MarketOrderType::kBuyProduct) ||
         order == static_cast<int>(programs::MarketOrderType::kBuyAnimal);
}

programs::Selection SelectUnit(const programs::Decision& decision,
                               const int64_t* spec, int64_t requested,
                               int64_t* maximum, int64_t* repairs) {
  programs::Selection selection = CancelSelection();
  const int control = static_cast<int>(spec[1]);
  if (control == static_cast<int>(programs::Control::kCancelPass)) {
    if (!decision.control_mask[control]) {
      throw std::invalid_argument(
          "teacher program cannot express a forced unit decision");
    }
    return selection;
  }
  if (control == static_cast<int>(programs::Control::kStep)) {
    const int direction = static_cast<int>(spec[3]);
    if (!decision.control_mask[control] || direction < 0 ||
        direction >= programs::kDirectionCount ||
        !decision.direction_mask[direction]) {
      ++repairs[kUnitToPass];
      if (!decision.control_mask[static_cast<int>(programs::Control::kCancelPass)]) {
        throw std::invalid_argument(
            "teacher program cannot express a forced unit decision");
      }
      return selection;
    }
    selection.control = control;
    selection.direction = direction;
    return selection;
  }
  if (control != static_cast<int>(programs::Control::kRawLocal)) {
    throw std::invalid_argument("teacher program unit token is invalid");
  }
  const int operation = static_cast<int>(spec[4]);
  const int argument = static_cast<int>(spec[2]);
  bool legal = decision.control_mask[control] && operation >= 0 &&
               operation < programs::kRawOperationCount &&
               decision.raw_operation_mask[operation];
  if (legal && IsArgumentRaw(operation)) {
    legal = argument >= 0 && argument < programs::kArgumentCount &&
            decision.raw_argument_mask[
                operation * programs::kArgumentCount + argument];
  }
  int64_t quantity_mode = static_cast<int64_t>(programs::QuantityMode::kOne);
  int64_t exact_quantity = 1;
  if (legal && IsQuantityRaw(operation)) {
    const int offset = operation * programs::kArgumentCount + argument;
    *maximum = decision.raw_quantity_max[offset];
    legal = SelectQuantity(
        decision.raw_quantity_mode_mask.data() +
            offset * programs::kQuantityModeCount,
        *maximum, requested, &quantity_mode, &exact_quantity, repairs);
  }
  if (!legal) {
    ++repairs[kUnitToPass];
    if (!decision.control_mask[static_cast<int>(programs::Control::kCancelPass)]) {
      throw std::invalid_argument(
          "teacher program cannot express a forced unit decision");
    }
    *maximum = 0;
    return selection;
  }
  selection.control = control;
  selection.argument = argument;
  selection.raw_operation = operation;
  selection.quantity_mode = quantity_mode;
  selection.exact_quantity = exact_quantity;
  return selection;
}

bool SelectMarket(const programs::Decision& decision, const int64_t* spec,
                  int64_t requested, programs::Selection* selection,
                  int64_t* order, int64_t* maximum, int64_t* repairs) {
  if (spec[0] == kSkipMarketToken) {
    ++repairs[kMarketSkip];
    return false;
  }
  if (spec[0] != kMarketToken) {
    throw std::invalid_argument(
        "teacher program market suffix contains a unit action");
  }
  *order = spec[5];
  if (*order < 0 || *order >= programs::kMarketOrderCount ||
      !decision.market_order_mask[*order]) {
    ++repairs[kMarketOmitted];
    return false;
  }
  *selection = programs::Selection{
      static_cast<int64_t>(programs::Control::kKeep), *order, -1, 0,
      static_cast<int64_t>(programs::Direction::kNorth),
      static_cast<int64_t>(programs::RawOperation::kDrop),
      static_cast<int64_t>(programs::QuantityMode::kOne), 1};
  if (!IsItemMarket(static_cast<int>(*order))) return true;
  const int item = static_cast<int>(spec[2]);
  const int offset = static_cast<int>(*order) * kNumItems + item;
  if (item < 0 || item >= kNumItems || !decision.market_item_mask[offset]) {
    ++repairs[kMarketOmitted];
    return false;
  }
  *maximum = decision.market_quantity_max[offset];
  int64_t mode = static_cast<int64_t>(programs::QuantityMode::kOne);
  int64_t exact = 1;
  if (!SelectQuantity(decision.market_quantity_mode_mask.data() +
                          offset * programs::kQuantityModeCount,
                      *maximum, requested, &mode, &exact, repairs)) {
    ++repairs[kMarketOmitted];
    return false;
  }
  selection->argument = item;
  selection->quantity_mode = mode;
  selection->exact_quantity = exact;
  return true;
}

void CopyCompactMask(const programs::Decision& decision,
                     const programs::Selection& selection, int64_t order,
                     int tiles, uint8_t* output) {
  const bool unit = decision.phase == programs::Phase::kUnit;
  const bool market = decision.phase == programs::Phase::kMarket;
  int cursor = 0;
  auto fallback = [&output, &cursor](int width, int index = 0) {
    output[cursor + index] = 1;
    cursor += width;
  };
  auto copy = [&output, &cursor](const uint8_t* values, int width) {
    std::copy_n(values, width, output + cursor);
    cursor += width;
  };
  if (unit) {
    copy(decision.control_mask.data(), programs::kControlCount);
  } else {
    fallback(programs::kControlCount);
  }
  if (unit && selection.control == static_cast<int>(programs::Control::kStep)) {
    copy(decision.direction_mask.data(), programs::kDirectionCount);
  } else {
    fallback(programs::kDirectionCount);
  }
  fallback(programs::kTaskCount);
  const int operation = static_cast<int>(selection.raw_operation);
  const int argument = static_cast<int>(selection.argument);
  if (unit &&
      selection.control == static_cast<int>(programs::Control::kRawLocal) &&
      IsArgumentRaw(operation)) {
    copy(decision.raw_argument_mask.data() +
             operation * programs::kArgumentCount,
         programs::kArgumentCount);
  } else {
    fallback(programs::kArgumentCount, programs::kNoneArgument);
  }
  fallback(tiles);
  if (unit &&
      selection.control == static_cast<int>(programs::Control::kRawLocal)) {
    copy(decision.raw_operation_mask.data(), programs::kRawOperationCount);
  } else {
    fallback(programs::kRawOperationCount);
  }
  if (unit &&
      selection.control == static_cast<int>(programs::Control::kRawLocal) &&
      IsQuantityRaw(operation)) {
    copy(decision.raw_quantity_mode_mask.data() +
             (operation * programs::kArgumentCount + argument) *
                 programs::kQuantityModeCount,
         programs::kQuantityModeCount);
  } else if (market && IsItemMarket(static_cast<int>(order))) {
    copy(decision.market_quantity_mode_mask.data() +
             (static_cast<int>(order) * kNumItems + argument) *
                 programs::kQuantityModeCount,
         programs::kQuantityModeCount);
  } else {
    fallback(programs::kQuantityModeCount);
  }
  if (market) {
    copy(decision.market_order_mask.data(), programs::kMarketOrderCount);
  } else {
    fallback(programs::kMarketOrderCount);
  }
  if (market && IsItemMarket(static_cast<int>(order))) {
    copy(decision.market_item_mask.data() +
             static_cast<int>(order) * kNumItems,
         kNumItems);
  } else {
    fallback(kNumItems);
  }
}

void RecordDecision(const programs::Decision& decision,
                    const programs::Selection& selection, int64_t order,
                    int64_t maximum, int row, int position, int capacity,
                    int tiles, int mask_width, Buffers* buffers) {
  const size_t decision_offset =
      static_cast<size_t>(row) * capacity + position;
  const std::array<int16_t, 7> scalars = {
      static_cast<int16_t>(decision.phase),
      static_cast<int16_t>(decision.unit_index),
      static_cast<int16_t>(decision.market_slot),
      static_cast<int16_t>(decision.unit_count),
      static_cast<int16_t>(decision.current_x),
      static_cast<int16_t>(decision.current_y),
      static_cast<int16_t>(decision.forced)};
  std::copy(scalars.begin(), scalars.end(),
            buffers->scalars.mutable_data() + decision_offset * 7);
  std::copy(decision.root_features.begin(), decision.root_features.end(),
            buffers->roots.mutable_data() +
                decision_offset * programs::kRootFeatureCount);
  std::transform(
      decision.option_features.begin(), decision.option_features.end(),
      buffers->options.mutable_data() +
          decision_offset * programs::kOptionFeatureCount,
      [](int64_t value) { return static_cast<int32_t>(value); });
  std::copy(decision.target_reservations.begin(),
            decision.target_reservations.end(),
            buffers->reservations.mutable_data() + decision_offset * tiles);
  const std::array<int64_t, 9> actions = {
      selection.control, 0, selection.target, selection.argument,
      selection.direction, selection.raw_operation, selection.quantity_mode,
      selection.exact_quantity, order};
  std::copy(actions.begin(), actions.end(),
            buffers->actions.mutable_data() + decision_offset * 9);
  CopyCompactMask(decision, selection, order, tiles,
                  buffers->masks.mutable_data() +
                      decision_offset * mask_width);
  buffers->quantity_max.mutable_data()[decision_offset] = maximum;
}

void CompileRow(programs::Session* session, const Engine* engine, int player,
                const int64_t* tokens, const int64_t* quantities,
                int count, int unit_count, const int64_t* specs, int spec_count,
                int row, int capacity, int tiles, int mask_width,
                Buffers* buffers) {
  int cursor = 0;
  int position = 0;
  int64_t* repairs = buffers->repairs.mutable_data(row, 0);
  while (position < capacity && session->DecisionRequired(*engine, player)) {
    const programs::Decision decision = session->Observe(*engine, player);
    programs::Selection selection = CancelSelection();
    int64_t maximum = 0;
    int64_t order = static_cast<int64_t>(programs::MarketOrderType::kEnd);
    if (decision.phase == programs::Phase::kUnit) {
      if (cursor >= unit_count) {
        throw std::invalid_argument("teacher program exhausted unit actions");
      }
      const int64_t token = tokens[cursor];
      if (token < 0 || token >= spec_count ||
          specs[token * kTokenSpecWidth] != kUnitToken) {
        throw std::invalid_argument(
            "teacher program unit prefix contains a market action");
      }
      selection = SelectUnit(decision, specs + token * kTokenSpecWidth,
                             quantities[cursor], &maximum, repairs);
      ++cursor;
    } else if (decision.phase == programs::Phase::kMarket) {
      bool selected = false;
      while (cursor < count && !selected) {
        const int64_t token = tokens[cursor];
        if (token < 0 || token >= spec_count) {
          throw std::invalid_argument("teacher program token is invalid");
        }
        selected = SelectMarket(decision,
                                specs + token * kTokenSpecWidth,
                                quantities[cursor], &selection, &order,
                                &maximum, repairs);
        ++cursor;
      }
      if (!selected) {
        const std::array<int64_t, kTokenSpecWidth> stop = {
            kMarketToken, static_cast<int64_t>(programs::Control::kKeep), 0,
            static_cast<int64_t>(programs::Direction::kNorth),
            static_cast<int64_t>(programs::RawOperation::kDrop),
            static_cast<int64_t>(programs::MarketOrderType::kEnd)};
        if (!SelectMarket(decision, stop.data(), 0, &selection, &order,
                          &maximum, repairs)) {
          throw std::invalid_argument(
              "teacher program cannot terminate its market phase");
        }
      }
    } else {
      throw std::logic_error("teacher program observed an invalid phase");
    }
    RecordDecision(decision, selection, order, maximum, row, position,
                   capacity, tiles, mask_width, buffers);
    programs::Selection applied = selection;
    if (decision.phase == programs::Phase::kMarket) applied.task = order;
    session->Select(*engine, player, applied);
    ++position;
  }
  if (session->DecisionRequired(*engine, player)) {
    throw std::invalid_argument(
        "teacher program exceeds the native decision capacity");
  }
  buffers->decision_counts.mutable_data()[row] =
      static_cast<int16_t>(position);
}

py::dict CompileBatch(
    py::list sessions, py::list engines, IntArray players, IntArray tokens,
    IntArray quantities, IntArray counts, IntArray unit_counts,
    IntArray token_specs, int workers) {
  ConditionalProgramOwners owners = ParseConditionalProgramOwners(
      std::move(sessions), std::move(engines), std::move(players), workers);
  const int batch = static_cast<int>(owners.sessions.size());
  const py::buffer_info token_info = tokens.request();
  const py::buffer_info quantity_info = quantities.request();
  const py::buffer_info count_info = counts.request();
  const py::buffer_info unit_info = unit_counts.request();
  const py::buffer_info spec_info = token_specs.request();
  if (token_info.ndim != 2 || token_info.shape[0] != batch ||
      quantity_info.ndim != 2 || quantity_info.shape != token_info.shape ||
      count_info.ndim != 1 || count_info.shape[0] != batch ||
      unit_info.ndim != 1 || unit_info.shape[0] != batch ||
      spec_info.ndim != 2 || spec_info.shape[1] != kTokenSpecWidth ||
      spec_info.shape[0] < 1) {
    throw py::value_error("native teacher trace inputs are misaligned");
  }
  const int width = static_cast<int>(token_info.shape[1]);
  const int capacity = owners.sessions.front()->maximum_decisions();
  const int tiles = owners.sessions.front()->config().board_size *
                    owners.sessions.front()->config().board_size;
  const int mask_width = CompactMaskWidth(tiles);
  const int spec_count = static_cast<int>(spec_info.shape[0]);
  const auto* token_data = static_cast<const int64_t*>(token_info.ptr);
  const auto* quantity_data = static_cast<const int64_t*>(quantity_info.ptr);
  const auto* count_data = static_cast<const int64_t*>(count_info.ptr);
  const auto* unit_data = static_cast<const int64_t*>(unit_info.ptr);
  const auto* spec_data = static_cast<const int64_t*>(spec_info.ptr);
  for (int row = 0; row < batch; ++row) {
    if (unit_data[row] < 1 || unit_data[row] > count_data[row] ||
        count_data[row] > width) {
      throw py::value_error("native teacher trace action counts are invalid");
    }
  }
  Buffers output{
      py::array_t<int16_t>({batch, capacity, 7}),
      py::array_t<float>({batch, capacity, programs::kRootFeatureCount}),
      py::array_t<int32_t>({batch, capacity, programs::kOptionFeatureCount}),
      py::array_t<int16_t>({batch, capacity, tiles}),
      py::array_t<int64_t>({batch, capacity, 9}),
      py::array_t<uint8_t>({batch, capacity, mask_width}),
      py::array_t<int64_t>({batch, capacity}),
      py::array_t<int16_t>(batch),
      py::array_t<int64_t>({batch, kRepairCount})};
  std::fill_n(output.scalars.mutable_data(), output.scalars.size(), int16_t{0});
  std::fill_n(output.roots.mutable_data(), output.roots.size(), 0.0F);
  std::fill_n(output.options.mutable_data(), output.options.size(), int32_t{0});
  std::fill_n(output.reservations.mutable_data(), output.reservations.size(),
              int16_t{0});
  std::fill_n(output.actions.mutable_data(), output.actions.size(), int64_t{0});
  std::fill_n(output.masks.mutable_data(), output.masks.size(), uint8_t{0});
  std::fill_n(output.quantity_max.mutable_data(), output.quantity_max.size(),
              int64_t{0});
  std::fill_n(output.decision_counts.mutable_data(),
              output.decision_counts.size(), int16_t{0});
  std::fill_n(output.repairs.mutable_data(), output.repairs.size(), int64_t{0});
  std::exception_ptr first_error;
  std::mutex error_mutex;
  {
    py::gil_scoped_release release;
#ifdef _OPENMP
#pragma omp parallel for schedule(static) num_threads(workers)
#endif
    for (int row = 0; row < batch; ++row) {
      try {
        CompileRow(owners.sessions[row], owners.engines[row],
                   owners.players[row], token_data + row * width,
                   quantity_data + row * width,
                   static_cast<int>(count_data[row]),
                   static_cast<int>(unit_data[row]), spec_data, spec_count, row,
                   capacity, tiles, mask_width, &output);
      } catch (...) {
        std::lock_guard<std::mutex> lock(error_mutex);
        if (!first_error) first_error = std::current_exception();
      }
    }
  }
  if (first_error) std::rethrow_exception(first_error);
  py::dict result;
  result["scalars"] = std::move(output.scalars);
  result["root_features"] = std::move(output.roots);
  result["option_features"] = std::move(output.options);
  result["target_reservations"] = std::move(output.reservations);
  result["actions"] = std::move(output.actions);
  result["conditional_masks"] = std::move(output.masks);
  result["quantity_max"] = std::move(output.quantity_max);
  result["decision_counts"] = std::move(output.decision_counts);
  result["repair_counts"] = std::move(output.repairs);
  return result;
}

}  // namespace teacher_trace

void BindConditionalProgramTeacherTrace(py::module_& module) {
  module.def(
      "conditional_program_compile_teacher_batch",
      &teacher_trace::CompileBatch, py::arg("sessions"), py::arg("engines"),
      py::arg("players"), py::arg("tokens"), py::arg("quantities"),
      py::arg("decision_counts"), py::arg("unit_counts"),
      py::arg("token_specs"), py::arg("workers"),
      "Compile complete direct-action teacher traces in one native batch.");
}
