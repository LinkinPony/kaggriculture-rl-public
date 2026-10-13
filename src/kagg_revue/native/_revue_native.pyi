from typing import Any

class Engine:
    def __init__(self, seed: int, configuration: dict[str, Any] | None = None) -> None: ...
    def reset(self, seed: int) -> None: ...
    def clone(self) -> Engine: ...
    def step(self, action0: Any, action1: Any) -> bool: ...
    def step_numeric(
        self,
        tokens: Any,
        quantities: Any,
        decision_counts: Any,
        unit_counts: Any,
    ) -> bool: ...
    def step_mixed_numeric(
        self,
        numeric_player: int,
        tokens: Any,
        quantities: Any,
        decision_count: int,
        unit_count: int,
        other_action: Any,
    ) -> bool: ...
    def step_with_trace(self, action0: Any, action1: Any) -> dict[str, Any]: ...
    def observation(self, player: int) -> dict[str, Any]: ...
    def encode_numeric(self, player: int, unit_limit: int) -> tuple[Any, Any, Any]: ...
    def policy_session(self, player: int, unit_limit: int) -> PolicySession: ...
    def money(self, player: int) -> float: ...
    def market_price(self, item: str, inventory: int) -> int: ...
    @property
    def done(self) -> bool: ...
    @property
    def step_index(self) -> int: ...
    @property
    def configuration(self) -> dict[str, Any]: ...

class PyRandom:
    def __init__(self, seed: int) -> None: ...
    def random(self) -> float: ...
    def getrandbits(self, k: int) -> int: ...
    def randbelow(self, n: int) -> int: ...

def actor_encoder_spec() -> dict[str, Any]: ...
def encode_actor_observation(
    observation: dict[str, Any],
    configuration: dict[str, Any] | None,
    unit_limit: int,
    opponent_shed_estimate: Any = None,
) -> dict[str, Any]: ...
def encode_official_observation_numeric(
    observation: dict[str, Any],
    configuration: dict[str, Any] | None,
    unit_limit: int,
    opponent_shed_estimate: Any = None,
) -> tuple[Any, Any, Any]: ...
def official_action_control_spec() -> dict[str, Any]: ...
def action_codec_spec() -> dict[str, Any]: ...
def derived_fact_spec() -> dict[str, Any]: ...
def gpu_policy_state_spec(board_size: int, unit_limit: int) -> dict[str, int]: ...
def decode_action_tokens(
    tokens: Any,
    quantities: Any,
    decision_count: int,
    unit_count: int,
    max_market_orders: int,
) -> dict[str, Any]: ...

class PolicySession:
    def __init__(
        self,
        observation: dict[str, Any],
        configuration: dict[str, Any] | None,
        unit_limit: int,
    ) -> None: ...
    def encode(self) -> tuple[Any, Any, Any]: ...
    def legal_mask(self) -> Any: ...
    def turn_facts(self, opponent_lower: Any = None, opponent_upper: Any = None) -> Any: ...
    def prefix_facts(self) -> Any: ...
    def candidate_facts(self) -> Any: ...
    def flow_snapshot(self) -> dict[str, Any]: ...
    def own_market_flow_bounds(self) -> Any: ...
    def gpu_state(self) -> Any: ...
    def select(self, token: int, quantity: int = 0) -> None: ...
    def select_compiled_units(self, tokens: Any, quantities: Any) -> None: ...
    def action(self) -> dict[str, Any]: ...
    @property
    def phase(self) -> int: ...
    @property
    def unit_count(self) -> int: ...
    @property
    def decision_count(self) -> int: ...

