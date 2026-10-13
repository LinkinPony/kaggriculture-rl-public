# U113: Recent Submissions from Three Parties to BC

Stop s82001 PPO as per user request, and start a new BC using the latest Actor at the time of stop and the cleaned, validated DECEM / M & M & P & Q / DSM dataset.

**Next state:** User requested transition to RL; this BC has been normally terminated at
**Batch 720 / 4,130,174 valid supervised turns** on **2026-09-24 08:45:18 UTC**, with the latest Actor used to initiate
[s84001: Cash differential reward, 50% self-play PPO](agronomy_watch3_margin_ppo50_20260924.md).

## Parent Run and New Run

`agronomy-v4-m384-dsm-games-ppo50-20260924-s82001` stopped normally at **2026-09-24 08:30:09 UTC** in **U113 / 14,464 games of RL**.
Actor/Critic Adam each took 452 steps, with dual rank RNG, PFSP, and full history pool preserved.
Using the latest complete checkpoint `checkpoints/update-000113.pt`, SHA256:
`a1f40ad6730be9ad8dbf66a133ac7bdf91274ee2475b68ee97f21c5f40e64e70`.
See [stop verification](../outputs/analysis/watch3-bc-20260924/stop-verification.json).

New BC **`agronomy-v4-m384-u113-watch3-bc100-20260924-s83001`** started at
**08:31:58 UTC** running GPU0 + GPU1, with run ID `59e262925e654a8c9a789a2cde5c5011`.
The initial Actor's **347 tensor**s and layout are identical to U113, with a new BC Adam created;
the parent ledger hash remains unchanged. See [Start Verification](../outputs/analysis/watch3-bc-20260924/initial-verification.json),
[Startup Log](../outputs/analysis/watch3-bc-20260924/launch.json), and
[Training Configuration](../configs/learning_agronomy_watch3_bc_20260924.yaml).

## Data and Training Agreement

Using the frozen **759 games / 783 trajectories**, with **750 train / 33 val**.
Filtering six versions from three parties based on official submission times from 9/23 00:00 to 9/24 08:11:31 UTC,
excluding 7 games involving MMPQ 56509757, and retaining the exclusion criteria from 56414341; additionally excluding 2 games that timed out mid-process.
Only monitoring teacher seats within the scope, retaining two teacher seats for 24 valid teacher matchups.
See [complete data description](watch3_bc_20260923_24.md).

Data manifest:
`outputs/datasets/agronomy-v4-watch3-submissions-20260923-24-train-val-q100/manifest.json`,
SHA256 `d93a4b53c8347006c18f06d2299580a9f13aa1d83c5e40a63f08a74034cf55e9`.
The training loader has re-confirmed all array hashes, geometric interfaces, and seed partitions, see runtime directory
`demonstration-qualification.json`.

Adopt the s81001 BC protocol: 16 × 384 network, 384 turn memory, agronomy v4, q100;
Normalize the five action types separately, with equal weights of 1. Fixed LR **1e-4**, dual-GPU BF16 computation, FP32 parameters and Adam optimizer;
Global 8 complete trajectories, 4 per GPU, sequence blocks of 48 turns.
Each epoch: **94 training batches / 5 validation batches**, totaling **9,400 Adam updates** over 100 epochs.
Each epoch contains 539,094 effective training supervision turns, with a total budget of 53,909,400 turns; padding with masked trajectory segments in the final batch.
Save full state every 16 batches and at epoch boundaries, no early stopping, stop after completion, and do not automatically enter PPO.

After normalizing the default values, compared to the previous BC, only the starting point, data, runtime directory, and random seed have changed; see
[Configuration Differences](../outputs/analysis/watch3-bc-20260924/protocol-differences.json) and
[Parse Configuration](../outputs/analysis/watch3-bc-20260924/resolved-training-config.json).

## Official Operation Verification

**08:35:06 UTC** Verified complete checkpoint of the **48th / 276,006 valid supervision turns**,
SHA256 `658a3f876f799cf79ca82ff205f56d8d19d96593292516d7f96433257d392b48`.
Adam for 48 steps, LR 1e-4, with dual rank RNG fully completed; all model and optimizer tensors are finite,
335 Actor tensors have been updated. Data hash, loss protocol, checkpoint, and ledger are consistent,
parent RL ledger unchanged. Dual-GPU training continues, warmed up to approximately **0.74 seconds/batch**, RL update count is 0.
See [formal verification](../outputs/analysis/watch3-bc-20260924/formal-verification.json).

1,894 source code archive files and native binary hashes have passed, see
[Source code recovery verification](../outputs/analysis/watch3-bc-20260924/source-verification.json).

## Recovery

After normal termination, the same BC can be continued through the archiving entry:

```bash
CUDA_VISIBLE_DEVICES=0,1 TMPDIR="$PWD/tmp" PYTHONPATH=src \
  .venv/bin/python -m kagg_revue.learning.recovery.cli \
  recovery.run=outputs/learning/agronomy-v4-m384-u113-watch3-bc100-20260924-s83001
```
