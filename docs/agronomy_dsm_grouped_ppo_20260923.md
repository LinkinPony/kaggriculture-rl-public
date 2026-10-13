# DSM Group Loss BC Batch 977 Transferred to PPO

Stop the current DSM BC as per user request; start an independent PPO using the latest weights at the time of stop; fully retain the opponent pool `agronomy-v4-m384-watch2-ppo-20260922-s78001` and add the weights from this running instance.

**Follow-up Implementation Revision:** After normal saving on September 23 in U89, enable [Quadrant Behavior Monitoring](quadrant_monitoring.md),
resuming training at 02:56 UTC from the original optimizer, random state, and PFSP. The original protocol and historical artifacts are preserved,
the authenticated training source code is located at `source-revisions/0001`; restore the use of the source code archive command at the end of this document.

## BC Stop and Weight Transfer

`agronomy-v4-m384-u1609-dsm-grouped-bc100-20260923-s79001` stopped cleanly at **2026-09-23 01:50:47 UTC**, at the **977th batch**, i.e., **12 complete epochs + 5 batches**,
after a total of **5,591,663 supervised turns**. The originally planned 100 epoch budget was terminated early; BC Adam, dual rank RNG, data cursor, and group loss identities were fully preserved, three training processes exited, and the write lock was released.

Parent checkpoint: `pretraining/shard-000977.pt`, SHA256: `f590f139309c359fa7b44814303cda652e4578e7664f9c2422093c36c1969344`.
Parent ledger SHA256: `cf8e632d0cded3262c808a5e77c74e95f4c5242a8d91d06fb118417e30a74aad`.
The new PPO initial Actor's **347 tensor**s are completely identical to those in the parent checkpoint.
PPO Actor/Critic Adam and Critic are reinitialized; no BC rehearsal is mixed in this turn.

See [BC Stop Verification](../outputs/analysis/dsm-grouped-bc-to-ppo-20260923/bc-stop-verification.json),
[Initialization and Recovery Verification](../outputs/analysis/dsm-grouped-bc-to-ppo-20260923/initialization-verification.json).

## Carry over the complete PFSP pool from s78001

Based on the frozen ledger when s78001 stops at U1609, SHA256:
`d7a97749e5fb41e5a62507dc0c9b077c76af1f3a602bbf6d3c14fd02f066414d`.

- Fully inherits its 225 external historical strategies, preserving source information, checkpoint hashes, and native compatibility evidence.
- Incorporates s78001's own 27 weights: the starting point, 25 snapshots from U64 to U1600, and the latest U1609.
- Retains the original 7 native C++ scripts, which participate uniformly in PFSP alongside historical strategies without independent quotas.
- Adds the current BC initial Actor, resulting in a total of 260 candidate actors in the initial unified pool.

The actual running sampler members are consistently verified against the ledger, with all original pool members of s78001 and the latest U1609 now fully activated.
A total of 252 historical strategies; capacity adjusted to **388**, retaining the original 136 strategy slots for self-owned strategies.
The new learner accumulates PFSP win-loss records from the neutral prior; the win-loss evidence of the old learner remains fully preserved in the previous run archives.
See [Complete Pool Verification](../outputs/analysis/dsm-grouped-bc-to-ppo-20260923/pool-verification.json),
[Member Selection Records](../outputs/analysis/dsm-grouped-bc-to-ppo-20260923/opponent-selection.json).

## PPO Protocol and Initialization

| Project | Configuration |
| --- | --- |
| Run | `agronomy-v4-m384-dsm-grouped-ppo-20260923-s80001` |
| Run ID | `383a299d16a747ed8b1a7170bba232b2` |
| Start | 2026-09-23 01:57:16 UTC |
| Actor | 16 × 384, 384 turn memory, v4 features, q100 |
| Device and Precision | GPU0 + GPU1, BF16 computation, FP32 parameters/Adam |
| Reward | Pure terminal WDL: win +1, draw 0, loss -1; γ=λ=1 |
| Game | 70% unified PFSP, 30% self-play; 128 games per update |
| Learning Rate | Actor 7.5e-6, Critic 1e-4 |
| Optimization | 1 epoch, 28 trajectories per card, KL 0.05 |
| Budget | 100,000 updates |
| Save/Snapshot | Fully save every 4 updates, add self-snapshot every 64 updates |

Configuration: [learning_agronomy_dsm_grouped_ppo_20260923.yaml](../configs/learning_agronomy_dsm_grouped_ppo_20260923.yaml).
See [parse configuration](../outputs/analysis/dsm-grouped-bc-to-ppo-20260923/resolved-training-config.json),
[startup log](../outputs/analysis/dsm-grouped-bc-to-ppo-20260923/launch.json).
The code, native binaries, parent weights, and complete historical dependencies have been frozen and verified through recovery confirmation.

## Official Training Acceptance

**U4 / 512 games** full checkpoint verification passed, SHA256:
`9a31344f4625d8a5394dbd4451185225e9e7c130255a826f8edaca59ef6efd08`.
Actor / Critic Adam each for **12 turns**, all tensors finite, dual rank RNG complete, 335 Actor tensors updated.
Rewards recorded on two GPUs are purely WDL. BC parent run and s78001 frozen ledger remain unchanged.
The first 4 rounds of PFSP sampling and statistical independent replay are consistent; checkpoint statistics match the ledger;
confirmation of the trajectory and the opponent pool shows no discrepancies.

1,875 files, native binaries, and scripts from the source code archive are recoverable; PFSP, historical archive, and weight transfer
10 related tests passed, Ruff, mypy (938 source files), and diff checks passed.
Monitoring audit status is RL/running; progress continued to Round 5 during acceptance; complete recoverable checkpoint is U4.
See [formal acceptance](../outputs/analysis/dsm-grouped-bc-to-ppo-20260923/formal-verification.json),
[source code recovery verification](../outputs/analysis/dsm-grouped-bc-to-ppo-20260923/source-recovery-verification.json), and
[monitoring audit](../outputs/analysis/dsm-grouped-bc-to-ppo-20260923/monitor-response.json).

## Recovery

Recovery command after normal stop:

```bash
CUDA_VISIBLE_DEVICES=0,1 TMPDIR="$PWD/tmp" \
  .venv/bin/python -m kagg_revue.learning.recovery.cli \
  recovery.run=outputs/learning/agronomy-v4-m384-dsm-grouped-ppo-20260923-s80001
```