class PolicySessionBatch:
    def __init__(self, sessions: list[PolicySession], workers: int) -> None: ...
    def encode(self) -> tuple[Any, Any, Any]: ...
    def encode_compact(self) -> tuple[Any, Any, Any]: ...
    def phases(self) -> Any: ...
    def unit_counts(self) -> Any: ...
    def legal_masks(self) -> Any: ...
    def decision_inputs(self) -> tuple[Any, Any]: ...
    def gpu_state(self) -> Any: ...
    def gpu_state_compact(self) -> Any: ...
    def flow_snapshots(self) -> dict[str, Any]: ...
    def turn_facts_batch(self, opponent_lower: Any, opponent_upper: Any) -> dict[str, Any]: ...
    def own_market_flow_bounds_batch(self) -> Any: ...
    def select(self, tokens: Any, quantities: Any, active: Any) -> None: ...
    def select_compiled_units(
        self,
        tokens: Any,
        quantities: Any,
        unit_counts: Any,
    ) -> None: ...
    def select_sequences(
        self,
        tokens: Any,
        quantities: Any,
        decision_counts: Any,
        unit_counts: Any,
    ) -> None: ...
    def compiled_unit_inputs(
        self,
        tokens: Any,
        quantities: Any,
        unit_counts: Any,
        include_facts: bool,
        include_gpu_state: bool,
    ) -> dict[str, Any]: ...
    def decision_facts(self) -> tuple[Any, Any]: ...
    @property
    def size(self) -> int: ...
    @property
    def workers(self) -> int: ...

def engine_policy_session_batch(
    engines: list[Engine],
    players: list[int],
    unit_limit: int,
    workers: int,
) -> PolicySessionBatch: ...
def engine_policy_turn_inputs(
    engines: list[Engine],
    players: list[int],
    unit_limit: int,
    workers: int,
) -> tuple[Any, Any, Any, Any, Any]: ...
def engine_policy_turn_inputs_into(
    engines: list[Engine],
    players: list[int],
    unit_limit: int,
    workers: int,
    board: Any,
    units: Any,
    global_features: Any,
    unit_counts: Any,
    state: Any,
) -> None: ...
def engine_policy_turn_inputs_compact_into(
    engines: list[Engine],
    players: list[int],
    unit_limit: int,
    workers: int,
    board: Any,
    units: Any,
    global_features: Any,
    unit_counts: Any,
    state: Any,
) -> None: ...
def engine_step_numeric_batch(
    engines: list[Engine],
    tokens: Any,
    quantities: Any,
    decision_counts: Any,
    unit_counts: Any,
    workers: int,
) -> Any: ...

class CapabilitySession:
    def __init__(
        self,
        configuration: dict[str, Any] | None = None,
        max_candidates: int = 16,
        max_edits: int = 2,
    ) -> None: ...
    def candidates(self, engine: Engine, player: int) -> dict[str, Any]: ...
    def select(self, candidate_index: int) -> int: ...
    def action_numeric(self, engine: Engine, player: int) -> dict[str, Any]: ...
    def decision_required(self, engine: Engine, player: int) -> bool: ...
    def reset(self) -> None: ...
    @property
    def max_candidates(self) -> int: ...
    @property
    def max_edits(self) -> int: ...
    @property
    def active(self) -> bool: ...
    @property
    def selected_mode(self) -> int: ...
    @property
    def selected_canonical_id(self) -> int: ...

def capability_spec() -> dict[str, Any]: ...
def capability_candidates_batch(
    sessions: list[CapabilitySession],
    engines: list[Engine],
    players: Any,
    workers: int,
) -> dict[str, Any]: ...
def capability_select_batch(
    sessions: list[CapabilitySession],
    candidate_indices: Any,
    workers: int,
) -> dict[str, Any]: ...
def capability_actions_batch(
    sessions: list[CapabilitySession],
    engines: list[Engine],
    players: Any,
    workers: int,
) -> dict[str, Any]: ...
def capability_decision_required_batch(
    sessions: list[CapabilitySession],
    engines: list[Engine],
    players: Any,
    workers: int,
) -> Any: ...

