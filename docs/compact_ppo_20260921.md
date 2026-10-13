# compact289: Latest BC Connection Official Dual-Card PPO

User requested to stop BC on 2026-09-21, and started a dual-GPU PPO with the latest weights, learning rate set to 1e-4, 500 update warmup, GAE lambda 0.95, gamma 0.999.
Retained the same run ID as `outputs/learning/compact289-v4-selected8-bc100-20260921-s74001`.
The directory name containing BC100 records the original budget, and does not indicate that 100 epochs have actually been completed.

## BC Boundary

- Normally terminated at `pretraining/shard-011333.pt`: 47 full epochs + epoch 48, batch 100/239.
- 11,333 Adam updates, 130,054,139 supervised turns.
- Final full epoch training NLL 0.26677751, validation NLL 0.28151980.
  The latest weights from partial epochs were not additionally verified, and the confirmation partition was not used for this handover selection.
- Weight SHA-256: `898919df3c0a9e44069f5b9857d6be4058a46512acfc4ab75e694f6e78799099`.
- The original BC ledger, source code, data identity, complete Adam states, and RNG for two ranks are retained.
  `bc-completion/0001/bc-final.pt` additionally preserves the original complete BC checkpoint.

## Formal Training Agreement

| Project | Configuration |
| --- | --- |
| Model | compact289, Actor + Critic, 2,887,708 parameters; full v4 features and 286 scenario tokens |
| Hardware and Precision | GPU0 + GPU1, two H200; BF16 mixed precision, parameters and Adam in FP32 |
| Base Learning Rate for Actor / Critic | Both set to 1e-4 |
| Warmup | First 500 PPO updates; linear warmup for both optimizers |
| γ / GAE λ | 0.999 / 0.95, computed in chronological order of full game time |
| Physical Game per Turn | 1,024, 820 self-play + 204 runs of historically identical models |
| Samples and Updates | All decisions involved, 1 epoch; global accumulation after which Actor/Critic each update once |
| Global Logical Batch / Computation Micro-batch | 2,000,000 / 12,288 rows; 6,144 rows per GPU per micro-batch |
| Opponent Pool | Start from BC endpoints, uniformly sampled; a snapshot added every 64 updates, capacity 177 |
| Reward | Pure terminal WDL: +1 for win, 0 for draw, -1 for loss |
| PPO | clip 0.1, entropy 1e-4, KL 0.05, only early stopping |
| Budget | Continuation of the original configuration with 100,000 updates |
| Execution | Two CPU/GPU sampling pipelines, asynchronous checkpoints |

Warmup uses absolute PPO update: `lr(u) = 1e-4 × min(u / 500, 1)`.
U1 is 2e-7, U250 is 5e-5, and U500 and beyond is 1e-4. Resuming continues from the last completed update without reinitializing the timer; during warmup, both the Actor and Critic are trained.

GAE uses `δ_t = r_t + γ V_(t+1) − V_t` and `A_t = δ_t + γ λ A_(t+1)`; terminal reward uses `V_T=0`, and WDL reward is only available in the final turn.
The critic target is `V_t + A_t`. The prefix-condition strategy uses the same-turn target minus the corresponding prefix baseline;
within the same turn, unit/market fields do not receive duplicate discounts, and padding fields still have no weight.
The original rollout retains undiscounted WDL for reward auditing, and the GAE target is constructed separately.

Model architecture and features remain unchanged. The old implementation retains the direct terminal return path with default gamma=1 and lambda=1;
Adding new parameters without changing their default values does not alter the identity of the old protocol.

## Startup, Recovery, and Verification

Configuration: [learning_compact_ppo_20260921.yaml](../configs/learning_compact_ppo_20260921.yaml).
Startup time: **2026-09-21 03:58:15 UTC**, initiated by the archive recovery process to launch two training ranks.
Training code identity: `c3daec1ec76f2a84af47acde5c1a34793a2f6e76004448a9e3aefbfd39ddeab0`.
Weights of the original BC Actor are directly continued; the two Adam optimizers for PPO are in new states, while the Critic is randomly initialized according to the original specification.

Upon runtime stop, restore using the original entry point:

```bash
CUDA_VISIBLE_DEVICES=0,1 TMPDIR="$PWD/tmp" \
  .venv/bin/python -m kagg_revue.learning.recovery.cli \
  recovery.run=outputs/learning/compact289-v4-selected8-bc100-20260921-s74001
```

GAE's Turn 719 parallel recursive and independent scalar recursive comparison, win/draw/loss trajectory boundaries, lambda 0/1, gamma discount, prefix padding, and warmup recovery tests passed; together with existing BC/PPO tests, a total of **20 tests passed**.
Related 11 Python files passed Ruff and mypy checks. Handover also verified the latest BC's hash, Adam steps, finite-ness of all tensors, double rank RNG, and archival source code and native binary identities.

See the [formal launch record](../outputs/analysis/compact-ppo-20260921/launch.json) and the run directory `bc-completion/0001/transition.json`.

Formal checkpoint verification completed for **U4 / 4096 games**: Both Actor and Critic Adam have advanced 4 steps, with actual learning rates both at **8e-7**. FP32 moments, gamma/lambda, and both rank RNGs are correct. All **651** tensors are finite. The Actor has been updated relative to BC, and the measured parameter count remains at **2,887,708**.
A total of **1,325,836** decisions were fully utilized in each of the first four rounds, with no early stopping of the Actor or sample subsampling.
U1 includes compilation time of approximately 495.8 seconds; U2–U5 per full round take approximately **33.14 / 33.29 / 33.23 / 33.42 seconds**, respectively.
These are early timing metrics for the current two-GPU trained policy; training continues.

Evidence: [Handover Verification](../outputs/analysis/compact-ppo-20260921/handoff-verification.json),
[Update Verification](../outputs/analysis/compact-ppo-20260921/formal-updates-verification.json),
[Checkpoint Verification](../outputs/analysis/compact-ppo-20260921/formal-checkpoint-verification.json).
The WebUI has confirmed the switch to the PPO view and displays the actual optimizer learning rate.
