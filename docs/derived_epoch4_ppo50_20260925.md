# Retraining v5b epoch 4 → PPO

**Next status:** User requested a direct feature migration fine-tuning switch to s82001. This run normally stopped at **U258 / 33,024 games** on **2026-09-25 06:15:27 UTC**, with full status preserved.
Current mainline see [s82001 v5b fine-tuning](s82001_v5b_continuation_20260925.md).

User requests to stop BC and start a new RL from epoch 4, inheriting the activity history pool from the previous RL and adding the previous instance's own data.
The original epoch 4 has already been deleted by the old checkpoint retention rule; upon learning that the retraining results differ from the original records, the user explicitly selects
**"Use the retrained epoch 4"**. This run uses the full v5b, without executing v5a or ablation studies.

## Starting Point and Original Operation

Original BC `derived-v5b-m384-u1843-dsm-bc100-20260925-s85001` stopped normally at batch 585, 3,364,920 supervision turns at **02:58:00 UTC**, with full state preserved.
Retraining `derived-v5b-epoch4-reconstruction-20260925-s85001` uses the same initial Actor, data, seed, batch order, and hyperparameters. CUDA non-determinism makes it not equivalent to the recovery of the original training.
Retraining stopped normally at batch 284 at **03:05:35 UTC**, selecting the saved epoch 4 from batch 276:

- Checkpoint: `pretraining/shard-000276.pt`, 276 Adam steps, 1,587,552 supervision turns.
- SHA256: `7ec9b1efadd32334d39d262b06a68ce35650346f71173215650259c65d41d665`.
- Training / Validation NLL: **0.075705 / 0.162742**; original epoch 4 validation record was 0.151673.
- 351 actor tensor values are finite, layout is full v5b / 27,915 dimensions.

See [User Selection Record](../outputs/analysis/derived-bc-to-rl-20260925/selected-epoch.json),
[Weight Check](../outputs/analysis/derived-bc-to-rl-20260925/epoch4-verification.json), and
[Stop Check](../outputs/analysis/derived-bc-to-rl-20260925/stop-verification.json).
BC's epoch weights are retained only for necessary members and can be compressed into files containing only the strategy; the latest restored checkpoint still retains the optimizer. Weight migration can be authenticated and read from this compressed storage, preventing future loss of optional epochs.

## New RL Protocol

Run directory: `outputs/learning/derived-v5b-m384-epoch4-ppo50-20260925-s86001`.
Adopt the effective protocol at s82001 stop, replacing only the starting point, feature version, runtime identity/seed, and historical pool capacity.
Detailed differences see [Protocol Comparison](../outputs/analysis/derived-bc-to-rl-20260925/protocol-diff.json),
Complete parameters see [Hydra Configuration](../configs/learning_derived_epoch4_ppo50_20260925.yaml).

- Pure terminal outcomes: WDL: +1 for win, 0 for draw, -1 for loss; `cash_weight=0`, `cash_margin=null`.
- Each round consists of 128 games: 64 self-play games, 64 uniform PFSP games; scripts have no dedicated quota or guaranteed allocation.
- Actor / Critic learning rates: **2e-5 / 1e-4 (from U27 onwards)**, previously 7.5e-6 / 1e-4; gamma = lambda = 1, no learning rate warmup.
- Dual H200, BF16, 384-turn memory, 48-turn gradient blocks; a full checkpoint is saved every 4 rounds.
- New Critic, PPO Adam, and RNG are introduced; the Actor inherits the exact state from epoch 4.
- Budget of 100,000 turns; a history of self-play is incorporated every 64 turns. No automatic evaluation at startup, periodic intervals, or end of run.

## Historical Pool

Source s82001 `agronomy-v4-m384-dsm-games-ppo50-20260924-s82001`,
Stopped at **U1843 / 235,904 games**, complete ledger SHA256:
`7ed90bebc9534313d94bf4960d8f2f59c6fdb9bbaa37fc8af5dfe209f9dce752`.

Fully inherit its **333 active strategies**: 304 with existing external history, 29 originating from its own initial start/snapshot;
Add its final **U1843**. Total: 334 external strategies, plus the new RL starting point to make **335 strategies**.
Retain 7 existing C++ scripts; initial unified pool contains **342 candidates**:
`ahmed_v45`, `metacounter_r1`, `shop_router_0913`, `rayk_v38_low_pressure`,
`farming_v4_0914`, `ahmed_v53`, `thomas_metav4`.

Strategy capacity **470**, retaining 136 historical slots of its own. The new learner uses a new PFSP prior; the game evidence of the old learner is preserved in its original run and does not claim the win rate of the new learner. Complete selection see [Opponent List](../outputs/analysis/derived-bc-to-rl-20260925/opponent-selection.json).

v2/v4 Historical Actor uses the same old fields and trailing validity block from new observations, preserving original weights and action semantics.
Each generation of native engine compares 10 games, 14,400 observations, showing consistency in old features, actions, masks, and full engine trajectory.
Evidence is bound by source/target native binary hashes, see
[Compatibility Certification](../outputs/analysis/derived-bc-to-rl-20260925/native-compatibility.json).
23 targeted tests, plus Ruff/mypy and diff format checks on 10 modified files, all passed.