class IntentLedgerSession:
    def __init__(self, configuration: dict[str, Any] | None = None) -> None: ...
    def observe(self, engine: Engine, player: int) -> dict[str, Any]: ...
    def select(self, candidate_index: int) -> int: ...
    def action(self, engine: Engine, player: int) -> dict[str, Any]: ...
    def action_numeric(self, engine: Engine, player: int) -> dict[str, Any]: ...
    def decision_required(self, engine: Engine, player: int) -> bool: ...
    def reset(self) -> None: ...
    @property
    def phase(self) -> int: ...
    @property
    def candidate_count(self) -> int: ...
    @property
    def step(self) -> int: ...

class IntentLedgerBatch:
    def __init__(
        self,
        sessions: list[IntentLedgerSession],
        engines: list[Engine],
        players: Any,
        workers: int,
        record_rollout: bool = True,
    ) -> None: ...
    def observe(self, active: Any, maximum_steps: int) -> dict[str, Any]: ...
    def observe_compact(self, active: Any, maximum_steps: int) -> tuple[int, int, int, int]: ...
    def device_auxiliary(self) -> dict[str, Any]: ...
    def write_prepared(
        self,
        candidate_fields: Any,
        candidate_features: Any,
        candidate_mask: Any,
        ledger: Any,
        status: Any,
        work_priorities: Any,
        work_orders: Any,
        work_mask: Any,
        positions: Any,
        market_prefix: Any,
        market_mask: Any,
        phase: Any,
        model_rows: Any,
    ) -> None: ...
    def record_prepared(
        self,
        selected: Any,
        log_probability: Any,
        value: Any,
        turn_index: int,
    ) -> None: ...
    def record_prepared_indexed(
        self,
        selected: Any,
        behavior_offset: int,
        turn_index: int,
    ) -> None: ...
    def replay_transaction(
        self,
        selected: Any,
        selected_fields: Any,
        counts: Any,
        behavior_offset: int,
        turn_index: int,
        maximum_steps: int,
    ) -> int: ...
    def apply_teacher_plans(
        self,
        directive_operations: Any,
        directive_targets: Any,
        directive_items: Any,
        directive_quantities: Any,
        directive_counts: Any,
        market_choices: Any,
        market_items: Any,
        market_quantities: Any,
        market_counts: Any,
        turn_index: int,
        maximum_steps: int,
    ) -> dict[str, Any]: ...
    def export_rollout(self) -> dict[str, Any]: ...
    def export_rollout_buckets(self) -> list[dict[str, Any]]: ...
    def select(self, active: Any, candidate_indices: Any) -> Any: ...
    def reset_transaction(self) -> None: ...
    @property
    def batch_size(self) -> int: ...

def intent_ledger_spec() -> dict[str, Any]: ...
def intent_ledger_observations_batch(
    sessions: list[IntentLedgerSession],
    engines: list[Engine],
    players: Any,
    workers: int,
) -> dict[str, Any]: ...
def intent_ledger_select_batch(
    sessions: list[IntentLedgerSession],
    candidate_indices: Any,
    active: Any,
    workers: int,
) -> Any: ...
def intent_ledger_actions_batch(
    sessions: list[IntentLedgerSession],
    engines: list[Engine],
    players: Any,
    workers: int,
) -> dict[str, Any]: ...

class AtomicEffectSession:
    def __init__(
        self,
        configuration: dict[str, Any] | None = None,
        unit_limit: int = 32,
        maximum_quantity: int = 128,
        task_conditioning: bool = False,
        destination_tasks: bool | None = None,
    ) -> None: ...
    def observe(self, engine: Engine, player: int) -> dict[str, Any]: ...
    def select(self, engine: Engine, player: int, candidate_index: int) -> int: ...
    def action(self, engine: Engine, player: int) -> dict[str, Any]: ...
    def action_numeric(self, engine: Engine, player: int) -> dict[str, Any]: ...
    def decision_required(self, engine: Engine, player: int) -> bool: ...
    def reset(self) -> None: ...
    @property
    def phase(self) -> int: ...
    @property
    def candidate_count(self) -> int: ...
    @property
    def step(self) -> int: ...
    @property
    def unit_limit(self) -> int: ...
    @property
    def maximum_quantity(self) -> int: ...

