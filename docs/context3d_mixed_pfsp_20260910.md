# Recent Three Days 26M: Restore PFSP, Add Scripts and Prior 26M Historical Strategy

2026-09-10 According to user request, restore PFSP for `context-26m-3d-20260910-s65001`,
add native script opponents, as well as partial historical versions of `context-26m-20260908-s62001`.
Configured as [learning_context_3d_pfsp_change.yaml](../configs/learning_context_3d_pfsp_change.yaml).

## Restore Boundary and Recipe

Formal pure self-play operation has normally stopped on **U544**. The model, two optimizers, dual-card RNG, and frozen U124 PFSP statistics have been fully saved. Both training and recovery locks have been released.
See [Stop Verification](../outputs/analysis/context3d-mixed-pfsp-20260910/stopped.json).

| Turn Type | Global Physical Game | Per-GPU Physical Game | Global Learning Trajectory |
| --- | ---: | ---: | ---: |
| Current Model Self-Play | 32 | 16 | 64 |
| Historical Model PFSP | 32 | 16 | 32 |
| Four Native Scripts PFSP | 64 | 32 | 64 |
| Total | 128 | 64 | 160 |

The scripts are `router_95`, `farming_v4`, `shop_router_0909`, `shop_router_0908`.
Each script must have at least one pair of seats per card, resulting in a global minimum of 4 games; the remaining seats are allocated according to the decayed PFSP.
Reuse the existing C++ script runtime; no turn-by-turn Python script strategy callbacks are used during training.

Model, BC source, optimizer, dual-GPU RNG, T=1, training seed range, 100k total budget, global logic
batch size 5,760 and execution micro-batch size 2,880 are retained. Each game is equally weighted, with trajectories from both self-play opponents each weighted at 0.5,
opponent game trajectories are frozen and only the learning agent is trained. The new ratio assigns 20 steps each to the Actor and Critic per round, and 32 steps each during pure self-play.

## Cross-Run History Pool

The historical pool capacity remains at **16**, with the prior runs of U512, U1536, U2560, U3584, and U4302 fixedly retained—totaling 5 external versions. The remaining 11 slots retain the current run's BC endpoint, earlier stages, and the most recent 4 snapshots.
A snapshot is added every 64 turns in the current run; external versions are not displaced by new snapshots from this run.
The additional probability covered by recent history is always allocated to the latest snapshot of the current run, without comparing update numbers across different runs.

Pre-import validation of source ledger SHA256, registration of checkpoint hash, original run ID, PPO identity, update number, environment, model topology, and limited weights. Import copies are saved in the official running `historical/`; `historical/manifest.json` records the source path, source ledger hash, original checkpoint hash, and source identity. The original file and its training lineage remain unchanged; external versions are only usable for freezing opponents and cannot pass the current learner's loading verification. Future archival recovery uses locally authenticated copies and does not rely on re-reading previous runs.

The old vocabulary size is **155**, and the current model is **183**. Each vocabulary uses an independent frozen inference graph, with each model retaining its original weights, logits, and sampling distributions. Actions from both sides are mapped to the union of vocabularies only before being fed into the historical game environment; the rollout actions, log-probabilities, and training vocabulary of the learning side retain their original values. Observations, network architecture, and other action semantics must remain consistent. No modifications to native binaries are made.

PFSP uses existing `(1-p)^2` difficulty weights, 20% uniform exploration, 10% coverage of the latest history, 8 prior games, 128 update half-life, and a maximum of 256 effective evidence games.
In each turn, one model is randomly selected from the entire historical batch, with two GPUs executing identical selection decisions and mirrored seat allocations.
The actual match statistics from U124's current run are retained and decayed according to the real update interval; the recovery boundary is explicitly migrated to U544.
External models and newly added scripts start with a 50% prior probability and do not inherit the win rate from previous learning agents.

## Verification Record

Three newly added regression coverage items encompass native execution equivalence, source authentication, and learning party lineage isolation, as well as pause statistics recovery and external pool retention. A total of **44** related Python checks passed, 692 files passed in Ruff and mypy; PFSP frontend checks passed.

Four-script completed 8 official environment comparisons, **11,520 observations** and **5,752 script actions** consistent.
See [Official Environment Verification](../outputs/analysis/context3d-mixed-pfsp-20260910/official.json).

Independent replica completed **U545–552, 8 rounds of real-world dual-GPU PPO**, totaling 1,024 games and 1,280 learning trajectories;
Paused normally at U548, restored to U552 from archived code and local historical replicas.
Both models were updated, and each optimizer advanced by **160 steps**, with all checkpoint tensors bounded;
PFSP sampling replay, ledger/checkpoint statistics, dual-GPU RNG, and parent chain verification all passed.
See [full acceptance](../outputs/analysis/context3d-mixed-pfsp-20260910/qualification.json).

Excluding the first startup, recovery, and initial vocabulary inference graph warm-up, U547/U548/U550/U552 take **26.71 / 26.68 / 27.86 / 26.32 seconds**, with a median of **26.69 seconds per turn**, and peak memory usage of approximately **95.33 GiB per GPU**.
U545/U546/U549/U551 take 260.88/65.05/135.82/38.29 seconds, including compilation or graph warm-up.
These figures are from short-term engineering validation and do not represent algorithmic performance under a fixed learning trajectory budget.
See [Summary](../outputs/analysis/context3d-mixed-pfsp-20260910/qualification-summary.json).

The browser has verified 5 externally linked fast-load rows with source identifiers, and the page has no JavaScript errors, see [WebUI Acceptance](../outputs/analysis/context3d-mixed-pfsp-20260910/webui-qualification.json).

## Official Switch-over

The formal change has been applied to **`population-revisions/0001`**, effective from **U545**.
Individual verification confirms that the protocol only affects `population` and `script_population`; all original asset hashes, the latest checkpoint, BC records, native binaries, and original PFSP interaction evidence remain unchanged.
The 5 imported files have the same SHA256 as the original checkpoint from the previous run.
See [Migration Verification](../outputs/analysis/context3d-mixed-pfsp-20260910/transition-verification.json).

Archival recovery has been initiated for GPU0 + GPU1, see
[Formal launch](../outputs/analysis/context3d-mixed-pfsp-20260910/formal-launch.json).
The U548 checkpoint has been confirmed, with SHA256 of
`64d7cebb8b99bdab1f4c6c33335a110fc82f21059ca461ab277a032dad0c9baa`.
A total of 512 games from U545–U548, with each round using a 32/32/64 ratio and 160 learning trajectories; both models have been updated, and each optimizer has advanced by 80 steps, with all tensors being finite.
PFSP sampling and statistical replay have passed; the checkpoint and ledger are consistent; the dual-GPU RNG is complete and distinct; BC records are preserved, and all 5 external historical versions are retained in the opponent pool.
See [Formal verification](../outputs/analysis/context3d-mixed-pfsp-20260910/formal-verification.json).

The official WebUI has displayed the new ratio and 5 historical versions with source run identifiers; no script errors were found in the browser,
see [page verification](../outputs/analysis/context3d-mixed-pfsp-20260910/webui-formal.json).
Training continues to run; real-time status is based on the official runs `run-status.json`, `learning-progress.json`.

The recovery entry point after normal shutdown remains unchanged:

```bash
CUDA_VISIBLE_DEVICES=0,1 .venv/bin/python -m kagg_revue.learning.recovery.cli recovery.run=outputs/learning/context-26m-3d-20260910-s65001
```
