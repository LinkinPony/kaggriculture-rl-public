"""Semantic teacher marginalization for the strategy migration."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from contextlib import nullcontext
from dataclasses import dataclass
from typing import Any, cast

import numpy as np
import torch
from torch import Tensor

from kagg_revue.policy.economics.transition import apply_selection
from kagg_revue.policy.model import TurnContext, TurnPolicyNet
from kagg_revue.policy.transformer import AttentionCache, HistoryState
from kagg_revue.policy.vocabulary import LEGACY_ACTIONS


@dataclass
class _SeatState:
    """Teacher/student recurrent state and their distinct action histories."""

    teacher_history: HistoryState | None
    student_history: HistoryState | None
    student_strategy: Tensor | None
    teacher_actions: Tensor
    teacher_quantities: Tensor
    teacher_mask: Tensor
    student_actions: Tensor
    student_quantities: Tensor
    student_mask: Tensor


def _history_context(
    actor: TurnPolicyNet,
    board: Tensor,
    units: Tensor,
    globals_: Tensor,
    previous_actions: Tensor,
    previous_quantities: Tensor,
    previous_mask: Tensor,
    history: HistoryState | None,
    economic_state: Tensor,
) -> tuple[TurnContext, HistoryState, Tensor]:
    """Build the legacy decoder memory before inserting any skill token."""
    if actor.economics is None:
        raise ValueError("semantic distillation requires the source economic compiler")
    economic = actor.economics.turn_features(
        economic_state,
        globals_.detach().cpu(),
    ).to(board.device)
    scene = actor.scene(
        board,
        units,
        globals_,
        previous_actions,
        previous_quantities,
        previous_mask,
        economic_features=economic,
    )
    temporal, next_history = actor.temporal.step(scene.summary[:, None], history)
    memory = torch.cat((temporal, scene.memory), dim=1)
    mask = torch.cat(
        (
            torch.ones((1, 1), dtype=torch.bool, device=board.device),
            scene.memory_mask,
        ),
        dim=1,
    )
    return TurnContext(memory=memory, memory_mask=mask), next_history, temporal[:, 0]


def _skill_context(
    actor: TurnPolicyNet,
    base: TurnContext,
) -> tuple[TurnContext, Tensor]:
    """Enumerate every source skill and return its causal prior."""
    if actor.skills is None:
        raise ValueError("semantic distillation source has no latent skills")
    skills = actor.architecture.skill_tokens
    memory = base.memory.expand(skills, -1, -1)
    mask = base.memory_mask.expand(skills, -1)
    embeddings = actor.skills.codebook.weight
    conditioned, conditioned_mask = actor._condition_memory(
        memory,
        mask,
        embeddings,
    )
    prior = torch.softmax(actor.skills.prior(base.memory[:, 0]).float(), dim=-1)[0]
    return TurnContext(memory=conditioned, memory_mask=conditioned_mask), prior


def _semantic_maps(
    source_keys: Sequence[str], target_keys: Sequence[str]
) -> tuple[Tensor, tuple[tuple[int, ...], ...], tuple[int, ...]]:
    target_by_key = {key: index for index, key in enumerate(target_keys)}
    old_to_new = []
    sources: list[list[int]] = [[] for _ in target_keys]
    explicit = []
    source_by_key = {key: index for index, key in enumerate(source_keys)}
    for old_index, key in enumerate(source_keys):
        semantic = key.replace("PICKUP_DEFAULT:", "PICKUP:").replace(
            "PLACE_DEFAULT:", "PLACE:"
        )
        try:
            new_index = target_by_key[semantic]
        except KeyError as error:
            raise ValueError(f"source action has no target semantic: {key}") from error
        old_to_new.append(new_index)
        sources[new_index].append(old_index)
    for key in target_keys:
        try:
            explicit.append(source_by_key[key])
        except KeyError as error:
            raise ValueError(f"target action has no explicit source row: {key}") from error
    return (
        torch.tensor(old_to_new, dtype=torch.long),
        tuple(tuple(indices) for indices in sources),
        tuple(explicit),
    )


def _old_legal(new_legal: Tensor, old_to_new: Tensor) -> Tensor:
    return new_legal.index_select(0, old_to_new.to(new_legal.device))


def _detach_history(history: HistoryState) -> HistoryState:
    layers = tuple(
        None
        if cache is None
        else AttentionCache(key=cache.key.detach(), value=cache.value.detach())
        for cache in history.layers
    )
    return HistoryState(layers=layers, position=history.position)


def _semantic_action_distribution(
    probabilities: Tensor,
    posterior: Tensor,
    old_to_new: Tensor,
    target_actions: int,
) -> tuple[Tensor, Tensor]:
    per_skill = probabilities.new_zeros(probabilities.shape[0], target_actions)
    per_skill.scatter_add_(
        1,
        old_to_new[None].expand(probabilities.shape[0], -1),
        probabilities,
    )
    return (posterior[:, None] * per_skill).sum(dim=0), per_skill


def _kl(target: Tensor, log_probabilities: Tensor) -> Tensor:
    support = target > 0
    supported_target = target[support]
    return (
        supported_target
        * (supported_target.log() - log_probabilities[support])
    ).sum()


def _quantity_target(
    teacher: TurnPolicyNet,
    teacher_hidden: Tensor,
    teacher_probabilities: Tensor,
    posterior: Tensor,
    source_tokens: tuple[int, ...],
    source_keys: Sequence[str],
    economic_state: Tensor,
) -> tuple[Tensor, Tensor]:
    """Return the alias- and skill-marginal quantity law and per-skill joint law."""
    if teacher.economics is None:
        raise ValueError("teacher economic compiler is absent")
    skills = teacher_hidden.shape[0]
    quantities = teacher.architecture.maximum_quantity
    joint = teacher_hidden.new_zeros(quantities, dtype=torch.float32)
    per_skill_joint = teacher_hidden.new_zeros(skills, quantities, dtype=torch.float32)
    for source_token in source_tokens:
        action_probability = teacher_probabilities[:, source_token].float()
        key = source_keys[source_token]
        if "_DEFAULT:" in key:
            distribution = teacher_hidden.new_zeros(skills, quantities, dtype=torch.float32)
            distribution[:, 0] = 1.0
        else:
            token = torch.full(
                (skills,), source_token, dtype=torch.long, device=teacher_hidden.device
            )
            facts = teacher.economics.quantity_features(
                economic_state,
                torch.tensor([source_token], dtype=torch.long),
            ).to(teacher_hidden.device)
            logits = teacher.action.quantity_logits(
                teacher_hidden,
                token,
                None,
                facts.expand(skills, -1, -1),
            )
            distribution = torch.softmax(logits.float(), dim=-1)
        contribution = action_probability[:, None] * distribution
        per_skill_joint = per_skill_joint + contribution
        joint = joint + (posterior[:, None] * contribution).sum(dim=0)
    total = joint.sum().clamp_min(torch.finfo(joint.dtype).tiny)
    return joint / total, per_skill_joint


def _seat_state(teacher: TurnPolicyNet, student: TurnPolicyNet, device: torch.device) -> _SeatState:
    return _SeatState(
        teacher_history=None,
        student_history=None,
        student_strategy=None,
        teacher_actions=torch.zeros(
            (1, teacher.architecture.max_decisions), dtype=torch.long, device=device
        ),
        teacher_quantities=torch.zeros(
            (1, teacher.architecture.max_decisions), dtype=torch.long, device=device
        ),
        teacher_mask=torch.zeros(
            (1, teacher.architecture.max_decisions), dtype=torch.bool, device=device
        ),
        student_actions=torch.zeros(
            (1, student.architecture.max_decisions), dtype=torch.long, device=device
        ),
        student_quantities=torch.zeros(
            (1, student.architecture.max_decisions), dtype=torch.long, device=device
        ),
        student_mask=torch.zeros(
            (1, student.architecture.max_decisions), dtype=torch.bool, device=device
        ),
    )


def semantic_distill(
    teacher: TurnPolicyNet,
    student: TurnPolicyNet,
    source_keys: Sequence[str],
    target_keys: Sequence[str],
    environment: Mapping[str, object],
    *,
    games: int,
    turns_per_game: int,
    learning_rate: float,
    seed: int,
    device: torch.device,
) -> dict[str, object]:
    """Distill skill/alias marginals on source-teacher full-rule on-policy states."""
    if teacher.architecture.skill_tokens < 2 or student.architecture.skill_tokens:
        raise ValueError("semantic distillation requires skilled teacher and skill-free student")
    if student.architecture.strategy_tokens < 2:
        raise ValueError("semantic distillation student lacks recurrent strategy")
    if teacher.economics is None or student.economics is None:
        raise ValueError("semantic distillation requires both economic compilers")
    if games < 1 or turns_per_game < 1:
        raise ValueError("semantic distillation coverage must be positive")

    from kagg_revue.native import _revue_native as native

    codec = cast(Mapping[str, Any], native.action_codec_spec())
    has_quantity = torch.as_tensor(codec["has_quantity"], dtype=torch.bool, device=device)
    old_to_new, sources_by_target, explicit_source = _semantic_maps(
        source_keys, target_keys
    )
    old_to_new_device = old_to_new.to(device)
    old_has_quantity = torch.tensor(
        [
            "_DEFAULT:" not in key
            and (
                key.startswith("UNIT:PICKUP:")
                or key.startswith("UNIT:PLACE:")
                or key.startswith("MARKET:SELL:")
                or key.startswith("MARKET:BUY_SEED:")
                or key.startswith("MARKET:BUY_PRODUCT:")
                or key.startswith("MARKET:BUY_ANIMAL:")
            )
            for key in source_keys
        ],
        dtype=torch.bool,
    )
    teacher.to(device).eval().requires_grad_(False)
    student.to(device).train()
    optimizer = torch.optim.AdamW(student.parameters(), lr=learning_rate)
    generator = torch.Generator(device=device).manual_seed(seed)
    action_kl_values: list[float] = []
    quantity_kl_values: list[float] = []
    game_kl_values: list[float] = []
    decisions = 0
    alias_mass = 0.0
    inventory_order_nonzero = 0
    extra_unit_turns = 0
    new_position_decisions = 0

    autocast = (
        torch.autocast(device_type="cuda", dtype=torch.bfloat16)
        if device.type == "cuda"
        else nullcontext()
    )
    for game_index in range(games):
        engine = native.Engine(seed + game_index, dict(environment))
        seats = [_seat_state(teacher, student, device) for _ in range(2)]
        game_losses: list[Tensor] = []
        game_metric = 0.0
        optimizer.zero_grad(set_to_none=True)
        for _ in range(turns_per_game):
            if engine.done:
                break
            completed_actions = []
            for seat, recurrent in enumerate(seats):
                teacher_session = engine.policy_session(seat, 16)
                student_session = engine.policy_session(seat, 32)
                teacher_board_np, teacher_units_np, teacher_global_np = teacher_session.encode()
                student_board_np, student_units_np, student_global_np = student_session.encode()
                teacher_board = torch.as_tensor(
                    np.asarray(teacher_board_np), device=device
                )[None]
                teacher_units = torch.as_tensor(
                    np.asarray(teacher_units_np)[..., :48], device=device
                )[None]
                teacher_global = torch.as_tensor(
                    np.asarray(teacher_global_np), device=device
                )[None]
                student_board = torch.as_tensor(
                    np.asarray(student_board_np), device=device
                )[None]
                student_units = torch.as_tensor(
                    np.asarray(student_units_np), device=device
                )[None]
                student_global = torch.as_tensor(
                    np.asarray(student_global_np), device=device
                )[None]
                inventory_order_nonzero += int(
                    np.count_nonzero(np.asarray(student_units_np)[0, :, 48:60])
                )
                own_units = int(np.count_nonzero(np.asarray(student_units_np)[0, :, 0] > 0.5))
                extra_unit_turns += int(own_units > 16)
                teacher_economic = torch.as_tensor(
                    np.asarray(teacher_session.gpu_state()), dtype=torch.int64
                )[None]
                student_economic = torch.as_tensor(
                    np.asarray(student_session.gpu_state()),
                    dtype=torch.int64,
                    device=device,
                )[None]

                with torch.no_grad(), autocast:
                    base_context, teacher_history, history_token = _history_context(
                        teacher,
                        teacher_board,
                        teacher_units,
                        teacher_global,
                        recurrent.teacher_actions,
                        recurrent.teacher_quantities,
                        recurrent.teacher_mask,
                        recurrent.teacher_history,
                        teacher_economic,
                    )
                    teacher_context, posterior = _skill_context(teacher, base_context)
                    teacher_action_state = teacher.action.initial_state(teacher_context)
                recurrent.teacher_history = teacher_history
                with autocast:
                    (
                        student_context,
                        student_history,
                        student_strategy,
                        _,
                    ) = student.start_turn(
                        student_board,
                        student_units,
                        student_global,
                        recurrent.student_actions,
                        recurrent.student_quantities,
                        recurrent.student_mask,
                        recurrent.student_history,
                        economic_state=student_economic,
                        strategy_state=recurrent.student_strategy,
                    )
                    student_action_state = student.action.initial_state(student_context)
                recurrent.student_history = student_history
                recurrent.student_strategy = student_strategy
                selected_teacher: list[int] = []
                selected_student: list[int] = []
                selected_quantities: list[int] = []
                previous_teacher: Tensor | None = None
                previous_student: Tensor | None = None
                previous_quantity: Tensor | None = None
                decision = 0
                while int(teacher_session.phase) != 2:
                    if decision >= teacher.architecture.max_decisions:
                        raise RuntimeError("teacher decision capacity was exceeded")
                    phase = int(teacher_session.phase)
                    if phase != int(student_session.phase):
                        raise RuntimeError("teacher/student policy sessions diverged")
                    teacher_phase_cpu = torch.tensor([phase], dtype=torch.long)
                    teacher_prefix = teacher.economics.prefix_features(
                        teacher_economic, teacher_phase_cpu
                    ).to(device)
                    teacher_candidates = teacher.economics.candidate_features(
                        teacher_economic, teacher_phase_cpu
                    ).to(device)
                    student_phase = torch.tensor([phase], dtype=torch.long, device=device)
                    student_prefix = student.economics.prefix_features(
                        student_economic, student_phase
                    )
                    student_candidates = student.economics.candidate_features(
                        student_economic, student_phase
                    )
                    with torch.no_grad(), autocast:
                        teacher_logits, teacher_hidden, teacher_action_state = (
                            teacher.action.next_cached(
                                previous_teacher,
                                previous_quantity,
                                teacher_phase_cpu.to(device).expand(
                                    teacher.architecture.skill_tokens
                                ),
                                teacher_context,
                                teacher_action_state,
                                economic_prefix_facts=teacher_prefix.expand(
                                    teacher.architecture.skill_tokens, -1
                                ),
                                economic_candidate_facts=teacher_candidates.expand(
                                    teacher.architecture.skill_tokens, -1, -1
                                ),
                            )
                        )
                    with autocast:
                        student_logits, student_hidden, student_action_state = (
                            student.action.next_cached(
                                previous_student,
                                previous_quantity,
                                student_phase,
                                student_context,
                                student_action_state,
                                economic_prefix_facts=student_prefix,
                                economic_candidate_facts=student_candidates,
                            )
                        )
                    teacher_new_legal = torch.as_tensor(
                        np.asarray(teacher_session.legal_mask()),
                        dtype=torch.bool,
                        device=device,
                    )
                    student_legal = torch.as_tensor(
                        np.asarray(student_session.legal_mask()),
                        dtype=torch.bool,
                        device=device,
                    )
                    teacher_legal = _old_legal(
                        teacher_new_legal, old_to_new_device
                    )
                    teacher_log_probabilities = torch.log_softmax(
                        teacher_logits.float().masked_fill(
                            ~teacher_legal[None], -torch.inf
                        ),
                        dim=-1,
                    )
                    teacher_probabilities = teacher_log_probabilities.exp()
                    target_action, per_skill_semantic = _semantic_action_distribution(
                        teacher_probabilities,
                        posterior,
                        old_to_new_device,
                        student.architecture.action_tokens,
                    )
                    target_action = target_action * student_legal.float()
                    target_action = target_action / target_action.sum().clamp_min(
                        torch.finfo(target_action.dtype).tiny
                    )
                    student_log_probabilities = torch.log_softmax(
                        student_logits[0].float().masked_fill(
                            ~student_legal, -torch.inf
                        ),
                        dim=-1,
                    )
                    action_kl = _kl(target_action.detach(), student_log_probabilities)
                    game_losses.append(action_kl)
                    action_kl_values.append(float(action_kl.detach().item()))
                    game_metric += float(action_kl.detach().item())
                    new_token = int(
                        torch.multinomial(
                            target_action,
                            1,
                            generator=generator,
                        ).item()
                    )
                    source_tokens = sources_by_target[new_token]
                    alias_mass += float(
                        sum(
                            teacher_probabilities[:, token]
                            .mul(posterior)
                            .sum()
                            .item()
                            for token in source_tokens
                            if "_DEFAULT:" in source_keys[token]
                        )
                    )
                    quantity = 0
                    likelihood = per_skill_semantic[:, new_token]
                    if bool(has_quantity[new_token]):
                        quantity_target, per_skill_joint = _quantity_target(
                            teacher,
                            teacher_hidden,
                            teacher_probabilities,
                            posterior,
                            source_tokens,
                            source_keys,
                            teacher_economic,
                        )
                        student_quantity_facts = student.economics.quantity_features(
                            student_economic,
                            torch.tensor([new_token], dtype=torch.long, device=device),
                        )
                        with autocast:
                            student_quantity_logits = student.action.quantity_logits(
                                student_hidden,
                                torch.tensor(
                                    [new_token], dtype=torch.long, device=device
                                ),
                                None,
                                student_quantity_facts,
                            )[0]
                        student_quantity_log = torch.log_softmax(
                            student_quantity_logits.float(), dim=-1
                        )
                        quantity_kl = _kl(
                            quantity_target.detach(), student_quantity_log
                        )
                        game_losses.append(quantity_kl)
                        quantity_kl_values.append(float(quantity_kl.detach().item()))
                        game_metric += float(quantity_kl.detach().item())
                        quantity_index = int(
                            torch.multinomial(
                                quantity_target,
                                1,
                                generator=generator,
                            ).item()
                        )
                        quantity = quantity_index + 1
                        likelihood = per_skill_joint[:, quantity_index]
                    posterior = posterior * likelihood.clamp_min(
                        torch.finfo(posterior.dtype).tiny
                    )
                    posterior = posterior / posterior.sum().clamp_min(
                        torch.finfo(posterior.dtype).tiny
                    )
                    old_token = explicit_source[new_token]
                    if bool(old_has_quantity[old_token]) and quantity < 1:
                        raise RuntimeError("explicit teacher quantity disappeared")
                    teacher_session.select(new_token, quantity)
                    student_session.select(new_token, quantity)
                    old_quantity = quantity if bool(old_has_quantity[old_token]) else 0
                    apply_selection(
                        teacher_economic,
                        torch.tensor([old_token], dtype=torch.long),
                        torch.tensor([old_quantity], dtype=torch.long),
                        torch.ones(1, dtype=torch.bool),
                        teacher.economics.layout,
                        LEGACY_ACTIONS,
                    )
                    apply_selection(
                        student_economic,
                        torch.tensor([new_token], dtype=torch.long, device=device),
                        torch.tensor([quantity], dtype=torch.long, device=device),
                        torch.ones(1, dtype=torch.bool, device=device),
                        student.economics.layout,
                    )
                    previous_teacher = torch.full(
                        (teacher.architecture.skill_tokens,),
                        old_token,
                        dtype=torch.long,
                        device=device,
                    )
                    previous_student = torch.tensor(
                        [new_token], dtype=torch.long, device=device
                    )
                    previous_quantity = torch.tensor(
                        [quantity], dtype=torch.long, device=device
                    )
                    selected_teacher.append(old_token)
                    selected_student.append(new_token)
                    selected_quantities.append(quantity)
                    decisions += 1
                    new_position_decisions += int(decision >= 26)
                    decision += 1
                recurrent.teacher_actions.zero_()
                recurrent.teacher_quantities.zero_()
                recurrent.teacher_mask.zero_()
                recurrent.student_actions.zero_()
                recurrent.student_quantities.zero_()
                recurrent.student_mask.zero_()
                teacher_count = len(selected_teacher)
                student_count = len(selected_student)
                recurrent.teacher_actions[0, :teacher_count] = torch.tensor(
                    selected_teacher, dtype=torch.long, device=device
                )
                recurrent.teacher_quantities[0, :teacher_count] = torch.tensor(
                    selected_quantities, dtype=torch.long, device=device
                )
                recurrent.teacher_mask[0, :teacher_count] = True
                recurrent.student_actions[0, :student_count] = torch.tensor(
                    selected_student, dtype=torch.long, device=device
                )
                recurrent.student_quantities[0, :student_count] = torch.tensor(
                    selected_quantities, dtype=torch.long, device=device
                )
                recurrent.student_mask[0, :student_count] = True
                completed_actions.append(teacher_session.action())
            engine.step(completed_actions[0], completed_actions[1])
        if not game_losses:
            raise RuntimeError("semantic distillation collected no decisions")
        loss = torch.stack(game_losses).mean()
        torch.autograd.backward(loss)
        torch.nn.utils.clip_grad_norm_(student.parameters(), 1.0)
        optimizer.step()
        game_kl_values.append(game_metric / len(game_losses))
        for recurrent in seats:
            if recurrent.student_history is not None:
                recurrent.student_history = _detach_history(recurrent.student_history)
            if recurrent.student_strategy is not None:
                recurrent.student_strategy = recurrent.student_strategy.detach()

    return {
        "status": "completed",
        "teacher_policy": "source checkpoint on-policy in the complete native rules engine",
        "skill_marginalization": "all source skills enumerated with causal posterior updates",
        "alias_marginalization": "DEFAULT probability merged; DEFAULT quantity is one",
        "games": games,
        "turns_per_game": turns_per_game,
        "full_recurrent_unroll_turns": turns_per_game,
        "decisions": decisions,
        "mean_action_kl": sum(action_kl_values) / len(action_kl_values),
        "mean_quantity_kl": (
            sum(quantity_kl_values) / len(quantity_kl_values)
            if quantity_kl_values
            else 0.0
        ),
        "first_game_mean_kl": game_kl_values[0],
        "last_game_mean_kl": game_kl_values[-1],
        "default_alias_probability_mass": alias_mass / decisions,
        "inventory_order_nonzero_features": inventory_order_nonzero,
        "extra_unit_turns": extra_unit_turns,
        "new_decision_position_count": new_position_decisions,
        "extra_unit_supervision": "none claimed; subsequent full-rule PPO is authoritative",
    }


__all__ = ["semantic_distill"]