class AtomicEffectBatch:
    def __init__(
        self,
        sessions: list[AtomicEffectSession],
        engines: list[Engine],
        players: Any,
        workers: int,
    ) -> None: ...
    def observe(self, active: Any) -> dict[str, Any]: ...
    def observe_compact(self, active: Any) -> tuple[int, int, int, int, int, int]: ...
    def write_prepared(
        self,
        candidate_fields: Any,
        candidate_features: Any,
        candidate_mask: Any,
        jobs: Any,
        job_mask: Any,
        work_prefix: Any,
        work_mask: Any,
        market_prefix: Any,
        market_mask: Any,
        previous_action: Any,
        previous_mask: Any,
        phase: Any,
        work_limit: Any,
        model_rows: Any,
    ) -> None: ...
    def write_prepared_prefix(self, prefix: Any, mask: Any) -> None: ...
    def write_prepared_mask(self, candidate_mask: Any, model_rows: Any) -> None: ...
    def advance(
        self,
        selected: Any,
        log_probability: Any,
        value: Any,
        turn_index: int,
    ) -> Any: ...
    def advance_indexed(
        self,
        selected: Any,
        behavior_offset: int,
        turn_index: int,
    ) -> Any: ...
    def actions(self) -> dict[str, Any]: ...
    def export_rollout_buckets(self) -> list[dict[str, Any]]: ...
    def reset_transaction(self) -> None: ...
    @property
    def batch_size(self) -> int: ...

def effect_policy_spec() -> dict[str, Any]: ...
def effect_policy_observations_batch(
    sessions: list[AtomicEffectSession],
    engines: list[Engine],
    players: Any,
    workers: int,
) -> dict[str, Any]: ...
def effect_policy_select_batch(
    sessions: list[AtomicEffectSession],
    engines: list[Engine],
    players: Any,
    candidate_indices: Any,
    active: Any,
    workers: int,
) -> Any: ...
def effect_policy_actions_batch(
    sessions: list[AtomicEffectSession],
    engines: list[Engine],
    players: Any,
    workers: int,
) -> dict[str, Any]: ...

class ConditionalProgramSession:
    def __init__(
        self,
        configuration: dict[str, Any] | None = None,
        unit_limit: int = 65,
    ) -> None: ...
    def reset(self) -> None: ...
    def decision_required(self, engine: Engine, player: int) -> bool: ...
    def observation(self, engine: Engine, player: int) -> dict[str, Any]: ...
    def select(
        self,
        engine: Engine,
        player: int,
        control: int,
        task: int,
        target: int,
        argument: int,
        direction: int,
        raw_operation: int,
        quantity_mode: int,
        exact_quantity: int,
    ) -> None: ...
    def action_numeric(self, engine: Engine, player: int) -> dict[str, Any]: ...
    def decision_required_visible(self, observation: dict[str, Any]) -> bool: ...
    def observation_visible(self, observation: dict[str, Any]) -> dict[str, Any]: ...
    def select_visible(
        self,
        observation: dict[str, Any],
        control: int,
        task: int,
        target: int,
        argument: int,
        direction: int,
        raw_operation: int,
        quantity_mode: int,
        exact_quantity: int,
    ) -> None: ...
    def action_numeric_visible(self, observation: dict[str, Any]) -> dict[str, Any]: ...
    @property
    def phase(self) -> int: ...

def conditional_program_spec(
    configuration: dict[str, Any] | None = None,
    unit_limit: int = 65,
) -> dict[str, Any]: ...
def conditional_program_observations_batch(
    sessions: list[ConditionalProgramSession],
    engines: list[Engine],
    players: Any,
    workers: int,
) -> dict[str, Any]: ...
def conditional_program_select_batch(
    sessions: list[ConditionalProgramSession],
    engines: list[Engine],
    players: Any,
    selections: Any,
    active: Any,
    workers: int,
) -> None: ...
def conditional_program_actions_batch(
    sessions: list[ConditionalProgramSession],
    engines: list[Engine],
    players: Any,
    workers: int,
) -> dict[str, Any]: ...
def conditional_program_compile_teacher_batch(
    sessions: list[ConditionalProgramSession],
    engines: list[Engine],
    players: Any,
    tokens: Any,
    quantities: Any,
    decision_counts: Any,
    unit_counts: Any,
    token_specs: Any,
    workers: int,
) -> dict[str, Any]: ...

