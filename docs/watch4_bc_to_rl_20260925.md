# Latest BC → PPO from Four Sides, inheriting complete s82001 history pool

**Next state:** Stopped normally as per user request at **2026-09-25 15:01:07 UTC** at
**U101 / 12,928 games**, complete state preserved. Subsequently [resume s82001 original RL](s82001_resume_v5b_20260925.md).
The original startup and confirmation records of this run are retained below.

Stop the current four-way BC according to user requirements, restore RL using its latest Actor, inherit the complete activity history pool from the previous round's RL, and treat the final strategy of the previous round's RL itself as a frozen opponent.

## Latest Weights and Stop Status

`derived-v5b-m384-u2349-watch4-bc100-20260925-s88001` stopped normally on **2026-09-25 13:46:38 UTC** at the **5,992nd batch / 34,329,530th supervision turn**.
After completing 25 epochs, it entered epoch 26; using the latest weights at stop time, including 17 batches of updates completed in epoch 26. Original BC optimizer, dual rank RNG, epoch weights, and records are preserved.

Origin: `pretraining/shard-005992.pt`, SHA256:
`76d46aa15b202a526581e5fbffa22f31a5ee521b1e07093f73a8bbd5ca9bddfc`.
The **351 tensors** of the new RL initial Actor are bit-identical to this checkpoint, with the same layout of complete v5b / 384 turn memory.
New Critic, PPO Adam, RNG, and this learner's PFSP statistics are created.
See [Stop Verification](../outputs/analysis/watch4-bc-to-rl-20260925/stop-verification.json) and
[Origin Verification](../outputs/analysis/watch4-bc-to-rl-20260925/initialization-verification.json).

## Complete History Pool

The previous round RL was `agronomy-v4-m384-dsm-games-ppo50-20260924-s82001`,
stopped at **U2349 / 300,672 games**, ledger SHA256:
`b5d894d49e51b9fddf3df68a366f81f11549fcaac7d9ad1d85514c952a72e5a8`.

Fully inherits its **341 active strategies**: 304 with existing external history, and 37 originating from its own starting point/snapshot.
Adds the final **U2349** not present in the active pool, totaling **342 external strategies**;
Plus the new BC starting point, totaling **343 strategies + 7 native C++ scripts**.
The identity of the final U2349 is
`c4244971cc6a28286e2e377374a1849d7fc72c76f866e043cb24041351d968df`.

Retain `ahmed_v45`, `metacounter_r1`, `shop_router_0913`, `rayk_v38_low_pressure`,
`farming_v4_0914`, `ahmed_v53`, `thomas_metav4`; the script binary and asset hash are identical to the previous round.
Strategy capacity **478**, continuing 136 historical slots from itself; a new snapshot is added every 64 turns.
All identity, origin, layout, and finite tensors of previous strategies are verified item by item via the import entry; compatibility evidence for old v2/v4 engines is reused based on source/target binary hashes. Evidence from prior PFSP games is preserved in the original run, while the new learner uses new priors.

See the [Selection List](../outputs/analysis/watch4-bc-to-rl-20260925/opponent-selection.json) and
[Historical Pool Verification](../outputs/analysis/watch4-bc-to-rl-20260925/pool-verification.json).

## RL Protocol and Startup

Retain the RL protocol effective at s82001 termination: pure terminal game **WDL: win +1, draw 0, loss -1**.
Each turn consists of **64 self-play games + 64 unified PFSP games**; the script has no independent quota or guaranteed allocation.
Actor/Critic learning rates: **7.5e-6 / 1e-4**, gamma = lambda = 1, no warmup.
Dual-GPU BF16, 48-turn gradient batches, 100,000 turn budget; save full checkpoints every 4 turns.
No automatic evaluation at startup, periodic intervals, or end of run. The protocol only modifies the starting point, running identity/seed, and source/capacity of the historical pool.

**2026-09-25 13:52:54 UTC** Startup
`derived-v5b-m384-watch4-ppo50-20260925-s89001`,
run ID `adb0ac0737c943e0993ace6d81aece62`. First authenticate and fully import the historical pool via bootstrap, then proceed with a normal resume entry from the initial state of a fresh run to execute U1.

Configuration (../configs/learning_watch4_ppo50_20260925.yaml),
Protocol differences (../outputs/analysis/watch4-bc-to-rl-20260925/protocol-diff.json),
startup logs (../outputs/analysis/watch4-bc-to-rl-20260925/launch.json), and
real-time progress (../outputs/learning/derived-v5b-m384-watch4-ppo50-20260925-s89001/learning-progress.json).
Four weight/history import modules Ruff, mypy have passed checks; the original BC and RL ledger hashes have not changed.

**14:00:56 UTC** Full verification completed for **U4 / 512 games** checkpoint, SHA256:
`aa91eb398d5ab594bcb395cab5e5fdb366e944e1bbd83a1fe5d43ff96cd07c5d`.
Actor/Critic Adam completed 16 steps, 339 Actor tensor updates performed; model and optimizer fully finite,
dual rank RNG fully intact. In the first four rounds, each round actually executed 64/64, with all rank rewards being pure WDL;
Actor/Critic learning rates set at 7.5e-6 / 1e-4; all PFSP sampling and post-game statistics precisely replayed from initial state.
Original BC and old RL ledger hashes remain unchanged, dual-GPU operation continues; after initial round, each round takes approximately 38 seconds.
See [formal operation verification](../outputs/analysis/watch4-bc-to-rl-20260925/running-verification.json).

Restore the complete state of this run upon termination:

```bash
CUDA_VISIBLE_DEVICES=0,1 TMPDIR="$PWD/tmp" PYTHONPATH=src \
  .venv/bin/python -m kagg_revue.learning.recovery.cli \
  recovery.run=outputs/learning/derived-v5b-m384-watch4-ppo50-20260925-s89001
```
