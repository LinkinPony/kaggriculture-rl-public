import torch

from kagg_revue.rl.distributed import DistributedContext
from kagg_revue.rl.effects.coordination import (
    aggregate_rollouts,
    distributed_rng_state,
    local_population_jobs,
    outcome_metrics,
    rank_rng_state,
)
from kagg_revue.rl.effects.fleet import shard_effect_jobs


def _diagnostics(*, games: int, episodes: int, elapsed: float) -> dict[str, object]:
    return {
        "physical_games": games,
        "episodes": episodes,
        "official_turns": episodes * 2,
        "policy_factors": episodes * 3,
        "factors": episodes * 4,
        "native_rollout_buckets": 2,
        "graph_variants_created": 1,
        "actor_streams": 1,
        "maximum_batched_actor_seconds": 0.2,
        "encode_seconds": 0.3,
        "native_observation_seconds": 0.4,
        "inference_seconds": 0.5,
        "native_transition_seconds": 0.6,
        "action_compilation_seconds": 0.7,
        "environment_seconds": 0.8,
        "finalization_seconds": 0.9,
        "turn_graph_capture_seconds": 1.0,
        "graph_capture_seconds": 1.1,
        "elapsed_seconds": elapsed,
    }


def test_effect_jobs_remain_complete_across_ranks_and_actor_streams() -> None:
    seeds = tuple(range(8))
    contexts = tuple(
        DistributedContext(
            rank=rank,
            world_size=2,
            device=torch.device("cpu"),
            cpu_affinity=(),
        )
        for rank in range(2)
    )
    rank_jobs = tuple(
        local_population_jobs(
            seeds,
            {"self_play": 0.5, "kaito_v48": 0.5},
            context,
            sampling_seed=17,
        )
        for context in contexts
    )
    assert {seed for jobs in rank_jobs for seed, _seat, _opponent in jobs} == set(seeds)
    assert not ({job[0] for job in rank_jobs[0]} & {job[0] for job in rank_jobs[1]})

    for jobs in rank_jobs:
        shards = shard_effect_jobs(jobs, 2)
        for seed in {job[0] for job in jobs}:
            containing = [shard for shard in shards if any(job[0] == seed for job in shard)]
            assert len(containing) == 1
            selected = [job for job in containing[0] if job[0] == seed]
            if selected[0][2] != "self_play":
                assert {job[1] for job in selected} == {0, 1}


def test_effect_rollout_aggregation_uses_rank_critical_path_and_direct_outcomes() -> None:
    payloads = (
        {
            "rank": 0,
            "device": "cuda:0",
            "diagnostics": _diagnostics(games=1, episodes=2, elapsed=3.0),
            "games": [
                {
                    "episode_id": "self_play:1:0",
                    "opponent_id": "self_play",
                    "seed": 1,
                    "seat": 0,
                    "outcome": 1,
                    "terminal_cash": 9.0,
                    "opponent_cash": 4.0,
                },
                {
                    "episode_id": "self_play:1:1",
                    "opponent_id": "self_play",
                    "seed": 1,
                    "seat": 1,
                    "outcome": -1,
                    "terminal_cash": 4.0,
                    "opponent_cash": 9.0,
                },
            ],
        },
        {
            "rank": 1,
            "device": "cuda:1",
            "diagnostics": _diagnostics(games=2, episodes=2, elapsed=5.0),
            "games": [
                {
                    "episode_id": "kaito_v48:2:0",
                    "opponent_id": "kaito_v48",
                    "seed": 2,
                    "seat": 0,
                    "outcome": 0,
                    "terminal_cash": 6.0,
                    "opponent_cash": 6.0,
                },
                {
                    "episode_id": "kaito_v48:2:1",
                    "opponent_id": "kaito_v48",
                    "seed": 2,
                    "seat": 1,
                    "outcome": 1,
                    "terminal_cash": 8.0,
                    "opponent_cash": 5.0,
                },
            ],
        },
    )

    diagnostics, games = aggregate_rollouts(payloads)
    metrics = outcome_metrics(games)

    assert diagnostics["physical_games"] == 3
    assert diagnostics["episodes"] == 4
    assert diagnostics["elapsed_seconds"] == 5.0
    assert diagnostics["inference_seconds"] == 0.5
    assert metrics["wins"] == 2
    assert metrics["ties"] == 1
    assert metrics["losses"] == 1
    opponents = metrics["opponents"]
    assert isinstance(opponents, dict)
    assert opponents["kaito_v48"]["games"] == 2


def test_effect_distributed_rng_selects_rank_state() -> None:
    payload = distributed_rng_state(({"rank": 0}, {"rank": 1}), ("cuda:0", "cuda:1"))
    context = DistributedContext(
        rank=1,
        world_size=2,
        device=torch.device("cpu"),
        cpu_affinity=(),
    )

    assert rank_rng_state(payload, context) == {"rank": 1}