class UnitTaskVisibleState: ...

class UnitTaskSession:
    def __init__(
        self,
        configuration: dict[str, Any] | None = None,
        unit_limit: int = 16,
        maximum_quantity: int = 128,
    ) -> None: ...
    def spec(self) -> dict[str, Any]: ...
    def visible_state(self, observation: dict[str, Any]) -> UnitTaskVisibleState: ...
    def observation_visible(self, state: UnitTaskVisibleState) -> dict[str, Any]: ...
    def compact_observation_visible(self, state: UnitTaskVisibleState) -> dict[str, Any]: ...
    def select_visible(
        self,
        state: UnitTaskVisibleState,
        mode: int,
        candidate_index: int,
        quantity: int,
        earliest: int,
        deadline: int,
    ) -> None: ...
    def action_numeric_visible(self, state: UnitTaskVisibleState) -> dict[str, Any]: ...
    def decision_required_visible(self, state: UnitTaskVisibleState) -> bool: ...
    def observation(self, engine: Engine, player: int) -> dict[str, Any]: ...
    def compact_observation(self, engine: Engine, player: int) -> dict[str, Any]: ...
    def select(
        self,
        engine: Engine,
        player: int,
        mode: int,
        candidate_index: int,
        quantity: int,
        earliest: int,
        deadline: int,
    ) -> None: ...
    def action_numeric(self, engine: Engine, player: int) -> dict[str, Any]: ...
    def decision_required(self, engine: Engine, player: int) -> bool: ...
    def reset(self) -> None: ...
    @property
    def candidate_count(self) -> int: ...
    @property
    def prefix_capacity(self) -> int: ...
    @property
    def unit_limit(self) -> int: ...
    @property
    def maximum_quantity(self) -> int: ...

def unit_task_spec(
    configuration: dict[str, Any] | None = None,
    unit_limit: int = 16,
    maximum_quantity: int = 128,
) -> dict[str, Any]: ...
def unit_task_snapshots_batch(
    sessions: list[UnitTaskSession],
    engines: list[Engine],
    players: Any,
    workers: int,
) -> dict[str, Any]: ...
def unit_task_apply_sequences_batch(
    sessions: list[UnitTaskSession],
    engines: list[Engine],
    players: Any,
    selections: Any,
    counts: Any,
    workers: int,
) -> None: ...
def unit_task_observations_batch(
    sessions: list[UnitTaskSession],
    engines: list[Engine],
    players: Any,
    workers: int,
) -> dict[str, Any]: ...
def unit_task_select_batch(
    sessions: list[UnitTaskSession],
    engines: list[Engine],
    players: Any,
    modes: Any,
    candidate_indices: Any,
    quantities: Any,
    earliest: Any,
    deadlines: Any,
    workers: int,
) -> None: ...
def unit_task_actions_batch(
    sessions: list[UnitTaskSession],
    engines: list[Engine],
    players: Any,
    workers: int,
) -> dict[str, Any]: ...
def unit_task_decision_required_batch(
    sessions: list[UnitTaskSession],
    engines: list[Engine],
    players: Any,
    workers: int,
) -> Any: ...

class StructuredPlanSession:
    def __init__(
        self,
        configuration: dict[str, Any] | None = None,
    ) -> None: ...
    def observation(self, engine: Engine, player: int) -> dict[str, Any]: ...
    def apply(
        self,
        engine: Engine,
        player: int,
        mode: int,
        line_operations: Any,
        line_values: Any,
        global_operation: int,
        global_values: Any,
    ) -> None: ...
    def action_numeric(self, engine: Engine, player: int) -> dict[str, Any]: ...
    def decision_required(self, engine: Engine, player: int) -> bool: ...
    def reset(self) -> None: ...
    @property
    def active(self) -> bool: ...
    @property
    def paused(self) -> bool: ...
    @property
    def active_line_count(self) -> int: ...
    @property
    def pending_events(self) -> int: ...
    @property
    def selected_mode(self) -> int: ...

