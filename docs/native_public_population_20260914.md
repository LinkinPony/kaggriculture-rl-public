# September 14 Native Script Opponent Update

The user requests to integrate the five selected opponents from the public notebook research into native C++, replace the default training script, and resume training from existing checkpoints.

## Five Frozen Identities

| Training ID | Public notebook | Strategy frozen this time |
| --- | --- | --- |
| `ahmed_v41` | [Ahmed V41](https://www.kaggle.com/code/ahmedberatozer/kaggriculture-v41-review-candidate) | V41 complete control chain |
| `metacounter_r1` | [MetaCounter R1](https://www.kaggle.com/code/alperen5252525/kaggriculture-metacounter-r1-scored-agent) | Complete version selecting experts based on shop combination |
| `shop_router_0913` | [Shop Router 0913](https://www.kaggle.com/code/yhay81/shop-router-0913) | 29 routes and original shop routing |
| `rayk_v38_low_pressure` | [Rank Your Agent](https://www.kaggle.com/code/raykkretzschmar/kaggriculture-rank-your-agent) | Notebook-exported V38 low-pressure opening entry |
| `farming_v4_0912` | [Farming Score V4](https://www.kaggle.com/code/lynnsakurai/farming-score-v4-a-better-shop) | September 12 snapshot, named separately from original `farming_v4` |

See the [frozen manifest](../data/external/kaggriculture-public-native-20260914/manifest.json) for exact entry points, SHA-256 hashes, Rayk auxiliary files, and notebook identities.
The original notebooks, extracted scripts, and download inventory are retained in `data/external/kaggriculture-notebook-survey-20260914/`.
See the [public notebook survey](public_notebook_survey_20260914.md) for the selection rationale.

## Native Implementation

`opponents/compilation/` generates C++ from frozen source code functions, loops, and branches prior to construction.
The same function implementation is shared among five strategies, totaling 209 functions and initialization units.
During training, there is no Python interpreter, AST, or bytecode execution, nor are there Python opponent callback functions per turn.
Native containers preserve the original dictionary order, mutable aliases, scoping, class methods, and copy semantics required by the original.
This is the generated native control flow and C++ container runtime, not a statically typed rewrite manually optimized on a per-function basis.

Entrance continues to use `create_native_opponent_session`, `create_batch`, and `_revue_native.ParallelBatch.advance_programs`; release GIL when executing against opponents.
Observations are constructed directly from the C++ Engine, and actions are also directly converted into C++ PlayerAction.
Each session and fork independently holds control state; they only share frozen trajectory data.
Asset loading binds source and compressed file hashes, and the compiler rejects unsupported syntax during build time.

The old `router_95`, `farming_v4`, `kaito_v58`, `shop_router_0908`, `shop_router_0909` have been removed from the active registry and standard training configurations will reject these retired identities.
Old source code, native implementations, and assets are preserved for historical reproduction; archival protocols remain readable.
The default main configuration and native league configuration have both been updated to use the new five.

## Completed Native Acceptance

- 100 complete and properly paired games: 143,800 actions all identical.
- 25 complete games with DIG/PASS interference injected every 37 turns: 35,950 actions all identical.
- Simultaneously compare control layer decisions, errors, and fallback counts; exclude actual timing diagnosis fields.
- 10 official interpreter comparisons covering five opponents and two seats; 7,190 script actions, complete observations, numeric batch, `advance_programs`, and the 360th-step fork all passed.
- 33 related tests passed, including source integrity protection, rejection of old identities, duplicate observation prevention, cross-game reset, fork state isolation, anonymous function scope release, quota statistics, PFSP recovery, and historical pool retention.
- Ruff, 744 source files passed mypy and `git diff --check`.

Accepted products are stored in `outputs/opponents/public-20260914/`:
[Normal Game](../outputs/opponents/public-20260914/conformance/report.json),
[Interference Game](../outputs/opponents/public-20260914/perturbed/report.json),
[Official Batch Comparison](../outputs/opponents/public-20260914/training/training-parity.json),
[Test Records](../outputs/opponents/public-20260914/tests.log).
These constitute integration correctness verification and do not represent coverage of all possible game scenarios or new leaderboard scores.

8 CPU workers, 8 games per batch of PASS learners' complete game trajectories, native batch timing measured four times:

| Opponent | Time per batch |
| --- | ---: |
| Ahmed V41 | 3.51–3.53 seconds |
| MetaCounter R1 | 3.07–3.09 seconds |
| Shop Router 0913 | 0.14 seconds |
| Rayk V38 | 2.93–2.97 seconds |
| Farming V4 Latest Version | 2.07–2.11 seconds |

This measurement does not include model inference or initialization, and thus cannot be directly used as the training per-turn latency.
After the full game, RSS stabilizes following the initial allocation, with the maximum increment in the last two batches being 4 KiB for each strategy;
Additional checks on session creation and cloning/destroying show no growth in any segment's RSS.
After loading all five strategies, the baseline process RSS is approximately 462 MiB.
The issue of reference cycles between local anonymous functions and their scopes has been fixed; regression checks also cover function aliasing and closures held by outer scopes, preventing premature release of data still needed by the closures. All validations were performed using the fixed binary.
See [Throughput and Memory Logs](../outputs/opponents/public-20260914/throughput.json).

## Stop of Original Operation and Migration

`outputs/learning/budget-q100-top10-2d-20260913-s68001`
Has been normally stopped and fully saved at **U2664**. Checkpoint SHA-256:
`fb437ed3c202fb16e5e8eefaa241cf6f689f657362c1c6c15c04efedfcb61a8e`.
The Actor and Critic optimizers have retained 55,930 / 55,944 steps respectively, and the RNGs for both GPUs are fully preserved.
All checkpoint tensors are finite. The parent process and worker have exited, and the run lock has been released.
See [Checkpoint Verification](../outputs/opponents/public-20260914/stop-verification.json).

Migrate and reuse the existing recovery and eligibility verification process, maintaining 128 games per turn, 30% self-play / 20% independent dynamic scripts / 50% historical PFSP, and the original dual-GPU execution setup.
The core rule engine binary remains unchanged; script extensions and trajectory assets are archived as independent runtime components.
Historical pool members and checkpoint PFSP states are preserved as-is; the new manifest identity starts with no prior evidence.
Upon first completion of the update, old script statistics are cleared.
See [Migration Configuration](../configs/learning_public_20260914_change.yaml) for recipe.

Isolated replica `public-native-qualification-20260914-v2` completed **12 turns / 1,536 games**:
U2668 was fully saved and safely stopped, then restored from frozen source archive to U2676.
Five new opponents were actually sampled; the Actor and Critic optimizers each continued for **252 steps**, both networks updated, all tensors finite, dual-GPU RNG fully present, PFSP exact replay and saved statistics consistent.
The official run in this acceptance phase was not modified. The current U2664 model has also passed 10 full comparisons in the official environment:
14,400 observations, 7,190 learner features, and 7,190 script actions are all consistent.
See [complete acceptance](../outputs/opponents/public-20260914/qualification.json) and
[current model official comparison](../outputs/opponents/public-20260914/official.json).

After recovery, the last six turns of computation graph warming-up take 30.63–35.67 seconds, with a median of 34.99 seconds;
The initial batch shape requires additional compilation and warming-up.
This short validation is not an assessment of training gains from new opponent combinations.

Formally migrated and archived as `population-revisions/0001`, effective from **U2665**.
The only protocol field changed before and after migration is `script_population`; all checkpoint members, historical pools, external models, and PFSP states have been individually verified and found consistent. The file hash of U2664 remains unchanged.
Formal operation has initiated dual-GPU archive recovery. See
[Migration Verification](../outputs/opponents/public-20260914/migration-verification.json) and
[Startup Log](../outputs/opponents/public-20260914/formal-launch.json).

**Formal U2668 checkpoint verified**: U2665–2668 added 512 games, each optimizer advanced by 84 steps, Actor/Critic parameters updated; all tensors are finite, dual GPU random streams progressed and remain independent.
Checkpoint state matches PFSP replay, parent checkpoint chain is complete, and the old script has been removed from new records and active statistics.
Training continues running, see [formal continuation verification](../outputs/opponents/public-20260914/formal-verification.json) and [real-time progress](../outputs/learning/budget-q100-top10-2d-20260913-s68001/learning-progress.json).

## Replay Entry Point

In an existing workspace with frozen original data:

```bash
.venv/bin/python -m kagg_revue.opponents.compilation.cli
.venv/bin/python -m kagg_revue.native.build build.target=legacy build.jobs=8
.venv/bin/python -m kagg_revue.opponents.portfolios.cli workers=12
.venv/bin/python -m kagg_revue.opponents.portfolios.cli mode=training
.venv/bin/python -m kagg_revue.opponents.compilation.benchmark
```

The generated file is located at `native/csrc/opponents/compiled/generated/`, and a compiler modification is required to regenerate it.
Do not directly edit the generated file. Source updates must re-freeze identity, generate assets, and pass qualification verification.
