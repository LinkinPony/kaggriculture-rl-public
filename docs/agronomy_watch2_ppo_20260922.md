# Latest Weight Transfer from Double-Player BC to PPO

User requests to pause the current BC, initiate RL with the latest weights, retain historical PFSP opponents and incorporate the preserved weights from `agronomy-v4-m384-selected8-ppo-20260921-s76001`.

## BC Stop and New Operation

BC `agronomy-v4-m384-u2902-watch2-bc100-20260922-s77001` stopped normally on **2026-09-22 12:07:02 UTC**. The latest checkpoint is at **batch 2,120**,
completing **7 epochs + round 8, 195/275 batches**, accumulating **12,182,704 supervised turns**.
The original target of 100 epochs was not reached; BC Adam, dual rank RNG, data cursor, and historical artifacts are fully preserved.

Parent weight: `pretraining/shard-002120.pt`, SHA256:
`1f6e49844cf0623a4e46266570378f6ed57cd2433c704a22fd0c788a4df9c9d9`.
Parent ledger SHA256: `bbe389024eaff53d4d1e0141dbab8e558ea58894d492bf731c3fd4e05313712c`.

New PPO **`agronomy-v4-m384-watch2-ppo-20260922-s78001`** started at
**12:18:58 UTC**, with initial parent process PID **994257**, running ID
`b7bb3b844146487e9f4f587504352d1c`.
The Actor's **347 tensor** values match exactly with the above BC checkpoint on a per-tensor basis.
New PPO Actor/Critic Adam and Critic are created, using a new seed, with no inheritance of BC optimizer or RNG.

Configuration: [learning_agronomy_watch2_ppo_20260922.yaml](../configs/learning_agronomy_watch2_ppo_20260922.yaml).
See [BC Stop Verification](../outputs/analysis/agronomy-watch2-bc-to-rl-20260922/bc-stop-verification.json),
[Initial Verification](../outputs/analysis/agronomy-watch2-bc-to-rl-20260922/initialization-verification.json),
and [Startup Log](../outputs/analysis/agronomy-watch2-bc-to-rl-20260922/launch.json).

## Complete Inheritance History of Opponents

Inherit all **178 external opponents** from s76001's frozen archive, preserving the original source, checkpoints, and hash.
Do not rely on these upstream run-ledgers that may have changed over time; s76001's ledger is fixed as
`77b8c0ad5fae72490e588173b978e675dd463e2c8c714249b51021aadb577379`.

| Historical Runs | Weight Count |
| --- | ---: |
| s73001, agronomy-v4-m384-bc100-3d | 41 |
| s65001, context-26m-3d | 27 |
| s62001, context-26m | 5 |
| s67001, budget-q100-3d | 25 |
| s69001, budget-q100-top10-2d | 29 |
| s68001, budget-q100-top10-2d | 51 |
| s76001, agronomy-v4-m384-selected8-ppo | 47 |
| Total | 225 |

s76001's **47** include `initial.pt`, 45 regular snapshots from U64–U2880, and
the final **U2902**. Its starting point is authenticated through the existing checkpoint-root lineage and is not erroneously marked as a random root.

Seven native C++ scripts retained: `ahmed_v45`, `metacounter_r1`, `shop_router_0913`, `rayk_v38_low_pressure`, `farming_v4_0914`, `ahmed_v53`, `thomas_metav4`.
The scripts coexist in the same PFSP pool with neural strategies, without separate quotas or minimum allocations.
With the current BC starting point, a total of **233 initial candidates** are formed (226 neural strategies + 7 scripts).
Historical capacity **361 = 225 external + 136 self-strategy slots**, retaining the snapshot space from the previous round.

The new learner reaccumulates PFSP win-loss records from a neutral prior; old runtime statistics and outputs are fully preserved.
137 native-compatible evidence entries required for v2 historical weights are inherited from the authenticated s76001 historical revision,
re-verified by reported hash and source/target engine identity, and directly pointed to in the new ledger.

## Training Protocol

| Project | Setting |
| --- | --- |
| Game ratio | 70% uniform PFSP + 30% self-play, rounded up based on paired two-GPU game counts |
| Reward | Pure terminal WDL: +1 for win, 0 for draw, -1 for loss; cash is used only for observation and diagnosis |
| Network | 16 × 384, 384 turn memory, complete v4 features |
| Device | GPU0 + GPU1, BF16 computation, FP32 parameters/Adam |
| PPO | γ=λ=1, Actor LR 7.5e-6, Critic LR 1e-4 |
| Batch | 128 games per update, 1 epoch, 28 trajectory per card per mini-batch, 48 turn sequence blocks |
| KL | Early termination of current update optimization at KL=0.05 |
| Execution | Two sampling pipelines, asynchronous checkpoints |
| Budget | 100,000 updates; a snapshot is included every 64 updates |
| Save and Evaluation | Full checkpoint every 4 updates; evaluation every 512 updates |

No online BC loss, no cash-margin or intermediate cash rewards. Both player data collection processes continue running.
14 historical imports/PFSP tests, Ruff, and full mypy (934 files) passed.
Initial configuration, Actor, 225 opponents, native scripts, and all active dependencies have passed formal recovery entry validation.

History import preparation entry `kagg_revue.learning.matchmaking.bootstrap` is only applicable to fresh runs.
This initialization has been completed and the same directory should not be executed again. For future normal shutdown recovery, use the original source code archive:

```bash
CUDA_VISIBLE_DEVICES=0,1 TMPDIR="$PWD/tmp" \
  .venv/bin/python -m kagg_revue.learning.recovery.cli \
  recovery.run=outputs/learning/agronomy-v4-m384-watch2-ppo-20260922-s78001
```

## Official Training Acceptance

**U4 / 512 games** complete checkpoint verified and a copy retained in the analysis directory.
SHA256: `95dd836ee19d0bf97cc890e7fbb8176aeda31b48f42f6fa5c51b930ec63319fd`.
Actor/Critic Adam each for **12 turns**; encoder, memory, and action head updated, all checkpoint tensors bounded,
two different rank CPU/CUDA RNGs fully intact. Checkpoint and ledger PFSP statistics consistent,
sampling from the first four rounds prior to initial neutral prior replay, game allocation, and win/loss evidence all consistent.

| Update | Opponent | Self-play / PFSP Games | Time |
| --- | --- | --- | --- |
| 1 | s76001 / U1600 | 40 / 88 | 89.07 seconds |
| 2 | s76001 / U2880 | 36 / 92 | 53.80 seconds |
| 3 | s68001 / U5312 | 40 / 88 | 40.32 seconds |
| 4 | s76001 / U2880 | 36 / 92 | 29.45 seconds |

Actual reward is −1/+1; cash reward and BC loss are zero. Parent BC checkpoint, ledger, and s76001 ledger hashes are preserved. Monitoring interface confirms type `rl`, status `running`, 233 candidates, and has reached U7 during reconciliation. Training continues, see [formal verification](../outputs/analysis/agronomy-watch2-bc-to-rl-20260922/formal-verification.json).
Together with [monitoring reconciliation](../outputs/analysis/agronomy-watch2-bc-to-rl-20260922/monitor-response.json).