def structured_plan_spec() -> dict[str, Any]: ...
def structured_plan_observations_batch(
    sessions: list[StructuredPlanSession],
    engines: list[Engine],
    players: Any,
    workers: int,
) -> dict[str, Any]: ...
def structured_plan_ready_observations_batch(
    sessions: list[StructuredPlanSession],
    engines: list[Engine],
    players: Any,
    workers: int,
) -> dict[str, Any]: ...
def structured_plan_apply_batch(
    sessions: list[StructuredPlanSession],
    engines: list[Engine],
    players: Any,
    modes: Any,
    line_operations: Any,
    line_values: Any,
    global_operations: Any,
    global_values: Any,
    workers: int,
) -> None: ...
def structured_plan_actions_batch(
    sessions: list[StructuredPlanSession],
    engines: list[Engine],
    players: Any,
    workers: int,
) -> dict[str, Any]: ...
def structured_plan_decision_required_batch(
    sessions: list[StructuredPlanSession],
    engines: list[Engine],
    players: Any,
    workers: int,
) -> Any: ...
def structured_plan_step_self_play_batch(
    engines: list[Engine],
    candidate_players: Any,
    candidate_sessions: list[StructuredPlanSession],
    opponent_sessions: list[StructuredPlanSession],
    workers: int,
) -> Any: ...
def structured_plan_advance_self_play_batch(
    engines: list[Engine],
    candidate_players: Any,
    candidate_sessions: list[StructuredPlanSession],
    opponent_sessions: list[StructuredPlanSession],
    workers: int,
) -> dict[str, Any]: ...
def structured_plan_step_boatlee_v21_batch(
    engines: list[Engine],
    candidate_players: Any,
    candidate_sessions: list[StructuredPlanSession],
    opponent_sessions: Any,
    workers: int,
) -> Any: ...
def structured_plan_step_mugundh_v21_batch(
    engines: list[Engine],
    candidate_players: Any,
    candidate_sessions: list[StructuredPlanSession],
    opponent_sessions: Any,
    workers: int,
) -> Any: ...
def structured_plan_step_kaito_v39_batch(
    engines: list[Engine],
    candidate_players: Any,
    candidate_sessions: list[StructuredPlanSession],
    opponent_sessions: Any,
    workers: int,
) -> Any: ...
def structured_plan_step_kaito_v48_batch(
    engines: list[Engine],
    candidate_players: Any,
    candidate_sessions: list[StructuredPlanSession],
    opponent_sessions: Any,
    workers: int,
) -> Any: ...

class KaitoV48Portfolio:
    def __init__(
        self,
        tokens: Any,
        quantities: Any,
        decision_counts: Any,
        unit_counts: Any,
        maximum_market_orders: int,
    ) -> None: ...

class KaitoV48Session:
    def __init__(self, portfolio: KaitoV48Portfolio) -> None: ...

def kaito_v48_action(
    engine: Engine,
    player: int,
    session: KaitoV48Session,
) -> dict[str, Any]: ...
def kaito_v48_proposed_route(engine: Engine, player: int, route: int) -> int: ...
def engine_step_kaito_v48_batch(
    engines: list[Engine],
    candidate_players: Any,
    sessions: list[KaitoV48Session],
    tokens: Any,
    quantities: Any,
    decision_counts: Any,
    unit_counts: Any,
    workers: int,
) -> Any: ...
def kaito_v48_action_numeric_batch(
    engines: list[Engine],
    players: Any,
    sessions: list[KaitoV48Session],
    tokens: Any,
    quantities: Any,
    decision_counts: Any,
    unit_counts: Any,
    workers: int,
) -> None: ...
def kaito_v48_route_action_numeric_batch(
    engines: list[Engine],
    players: Any,
    sessions: list[KaitoV48Session],
    routes: Any,
    tokens: Any,
    quantities: Any,
    decision_counts: Any,
    unit_counts: Any,
    workers: int,
) -> None: ...

