# Strength Selection Version BC → Validate Optimal Weight Automatic Connection to s99001 RL (2026-09-28)

After BC completes, automatically switch to RL using the verified optimal weights, carrying over all RL formulations from s97001.
BC has already completed normally before workflow attachment, so the handover is executed immediately; RL
`derived-v5b-m384-strength-canonical-ppo50-warmup300-20260928-s99001`
started at **08:29:37 UTC**, run ID `6c0e950366ac4feca6dc9469f31bfc79`.

## BC Results

`derived-v5b-m384-u590-strength-canonical-bc-20260928-s98001` at **08:14:08 UTC**
Completed normally due to early stopping: 13 epochs / 1,378 batches, improvement less than 0.0005 for 4 consecutive turns after epoch 9.
Validation optimum at **epoch 11**, target **0.14828**,
`pretraining/shard-001166.pt`, SHA256
`3ab4a6edf968c20cda8b08c523d0f549461b770d67998aaf06fd4eb96cf296cb`.

| Validation Metric | Round 1 | Round 11 (selected) | Round 13 |
| --- | ---: | ---: | ---: |
| Total Objective | 0.1768 | 0.1483 | 0.1485 |
| Positioning NLL / Accuracy | 0.157 / 93.9% | 0.135 / 94.7% | 0.134 / 94.8% |
| Market Operations NLL / Accuracy | 0.205 / 92.2% | 0.172 / 93.5% | 0.175 / 93.5% |
| Market Count NLL / Accuracy | 0.410 / 86.2% | 0.330 / 88.3% | 0.332 / 88.4% |
| Unit Count NLL | 0.158 | 0.151 | 0.153 |

Validation of market operations: NLL reaches its minimum of 0.1714 at epoch 8, with unit quantity showing a slight increase from epoch 9 onward;
other domains continue to decline, with the overall objective reaching its minimum at epoch 11.

## Attached Handover

The original workflow could only create and run BC itself, while s98001 was started separately; therefore, a new `attached_bc` mode is added:

- On startup, require that the planned BC protocol matches exactly with the currently running BC ledger, and verify historical archive hashes;
  The current 2,009 source code files and native libraries are frozen into the workflow directory, and the runner executes within an isolated copy.

- Wait for the BC process to exit; only `complete` proceeds. RL is not initiated if the process is stopped, terminated, or the workflow is cancelled.

- Thereafter, follow the original steps: select the saved checkpoint with the lowest verification target, and verify members, lineage, dataset, and numerical boundedness;
  Then inherit the historical pool via the original bootstrap, and initiate training using the original RL phase.

The source code identity recorded in the RL ledger is `3c34137c…`, and both the native library and script runtime are consistent with the frozen snapshot, with the same implementation used for subsequent recovery. See [Plan](../outputs/workflows/derived-v5b-strength-canonical-bc-to-rl-20260928/plan.json), [Selection Point](../outputs/workflows/derived-v5b-strength-canonical-bc-to-rl-20260928/selection.json), and [Workflow State](../outputs/workflows/derived-v5b-strength-canonical-bc-to-rl-20260928/status.json).

## RL Formula and Historical Pool

Same as s97001 ([configuration](../configs/learning_strength_canonical_ppo50_20260928.yaml)):
Terminal `WDL + delta / (abs(delta) + 10000)`, `cash_weight=0`; Actor / Critic LR
**7.5e-6 / 1e-4**, **300 update** linear warmup; per turn **64 self-play games + 64 unified PFSP games**;
frequency reduction for high-win-rate opponents: 64 / 0.95 / 0.05; 7 native scripts; gamma = lambda = 1,
100,000 update budget, save every 4 updates, no automatic evaluation.

Historical pool inherits all **420** external strategies from s97001, plus s97001's own **11** checkpoints
(initial, U64 to U576 every 64 turns, final U590), totaling **431** external strategies;
plus the new BC starting point of **432 strategies + 7 native scripts**, capacity **567**, retaining **136** own slots.
The old PFSP evidence remains in original operation, while the new learner starts from a fresh prior.

## Verification

- Pre-start read-only verification: 420 inherited opponents authenticated via s97001 archive (including replay equivalence evidence from legacy native libraries), all lineage, layout, and numerical checks of the self's 11 checkpoints passed; see [Pool Pre-verification](../outputs/analysis/strength-canonical-bc-to-rl-20260928/pool-preflight.json).
- The initial Actor's 351 tensors match bit-by-bit with the selected BC weights.
- U8 checkpoint: 32 steps for Actor/Critic Adam, LR **2e-7 / 2.67e-6**, consistent with warmup; 339 Actor tensors have been updated, model and optimizer are finite, and both rank RNGs are complete.
  The first 8 turns each allocated 64/64, with 0 error in terminal reward formula for two GPUs; BC and s97001 ledger remain unchanged.
  See [Run Verification](../outputs/analysis/strength-canonical-bc-to-rl-20260928/running-verification.json).

**Early signals.** The 8th round learning rate remains extremely small (maximum prefix KL around 0.0006), and the learner is approximately at the BC starting point.
In this round, PFSP drew the predecessor **s97001 U590**, resulting in **37 wins, 27 losses**, with an average cash increase of +179.
Under the old design, the corresponding results at the BC starting point for the predecessor were s97001 U1 **14–50** and s95001 U3 **7–57**.
This is a single round of 64 games from the training ledger with T=1 sampling, not a formal evaluation.

## Pause and Resume

**Subsequent Status:** U307 has joined [PFSP inheritance](pfsp_inheritance_20260928.md); the original workflow has ended;
Currently running in tmux session `rl-s99001`, managed by the recovery supervision process (PID 1779394). Sending it SIGTERM will cause it to save and exit after the current update ends. The original records from the handover are provided below.

Process flow in tmux session `workflow-strength-canonical-rl`: launcher (806328) → runner (806666) → training (816958). Sending a SIGTERM to the launcher results in hierarchical propagation; training saves and exits after the current update completes, and the workflow will no longer start any further stages. The `tmp/learning-workflow-qbwj7cdx` session must not be deleted during runtime. After termination, recovery is performed using its own archive:

```bash
CUDA_VISIBLE_DEVICES=0,1 TMPDIR="$PWD/tmp" PYTHONPATH=src \
  .venv/bin/python -m kagg_revue.learning.recovery.cli \
  recovery.run=outputs/learning/derived-v5b-m384-strength-canonical-ppo50-warmup300-20260928-s99001
```

## Code

- `learning/workflows/config.py`: `attached_bc` field, default disabled, previous plans are unaffected.
- `learning/workflows/runner.py`: `attend()` waits for external BC; a vanished running process is considered a failure.
- `learning/workflows/attach.py`: Verify and freeze implementation after supervision handover.
- `learning/workflows/test_runner.py`: Behavior of attachment mode under four conditions—completion, stop, process disappearance, and cancellation.
- [Workflow Configuration](../configs/workflow_strength_canonical_bc_to_rl_20260928.yaml)

```bash
CUDA_VISIBLE_DEVICES=0,1 TMPDIR="$PWD/tmp" PYTHONPATH=src \
  .venv/bin/python -u -m kagg_revue.learning.workflows.attach
```

Ruff, mypy passed, 9 workflow tests passed.