The native script completes an additional 14 full games with two seats, 10,066 v5b observations consistent with independent core encoding, all finite; this is an integrated verification for the full PASS learner, not a strategy strength assessment. See
[Script Verification](../outputs/analysis/derived-bc-to-rl-20260925/script-v5b-verification.json).
The optional layout field in historical archives is parsed using default values before performing a full layout comparison; original archives and source metadata remain unchanged.
This compatibility fix passes all 12 historical import regression checks.

## Startup and Verification

**2026-09-25 03:18:45 UTC** Startup, run ID `0df4d8ad66134fe9912f94f989e2746c`,
Supervision process PID 1920227. First import all opponents using authentication bootstrap, then restart U1 via the normal resume entry from the newly launched `initial.pt`; the resume does not inherit the original RL optimizer or update count.
See [Startup Log](../outputs/analysis/derived-bc-to-rl-20260925/launch.json).

[Start Validation](../outputs/analysis/derived-bc-to-rl-20260925/initialization-verification.json)
Confirm that all 351 Actor tensors are bit-by-bit identical;
[Historical Pool Validation](../outputs/analysis/derived-bc-to-rl-20260925/pool-verification.json)
Confirm that the hash and origin of the 333 original pool members plus the additional U1843 are complete, and that the 7 script protocols are consistent,
the ledger of the original BC, retraining BC, and original RL has not been altered.

**03:26:28 UTC** Full validation of U4 / 512 games checkpoint `checkpoints/update-000004.pt`,
SHA256 `be8be22615b70186f247c6d9992298a048c8388b161a31d9504bfb55f43500c9`.
Actor/Critic Adam each take 16 steps; 339 Actor tensors updated, all checkpoint tensors bounded, double rank RNG complete.
PFSP scheduling and statistics from the first four rounds are exactly replayed from the initial ledger; each round consists of 64 self-play games + 64 PFSP games,
rewards take values of −1/+1, cash rewards are zero. U1 has actually played against the newly joined s82001 U1843,
and also completed matches against historical v2 and v4 strategies; rounds three and four take approximately 38 seconds.
Training continues, see [formal verification](../outputs/analysis/derived-bc-to-rl-20260925/formal-verification.json).

Resume from the checkpoint of this run itself:

```bash
CUDA_VISIBLE_DEVICES=0,1 TMPDIR="$PWD/tmp" PYTHONPATH=src \
  .venv/bin/python -m kagg_revue.learning.recovery.cli \
  recovery.run=outputs/learning/derived-v5b-m384-epoch4-ppo50-20260925-s86001
```

This recovery entry uses the running archived source code, native libraries, opponent copy, optimizer, RNG, and PFSP.
Do not perform a fresh bootstrap on the same directory again.

<a id="section-3a5f574f4c9c"></a>

## Learning Rate Adjustment

User requests to increase the learning rate to **2e-5**; under current settings, increase the Actor LR, while maintaining the Critic LR at 1e-4.
**03:38:51 UTC** normally terminated at **U26 / 3,328 games**, boundary checkpoint SHA256:
`16a396c0154e53d6fd0da0765d2752f1c38c5ab1d93aa27cdd86acde0b5d7841`.
Both Adam optimizers completed 104 steps. Full checkpoint CPU recovery verification confirmed consistency in model parameters,
Adam first- and second-order momentum, and step count, with the only difference being the LR of the Actor parameter group changed from 7.5e-6 to 2e-5.
Dual rank RNG and original checkpoint byte integrity are fully preserved.

Fixes `Learner.restore_optimizers()`: For the loop PPO without rollback protection, the same declared constant LR is used; rollback protection with actual adaptive decay retains the saved LR. 11 directed tests and static checks pass.
Adds a narrow-range [LR revision entry](../src/kagg_revue/learning/recovery/rates.py),
allowing modification of the Actor's LR only for stopped, hash-bound PPO ledgers; native engine and all recovery dependencies must undergo authentication.

Formally revised `learning-rate-revisions/0001`: preserve the old ledger, maintain hard links to the complete U26 checkpoint, and incorporate new source code.
Protocol comparison confirmation: only modifies `actor_learning_rate`; members, training records, PFSP, historical pool, and scripts remain unchanged.
**03:46:23 UTC** Initiate recovery restoration via archive entry, retain the existing run ID, and apply new LR from **U27**.
See [Recovery Check](../outputs/analysis/derived-s86001-lr-2e5-20260925/optimizer-restore-verification.json),
[Revision Check](../outputs/analysis/derived-s86001-lr-2e5-20260925/revision-verification.json), and
[Startup Log](../outputs/analysis/derived-s86001-lr-2e5-20260925/launch.json).

**03:50:46 UTC** Passed post-recovery formal verification: U27 and U28 both have actual Actor LR of **2e-5**;
U28's full checkpoint has Actor/Critic LR of **2e-5 / 1e-4**, with Adam steps extended from 104 to 112.
Both Actor and Critic have been updated, all tensors are finite, dual rank RNG is complete; PFSP sampling and statistics are exactly replayed from U26.
Game pairing remains 64/64, reward remains pure terminal WDL, pool consists of 335 strategies + 7 scripts.
U28 SHA256: `61c9b2157351be317bc537794ecfc6523292c457a2b8ac60cd056f4898637384`.
Training continues, see [run verification](../outputs/analysis/derived-s86001-lr-2e5-20260925/resume-verification.json).