class KaitoV39Portfolio:
    def __init__(
        self,
        tokens: Any,
        quantities: Any,
        decision_counts: Any,
        unit_counts: Any,
        parts_layout: Any,
        parts_numeric: Any,
        parts_actor_lengths: Any,
        parts_unlocks: Any,
        parts_shop_counts: Any,
        parts_seats: Any,
        nested_indices: Any,
        nested_margins: Any,
        fallback_indices: Any,
        fallback_margins: Any,
        stage1_indices: Any,
        stage1_margins: Any,
        stage2_indices: Any,
        stage2_margins: Any,
        maximum_market_orders: int,
    ) -> None: ...

class KaitoV39Session:
    def __init__(self, portfolio: KaitoV39Portfolio) -> None: ...

def kaito_v39_action(
    engine: Engine,
    player: int,
    session: KaitoV39Session,
) -> dict[str, Any]: ...
def engine_step_kaito_v39_batch(
    engines: list[Engine],
    candidate_players: Any,
    sessions: list[KaitoV39Session],
    tokens: Any,
    quantities: Any,
    decision_counts: Any,
    unit_counts: Any,
    workers: int,
) -> Any: ...

class MugundhV21Portfolio:
    def __init__(
        self,
        tokens: Any,
        quantities: Any,
        decision_counts: Any,
        unit_counts: Any,
    ) -> None: ...

class MugundhV21Session:
    def __init__(self, portfolio: MugundhV21Portfolio) -> None: ...

def mugundh_v21_action(
    engine: Engine,
    player: int,
    session: MugundhV21Session,
) -> dict[str, Any]: ...
def engine_step_mugundh_v21_batch(
    engines: list[Engine],
    candidate_players: Any,
    sessions: list[MugundhV21Session],
    tokens: Any,
    quantities: Any,
    decision_counts: Any,
    unit_counts: Any,
    workers: int,
) -> Any: ...

class NativeOpponentPortfolio:
    def __init__(self, data: dict[str, Any]) -> None: ...

class NativeOpponentSession:
    def __init__(self, portfolio: NativeOpponentPortfolio, maximum_orders: int) -> None: ...
    def clone(self) -> NativeOpponentSession: ...

def native_opponent_action(
    engine: Engine, player: int, session: NativeOpponentSession
) -> dict[str, Any]: ...
def native_opponent_diagnostics(session: NativeOpponentSession) -> dict[str, Any]: ...
def native_compiled_closure_lifetimes() -> bool: ...
def native_compiled_dictionary_get() -> bool: ...
def native_compiled_function_profile() -> list[dict[str, Any]]: ...
def canonical_opponent_action(action: dict[str, Any], maximum_orders: int) -> dict[str, Any]: ...
def engine_step_native_opponent_batch(
    engines: list[Engine],
    candidate_players: Any,
    sessions: list[NativeOpponentSession],
    tokens: Any,
    quantities: Any,
    decision_counts: Any,
    unit_counts: Any,
    workers: int,
) -> Any: ...

class BoatleeV21Portfolio:
    def __init__(
        self,
        tokens: Any,
        quantities: Any,
        decision_counts: Any,
        unit_counts: Any,
        maximum_market_orders: int,
    ) -> None: ...

class BoatleeV21Session:
    def __init__(self, portfolio: BoatleeV21Portfolio) -> None: ...

def boatlee_v21_action(
    engine: Engine,
    player: int,
    session: BoatleeV21Session,
) -> dict[str, Any]: ...
def engine_step_boatlee_v21_batch(
    engines: list[Engine],
    candidate_players: Any,
    sessions: list[BoatleeV21Session],
    tokens: Any,
    quantities: Any,
    decision_counts: Any,
    unit_counts: Any,
    workers: int,
) -> Any: ...

