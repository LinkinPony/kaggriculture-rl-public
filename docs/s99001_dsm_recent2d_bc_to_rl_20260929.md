# s99001 U1061 → Latest Two Days DSM BC → RL (2026-09-29)

User requests to stop the DECEM workflow and switch to **RL v5b s99001 latest weights**, using DSM's most recent two-day data for BC followed by RL, and further clarifies that the **critic also inherits the s99001 latest checkpoint**.

## Stop and Parent Weight

DECEM BC s100601 The process has already been completed and automatically entered RL. After sending a SIGTERM signal to the workflow parent process,
RL s100701 normally stops at **U34**, the workflow is registered as `cancelled`, and all parent and child training processes exit.
Final checkpoint `checkpoints/update-000034.pt`, SHA256
`6064792f59dbc5e37f99f28a438490056cab10206b2ff9f5c3299fbd36b4f110`.
Complete historical data and weights are retained.

s99001 latest registered, actually recoverable weight is **U1061**:

- Run: `outputs/learning/derived-v5b-m384-strength-canonical-ppo50-warmup300-20260928-s99001`
- Checkpoint: `checkpoints/update-001061.pt`
- SHA256: `03a8c0f738811f00ab8200297e8ce7ffde29d46c411c17d0f9c67b72ec92aa42`
- Original ledger SHA256: `31b1d6f83c5653f0ed5934ccf788f3e4a0e8251ed9745b934a3dd2fae048c186`

351 actor tensors, 186 critic tensors are all finite; critic structure strictly loaded and bit-by-bit comparison passes.
BC inherits this actor; after BC, the RL inherits this critic. Optimizers are created in two stages, original runtime is preserved.

## Data Boundary

For this "most recent two days," the interpretation is based on the DSM version submitted by **9/28–9/29 UTC**, with boundaries from `2026-09-28 00:00:00 UTC` to the freeze snapshot `2026-09-29 16:32:06.401662 UTC`.
The complete public games of these versions are retained, without filtering by result or leaderboard score, and without including teacher seats from other teams.

| DSM Submission | Date UTC | Number of Frozen Public Games |
| --- | --- | ---: |
| 56629969 | 9/28 | 99 |
| 56643615 | 9/28 | 120 |
| 56646963 | 9/28 | 115 |
| 56661176 | 9/29 | 92 |
| 56664798 | 9/29 | 109 |
| 56675988 | 9/29 | 63 |

A total of **598 games / 598 teacher trajectories**. Re-query the six submitted Kaggle game lists to supplement 11 games;
No download failures or backlog. The original API response, newly added replays, and source list are permanently stored in
`data/external/kaggriculture-dsm-recent2d-20260929/`, without overriding the continuous collector's data.
Continue using v5b full-trajectory observation, canonical market labels, quantity 1–100, and seed 62001 for training/validation splits.

All 598 games passed encoding with no exclusions; training/validation **563/35**, totaling **429,962** contexts and supervised frames. After market normalization, the proportion of teacher states being completely identical is 99.77649%, with a maximum teacher cash difference of 285.
The data manifest is located at
`outputs/datasets/derived-v5b-dsm-recent2d-20260929-train-val-q100/manifest.json`, SHA256
`f4757ab4c4c5b8f2099f1f6e582d47d7a802747af4d14eea7425178b74e8dec0`.
Hash verification passed for 1,794 arrays; 8 independent re-encodings, 11,520 official observations consistent, covering all six versions. 459 frames were truncated at the existing upper limit of 100, with all 598 world seeds being mutually distinct.

## Training Protocol

Configuration: `configs/workflow_s99001_dsm_bc_to_rl_20260929.yaml`.

- **BC s100801**: Two GPUs, starting from the Actor of s99001 U1061, using only the current DSM data.
  LR 1e-5, field_mean, market field weight 3.5, maximum 40 epochs, patience 4, min_delta 0.0005,
  save selection information every epoch; the Actor with the lowest validation loss automatically enters RL.

- **RL s100901**: Actor from this BC, critic from s99001 U1061. Continue current pure terminal WDL (+1/0/−1), KL (current policy || starting point of this BC) 0.3, update every 128 games per two GPUs,
  Actor/critic LR 7.5e-6/1e-4, 300 updates warmup, new PPO optimizer.

- 50% self-play, 50% unified PFSP; inherit 431 external strategies from s99001 and 24 retained weights from itself,
  adding the new BC starting point to form a total of 456 neural strategies and 7 native scripts, capacity 567.
  mastery 64/0.95/0.05, inherit PFSP evidence from s99001 with discount 0.5.
  RL saves permanent checkpoints every 50 updates, and continues training.

Freeze the workflow code, configuration, and native runtime; only create the RL after the BC completes normally and verifies the optimal weights.
The new RL is authenticated and saves a copy of the U1061 parent checkpoint, writes its critic into the new runtime `initial.pt`; the first PPO update loads this critic; subsequent updates restore usage of its own complete checkpoint.

## BC Completion and Actual Handover

BC completed 15 epochs and stopped early normally according to patience 4. The validation optimal **epoch 11** grouped NLL is **0.14588223007829318**, with the final epoch value at 0.14812767018483736; automatically selected
`pretraining/shard-000781.pt`, SHA256
`ba6e84247aea57f996af8543e01e52f09bd4894d297473e3b70e2b9ff7d592e3`.

RL s100901's run ID is `81cfb029e0cd428d87136a07250a5170`, with the actual `initial.pt` SHA256 value being `54aefee44e96350d7a5893ef1c4562d4172bed6d88a15c9b47c948f6410d115c`.
351 actor tensors match bit-by-bit with the selected BC weights, and 186 critic tensors match bit-by-bit with s99001 U1061; all tensors are finite, and a new PPO optimizer is created. All 455 external policies inherit evidence from the predecessor, and 365 opponent initial entries have been confirmed in the acquired set. See [actual handover verification](../outputs/analysis/s100901-first20-20260929/handoff.json).

## Verification Entry Point

- [Stop and replace record](../outputs/analysis/s99001-u1061-dsm-recent2d-20260929/transition-request.json)
- [Actor/critic parent weight verification](../outputs/analysis/s99001-u1061-dsm-recent2d-20260929/parent-preflight.json)
- [Pre-check of 455 historical weights](../outputs/analysis/s99001-u1061-dsm-recent2d-20260929/pool-preflight.json)
- [Data selection](../outputs/datasets/derived-v5b-dsm-recent2d-20260929-train-val-q100/source-manifests/selection.json)
- [Data verification](../outputs/analysis/s99001-u1061-dsm-recent2d-20260929/data-verification.json)
- [Workflow status](../outputs/workflows/derived-v5b-s99001u1061-dsm2d-bc-to-rl-20260929/status.json)
- [BC progress](../outputs/learning/derived-v5b-m384-s99001u1061-dsm2d-bc-20260929-s100801/learning-progress.json)

13 tests passed for data selection over the last two days, critic inheritance, and BC→RL handover; related code Ruff, mypy passed.

```bash
.venv/bin/python -u -m kagg_revue.learning.workflows.cli \
  --config-name workflow_s99001_dsm_bc_to_rl_20260929
```

The workflow has entered RL; do not re-execute the new command in the same output directory. Proceed with archiving recovery via frozen runs.
