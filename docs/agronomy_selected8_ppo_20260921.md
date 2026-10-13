# Eight Teams, Five-Day BC Latest Weight Launching Dual-Card PPO

User requests to terminate the current BC, initiate a new RL using the latest weights, and confirm **70% unified PFSP, 30% self-play**.
The new run is `outputs/learning/agronomy-v4-m384-selected8-ppo-20260921-s76001`,
launched at **2026-09-21 09:20:37 UTC**, with parent process PID **3677615**.

## BC Stop and Weight Source

Parent run `agronomy-v4-m384-u7820-selected8-bc100-20260921-s75001` has been normally saved and stopped at
**09:15:36 UTC**, with the parent process and both GPU worker processes exiting.
A total of **10 complete epochs + Round 11, 164/477 batches** were actually completed, amounting to **4,934 Adam updates** and
**28,368,847 supervised turns**. The BC100 budget was terminated early as per user request.
The training/validation NLL at the end of the last complete epoch was **0.17948 / 0.22901**; validation was not fully performed at the end of partial rounds, and the final confirmation set has not yet been evaluated.

Latest checkpoint is `pretraining/shard-004934.pt`, SHA256:
`4fec69a4841733643cdc671c8e4afbdd43f4deae835831a0585925f8ba00b240`.
Confirmed all tensor finite, BC Adam steps at 4,934, dual rank RNG complete, and model geometry consistent.
The original BC directory is fully preserved; the new RL saves a complete parent checkpoint copy, parent ledger hash, parent protocol, and source record.

## Fixed PPO Configuration

Entry: [learning_agronomy_selected8_ppo_20260921.yaml](../configs/learning_agronomy_selected8_ppo_20260921.yaml).

| Project | Setting |
| --- | --- |
| Model | Original 16 × 384 Actor, 24,944,666 parameters, 384 turn memory, full v4 features |
| Initial Weights | Latest BC Batch 4,934 above, full Actor parameter inheritance |
| PPO Initialization | New Actor/Critic Adam; Critic randomly initialized according to original specification |
| Device and Precision | GPU0 + GPU1, two H200; BF16 mixed precision computation |
| Reward | Pure terminal WDL: win +1, draw 0, loss -1 |
| Discount | γ=1, λ=1 |
| Learning Rate | Actor `7.5e-6`, Critic `1e-4`, no additional warmup |
| Budget | 100,000 PPO updates, 128 full games per round |
| Optimization | 1 epoch, 28 trajectories per card in small batches, 48 turn segments, early stopping at KL 0.05 |
| Sampling and Saving | Two sampling pipelines, asynchronous checkpoints; save every 4 updates |
| Seed | New root 76001; training 5,000,000,000, selection/confirmation 5,020,000,000 / 5,021,000,000 |
| Fixed Evaluation | Every 512 updates; starting point from current BC and two random anchors, each with 64 games |

No BC data reading or supervision loss this time, and no inheritance of the cash differential reward exception from the previous s73001.
BC Adam and RNG are preserved in parent checkpoint copies, and PPO uses independent optimization with random states.

## Unified Opponent Pool

This section records the initial pool; subsequently, 137 additional external historical weights used by s73001 from U260 have been supplemented, expanding the historical capacity to 314. Current configuration and confirmation are available at
[Historical Pool Completion](agronomy_selected8_history_completion_20260921.md).

Initial **49 candidates = 7 native scripts + 41 historical model weights + current BC starting point**.
Scripts are `ahmed_v45`, `metacounter_r1`, `shop_router_0913`,
`rayk_v38_low_pressure`, `farming_v4_0914`, `ahmed_v53`, `thomas_metav4`.
Using the existing native C++ batch interface for execution.

Historical weights take the current retained self BC/PPO pool from s73001, and incorporate the final U7820, specifically 41 members, with parent ledger hash fixed in Hydra configuration. All member identities and native environment identities have been confirmed. The new PPO adds its snapshot every 64 updates; historical pool capacity is 177.

70% as the unified pool target ratio, 30% from self-play; integer allocation is performed based on dual-GPU, dual-seat pairing.
Sampling is conducted jointly by scripts and historical models, with no separate quotas or minimum game counts assigned to scripts.
New Actor's PFSP evidence is accumulated from prior knowledge; the win-loss evidence of the original s73001 is preserved in its original runtime.

## Recovery and WebUI

Run ID: `feeadf9606f541ea8ad0795eff3e74c6`; Source Code Identity:
`0cca36a59dd3f53f3d025cd9fd27a413abad345275759ad8a8926d6b186ec901`.
The run directory contains source code archives, native environment, native scripts, and historical weight backups. Restore usage:

```bash
CUDA_VISIBLE_DEVICES=0,1 TMPDIR="$PWD/tmp" \
  .venv/bin/python -m kagg_revue.learning.recovery.cli \
  recovery.run=outputs/learning/agronomy-v4-m384-selected8-ppo-20260921-s76001
```

[Open new RL WebUI](http://127.0.0.1:8765/?run=learning%2Fagronomy-v4-m384-selected8-ppo-20260921-s76001).
The new run uses the PPO update axis, displaying unified PFSP, opponent distribution, optimization, and fixed evaluation;
weight sources are labeled as checkpoint initialization. The old BC continues to retain independent epoch curves and stopping progress.

Evidence: [BC stop verification](../outputs/analysis/agronomy-selected8-bc-to-rl-20260921/bc-stop-verification.json),
[officially launched](../outputs/analysis/agronomy-selected8-bc-to-rl-20260921/launch.json).

## Formal Save Point Verification

**U4 / 512 games** checkpoint `checkpoints/update-000004.pt` has passed verification:
SHA256 `8a780d79f1a6077a8644782a5fa5d6c157ba6ed16be819bc0e17ddd4aa5ab9e7`.
Actor/Critic Adam advances **12 steps**, encoder, time memory, and action head relative to BC have all been updated,
all tensors are finite, double rank RNG is complete. Actual learning rate matches configured value, rewards contain only −1/+1,
cash reward and supervision retention loss are zero.

The sampling and win/loss statistics for the first four rounds of PFSP have been replayed, and the checkpoints and ledger evidence are consistent. The rounds are as follows:
**40/88, 36/92, 40/88, 36/92** — self-play games/unified pool competitions; a historical model was drawn in each of the first four rounds.
No script quota is enforced in this round. The initial Actor matches the BC's 4,934th batch element-wise, and the parent BC ledger and weight hash remain unchanged.
A complete first PPO checkpoint has been preserved for separate analysis.

U1/U2 include initial graph compilation; U3/U4 warm-up takes **29.59 / 29.43 seconds per 128 games**;
This turnaround time does not represent the stable throughput of all scripts or historical opponents.
Training continues running. 8 test items, Ruff/mypy, and JavaScript syntax checks have passed.
Source code, native runtime library, and `restore` in separate archived directories have been verified; no formal PPO interruption has been caused.
Chromium testing confirms normal operation of the new RL panel, checkpoint initialization instructions, and automatic refresh, with no JavaScript errors.

See [Weight Inheritance Verification](../outputs/analysis/agronomy-selected8-bc-to-rl-20260921/initialization-verification.json),
[Formal PPO Verification](../outputs/analysis/agronomy-selected8-bc-to-rl-20260921/formal-verification.json),
[Archival Recovery Check](../outputs/analysis/agronomy-selected8-bc-to-rl-20260921/archive-recovery-verification.json),
and [WebUI Check](../outputs/analysis/agronomy-selected8-bc-to-rl-20260921/webui-verification.json).