class EngineBatch:
    def __init__(self, seeds: Any, configuration: dict[str, Any] | None = None) -> None: ...
    def reset(self, seeds: Any) -> None: ...
    def encode(self, unit_limit: int) -> tuple[Any, Any, Any]: ...
    def step(
        self,
        tokens: Any,
        quantities: Any,
        decision_counts: Any,
        unit_counts: Any,
    ) -> Any: ...
    def money(self) -> Any: ...
    @property
    def size(self) -> int: ...

class NativeOfficialActionBuilder:
    def __init__(
        self,
        observation: dict[str, Any],
        configuration: dict[str, Any] | None = None,
    ) -> None: ...
    def choices(self) -> dict[str, Any]: ...
    def select(self, key: str, quantity: int | None = None) -> None: ...
    def action(self) -> dict[str, Any]: ...
    def local_state(self) -> dict[str, Any]: ...
    @property
    def spec_version(self) -> str: ...

def game_rules() -> dict[str, Any]: ...
def compile_unit_prefix_from_obs(
    obs: dict[str, Any],
    configuration: dict[str, Any] | None,
    requested_action: dict[str, Any],
) -> dict[str, Any]: ...
def compile_market_from_post_unit(
    obs: dict[str, Any],
    configuration: dict[str, Any] | None,
    post_unit: dict[str, Any],
    requested_market: Any,
) -> dict[str, Any]: ...

class NativePlanner:
    spec_version: int
    def __init__(
        self,
        configuration: dict[str, Any] | None = None,
        options: dict[str, Any] | None = None,
    ) -> None: ...
    def plan(self, observation: dict[str, Any]) -> dict[str, Any]: ...
    def plan_compact(self, observation: dict[str, Any]) -> dict[str, Any]: ...
    def act(self, observation: dict[str, Any]) -> dict[str, Any]: ...
    def reset(self) -> None: ...

def parallel_spec() -> dict[str, Any]: ...

class ContractSession:
    def encode_replay_into(
        self, steps: Any, seat: int, observations: Any, actions: Any
    ) -> None: ...
    def __init__(self, configuration: dict[str, Any], units: int) -> None: ...
    def update(self, observation: dict[str, object]) -> None: ...
    def observe_into(self, output: Any) -> None: ...
    def action(self, plan: Any) -> dict[str, object]: ...
    def set_program(self, plan: Any, capacity: int, quantities: list[int]) -> None: ...
    def program_action(self) -> dict[str, object]: ...

class ParallelBatch:
    def fork(self, parents: Any) -> ParallelBatch: ...
    def replay_prefixes(self, prefixes: list[Any]) -> None: ...
    def __init__(
        self,
        configuration: dict[str, Any],
        seeds: list[int],
        seats: list[int],
        opponent_ids: list[str],
        opponents: list[Any],
        teachers: list[Any],
        units: int,
        workers: int,
        quantities: list[int],
    ) -> None: ...
    def observe_into(self, output: Any) -> None: ...
    def observe_selfplay_into(self, output: Any) -> None: ...
    def teacher_into(self, labels: Any) -> None: ...
    def step(self, actions: Any) -> None: ...
    def advance(self, contracts: Any, turns: int) -> None: ...
    def advance_selfplay(self, contracts: Any, turns: int) -> None: ...
    def advance_programs(
        self,
        plans: Any,
        turns: int,
        capacity: int,
        selfplay: bool = False,
    ) -> None: ...
    def cash(self) -> Any: ...
    def observation(self, lane: int, player: int = -1) -> dict[str, Any]: ...
    def action(self, lane: int, actions: Any) -> dict[str, Any]: ...
    def contract_action(self, lane: int, contracts: Any, player: int = -1) -> dict[str, Any]: ...
    @property
    def features(self) -> int: ...
    @property
    def entity_features(self) -> int: ...
    @property
    def slots(self) -> int: ...
    @property
    def step_index(self) -> int: ...
    @property
    def completed_games(self) -> int: ...
    @property
    def transitions(self) -> int: ...
