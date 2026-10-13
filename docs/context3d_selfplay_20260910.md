# Last Three Days 26M: Pause PFSP, Continue Pure Self-Play

2026-09-10 User requests to pause PFSP and switch to pure self-play. Target operation is
`outputs/learning/context-26m-3d-20260910-s65001`, retain the original random seed and the completed four BC epochs.
Initial data, model, and BC records are available in [Three-Day BC and PFSP Startup Record](context_3d_pfsp_20260910.md).

## Switching Boundaries and Recipes

Operated normally on U124 after full update, then stopped normally, totaling **15,872 games**.
Restore point is `checkpoints/update-000124.pt`, SHA256:
`92c5c3089f8c78623b4b105155470a055ba94fa9c93dd8243e30a559bf9dd9ce`.
Each optimizer completed 2,976 steps; all model and optimizer tensors are finite, and both GPU RNG and PFSP statistics are complete.
See [Stop Verification](../outputs/analysis/context3d-selfplay-20260910/stopped.json).

Switch configuration to [learning_context_3d_selfplay_change.yaml](../configs/learning_context_3d_selfplay_change.yaml).
The protocol only modifies `population`: the historical match weight is changed from 0.5 to 0, and `pfsp: null` is explicitly set.
The script opponent remains empty. Update number, total budget of 100,000 turns, training seed range, BC endpoint, model, two optimizers,
current Actor learning rate **7.5e-6**, Critic learning rate **1e-4**, T=1, and reward remain unchanged.

| Item | Before Switch | Pure Self-Play |
| --- | ---: | ---: |
| Physical matches per round | 128 | 128 |
| Current model self-play matches | 64 | **128** |
| Historical PFSP matches | 64 | **0** |
| Scripted matches | 0 | **0** |
| Learning trajectory | 192 | **256** |
| Actor/Critic target optimization steps | Each 24 | **Each 32** |
| Global logic batch / execution micro-batch | 5,760 / 2,880 | 5,760 / 2,880 |

Each side's trajectory weight is 0.5, maintaining equal weighting per game. The GPU0 + GPU1 and 8 native environment threads per card remain unchanged.
The seed set per round remains unchanged; the seeds are reallocated to the two cards based on the new game compositions, without requiring reallocation of the entire seed interval.
Historical weights are still managed according to existing snapshots and retention rules; no historical inference runtime is built during pauses, and no historical opponents are sampled.
The PFSP statistics of U124 are preserved in the recovery chain; if PFSP is restored later, an explicit update to the statistics boundary is required.

The previous pure self-play switch entry inherited PFSP configuration and forcibly changed the seed range. This fix explicitly disables PFSP and allows retaining the original seed range while keeping the same number of games. An additional regression is added to cover the scope of protocol changes, the complete seed set for two GPUs, and the WebUI not displaying paused samplers in real-time.
14 related tests, full Ruff and mypy (690 source files) passed, see
[Check Record](../outputs/analysis/context3d-selfplay-20260910/checks.json).

## Runtime Verification

Before switching, validate U125–128's four-round complete two-GPU PPO using an independent replica. Stop normally during the process and restore from archive.
Acceptance passed: U126 stopped and restored to U128, completing 512 games across four rounds, 1,024 learning trajectories, with each optimizer advancing 128 steps; all tensors are finite, two-GPU RNG is complete and distinct, and PFSP statistics match those of U124.
No KL rejections occurred in any round, and both Actor and Critic completed 32 steps per round. Initial warm-up and recovery steady-state times were 355.66 / 219.39 seconds; U126/U128 steady-state times are **39.01 / 38.39 seconds**, median **38.70 seconds**, peak **96.10 GiB per GPU**.
The initial acceptance did not reuse project compilation cache; the formal recovery explicitly used repository `tmp/torchinductor` and `tmp/triton`.
See [Full Acceptance](../outputs/analysis/context3d-selfplay-20260910/qualification.json) and
[Model, Optimizer, and Frozen Statistics Verification](../outputs/analysis/context3d-selfplay-20260910/qualification-verification.json).

The formal protocol migration has been applied to `sampling-revisions/0001`, **effective from U125 onwards**.
Only the `population` field is modified before and after the migration; all registered weight hashes, models, optimizers, RNG records, BC records, existing historical pools, and PFSP statistics retain their original values, see
[Migration Verification](../outputs/analysis/context3d-selfplay-20260910/transition-verification.json).
Formal operation began at **2026-09-10 10:38:37 UTC** from U124 archival recovery, see
[Startup Log](../outputs/analysis/context3d-selfplay-20260910/formal-launch.json).

Formal **U128 checkpoint verified**, SHA256 is
`ec3de9029e5f65958948292bca67895033fbe00ffd3dc00291b5790f7ba28a35`, with direct parent chain pointing to U124.
U125–128 each round consists of 128 pure self-play games and 256 trajectories, with no historical opponents, scores, or PFSP sampling records.
Both models have been updated, and each optimizer has advanced 128 steps. All tensors are finite, with complete and distinct dual-GPU RNGs.
BC records and frozen PFSP statistics remain unchanged, see
[Formal recovery verification](../outputs/analysis/context3d-selfplay-20260910/formal-verification.json).
U125 warm-up recovery time is 115.55 seconds; U126–128 are **38.41 / 38.48 / 39.22 seconds**, median **38.48 seconds**, peak **96.10 GiB per card**; all four rounds complete 32 steps each for Actor and Critic, with no KL rejections.

WebUI has displayed **100% Self-play** and the U125 configuration boundary; metrics have been submitted and are loading normally; current PFSP card and historical pool tables are hidden, no JavaScript errors in the browser, see [WebUI Verification](../outputs/analysis/context3d-selfplay-20260910/webui-formal.json).
Page: <http://127.0.0.1:8765/?run=learning/context-26m-3d-20260910-s65001>.

The official status and ratios are based on the running directory's `run-status.json`, `learning-progress.json`.

The recovery command after normal shutdown remains unchanged:

```bash
CUDA_VISIBLE_DEVICES=0,1 .venv/bin/python -m kagg_revue.learning.recovery.cli recovery.run=outputs/learning/context-26m-3d-20260910-s65001
```
