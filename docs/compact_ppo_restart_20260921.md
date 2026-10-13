# compact289 PPO: Restart from Original BC

2026-09-21 User requests to stop the rapid degradation of PPO, then explicitly restores the previous large model's gamma, lambda, and the number of Actor updates per turn on dual cards, and directly initiates formal training.

Old run `compact289-v4-selected8-bc100-20260921-s74001` on U47 / 48,128 games
Normal save and exit, exit code 0. The win count against fixed BC opponents dropped from 109/204 at U1 to 0/204 at U44, and the average terminal cash in self-play games decreased from approximately 100,268 to approximately 25,083.
These are training game diagnostics, not independent evaluations, and cannot alone prove which parameter caused the degradation.
The source code, ledger, checkpoints, and complete BC boundaries of the old run are preserved.

New branch is `outputs/learning/compact289-v4-selected8-ppo-restart-20260921-s74001`,
Started GPU0 + GPU1 at 04:37:51 UTC. Configuration see
[`learning_compact_ppo_restart_20260921.yaml`](../configs/learning_compact_ppo_restart_20260921.yaml).

| Item | Current Official Configuration |
| --- | --- |
| Initialization | Original BC `pretraining/shard-011333.pt`; no use of degraded PPO weights |
| γ / GAE λ | 1 / 1, consistent with the original large model configuration |
| Global Logic Batch Size | 442,368 rows; three batches sequentially set at 442,368 / 442,368 / 441,100 rows |
| Actor / Critic Updates per Turn | 3 / 3; Actor updates are prematurely terminated if KL divergence exceeds the original threshold |
| Samples per Turn | All 1,325,836 rows used once, 1 epoch |
| Learning Rate and Warmup | Actor and Critic both at 1e-4, linear warmup over 500 updates, counting from U1 reset |
| Games and Opponents | 1024 games: 820 self-play games + 204 games against historical strategies of the same specification |
| Model | Original compact289, 2,887,708 parameters, complete v4 features and action ABI |
| Reward | Pure terminal WDL: +1 for win, 0 for draw, -1 for loss |
| Other Controls | BF16, KL 0.05 with early stopping only, clip 0.1, entropy 1e-4, original evaluation and retention settings |

The actual Actor/Critic steps for the original dual-card U7702/U7703 are both 3; the later single-card U7820's 6 steps come from changes in device count. This instance aligns with the dual-card configuration. Each turn of 3 steps is realized through three logical batches, with all samples still traversed only once.

When γ=λ=1, the time target reverts to the direct terminal outcome WDL; for each valid action prefix, the terminal return is used minus the corresponding prefix baseline. The Actor/Critic no longer employs the time bootstrap from the previous 0.999/0.95.
The Adam optimizers for both the PPO Actor and Critic start from zero; the Critic is reinitialized according to the original specifications.
The full Adam and dual rank RNG from the original BC are retained, and the new PPO uses the original configuration's initialization seed.

BC weight SHA-256: `898919df3c0a9e44069f5b9857d6be4058a46512acfc4ab75e694f6e78799099`.
Archived source code SHA-256: `f93a354dafd4fe0c88f19a5bac84dd26ddf4c4815647271c2c59152816c55704`.
The new branch uses the same random root/BC's `run_id`, with an additional independent `branch_id` and output directory;
the original BC handover records and a complete copy of the parent PPO's ledger are preserved in the new directory.

The tool restart is only allowed to modify the output directory, γ, λ, and logical batch size; all other parsed protocols remain identical.
BC hash, Adam steps, finiteness of all tensors, dual rank RNG, archived source code, and native binary verification passed,
parent ledger hash unchanged. Relevant Python files Ruff, mypy passed; the PPO algorithm implementation remains unmodified.
Existing return computation and compact target testing pass all 7 checks.

Formal **U4 / 4096 game** checkpoint verified: Actor/Critic Adam steps are both **12**,
three updates per round, two GPUs with full samples, γ=λ=1 and pure WDL are all consistent with the protocol.
Actual U4 learning rate is **8e-7**, optimizer moments are FP32, all tensors are finite,
dual rank RNG is complete; parameter count remains **2,887,708**, Actor has relatively updated from BC.
U2–U4 warm-up takes approximately **33.5 seconds per 1024 games**.
Checkpoint saved to analysis directory to avoid subsequent retention of strategy samples from this launch; training continues.

The win counts against BC in the first four turns were **109/204, 97/204, 116/204, 106/204**.
This is a validation of startup and configuration effectiveness, and does not prove continuous improvement or external competition intensity.

Restore entry (to be executed only after this branch has stopped):

```bash
CUDA_VISIBLE_DEVICES=0,1 TMPDIR="$PWD/tmp" \
  .venv/bin/python -m kagg_revue.learning.recovery.cli \
  recovery.run=outputs/learning/compact289-v4-selected8-ppo-restart-20260921-s74001
```

Evidence: [Startup Log](../outputs/analysis/compact-ppo-restart-20260921/launch.json),
[Restart Verification](../outputs/analysis/compact-ppo-restart-20260921/transition-verification.json),
[Formal Checkpoint Verification](../outputs/analysis/compact-ppo-restart-20260921/formal-checkpoint-verification.json),
[Branch Lineage](../outputs/learning/compact289-v4-selected8-ppo-restart-20260921-s74001/restart/transition.json).
