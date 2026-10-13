# Native Training Integration of Xin Si Script

This article retains the historical record of the initial integration. Subsequently, according to user requirements, Shop Router 0908 takes over Boatlee v29. The current active version and acceptance are available at [Shop Router Integration](native_shop_router_0908.md) and
[Current Mainline](CURRENT_MAINLINE.md).

2026-09-08 According to user request, the current script training entry for Kaito v39, Kaito v48, Mugundh v21, and Boatlee v21 is retired and replaced with the four frozen public versions listed below. The current formal operation continues with the previously established pure self-play; this update provides a subsequent script training pool without modifying the archived protocol currently in operation.

| Active ID | Source | Native Behavior |
| --- | --- | --- |
| `router_95` | [Thomas 95.5% Router](https://www.kaggle.com/code/thomastschinkel/kaggriculture-95-5-win-rate-via-replay-routing) | 5 trajectories, 10-stage public state decision tree |
| `farming_v4` | [Farming Score V4](https://www.kaggle.com/code/lynnsakurai/farming-score-v4-a-better-shop) | 4 compatible prefix trajectories, fund and warehouse protection, invalid action repair |
| `kaito_v58` | [Kaito v58](https://www.kaggle.com/code/kaitofukami/238-238-known-streams-v58-minimax-closed-loop) | Independent repair of 10 trajectories, market traffic control and dynamic selection |
| `boatlee_v29` | [Boatlee v29](https://www.kaggle.com/code/boatlee/v29-r1-adaptive-market-hysteresis) | Trajectory repair, image recognition, adjusted market selling with state tracking |

Version is bound by SHA-256 from [frozen manifest](../data/external/kaggriculture-notebook-survey-20260908/manifest.json) and [source directory](../src/kagg_revue/opponents/portfolios/catalog.py).
Initial strength filtering is referenced from [public notebook research](public_notebook_survey_20260908.md);
the acceptance validation of the transplantation and training interface here does not consider the win rate in the notebook title as the win rate of this actual test.

## Execution Method

Strategy implementation is located at [C++ opponents](../src/kagg_revue/native/csrc/opponents/),
reading state directly from the native Engine. Python is only used at creation time for validation, decompression, and asset loading;
during training, there are no imported original scripts, per-turn Python callbacks, observation dictionary construction, or trajectory decompression.
Approximately 180 KiB of compressed assets are statically extracted via AST whitelist and can be reconstructed from frozen source code.
Decompressed trajectories are shared across games and immutable, with independent mutable states per game and per seat.
Kaito's 10 controllers advance synchronously turn-by-turn, replacing the original implementation's delayed creation and prefix replay;
batch forks fully replicate the state of each controller, sharing read-only assets.

Continue using `create_native_opponent_session` → `create_batch` → `_revue_native.ParallelBatch.advance_programs`, releasing the GIL for the entire batch and executing with OpenMP.
Numerical action batching also adopts the same strategy; numerical batches reuse variable sessions and are rejected before progression.
The original script's market slot ordering, zero-quantity slots, terminal liquidation, and Python floating-point rounding semantics are preserved.

`PublicPopulation`, the trusted runtime registry, the runtime archive asset table, and the current training configuration are selected only from the new four.
The legacy underlying modules, teacher dependencies, and historical research configurations are retained for reproducibility; old IDs are no longer accepted by the current training factory.
Ongoing training continues to be executed via the archived source code; future recovery should also use the archive entry specific to that run.

## Acceptance

- Final binary coverage of 8 leading stores, all permutations of both sides' positions, and mirror configurations, totaling **128 games, 184,064 actions**;
  All actions parsed by the official authority, both engine states, and session replica outputs are fully consistent.
  [Report](../outputs/analysis/native-opponents-20260908/shop-coverage/report.json).
- An additional **32 games, 46,016 actions**, where every 37th turn one side's original action is perturbed, to verify recovery and selling procedures after deviation from intended trajectories.
  [Report](../outputs/analysis/native-opponents-20260908/perturbed/report.json).
- Actual training interface includes **8 complete official rule mirrors** with balanced positions for both sides, validating **5,752 script turns**,
  while simultaneously checking numerical batches, physical game turn counts, and 16 independent subsequent trajectories generated at turn 360.
  The official reference is the frozen kaggle-environments 1.32.7.
  [Report](../outputs/analysis/native-opponents-20260908/training-parity.json).
- Four reconstructed asset hashes from source code are completely identical; asset archive and restore operations pass successfully.
  [Asset Identity](../outputs/analysis/native-opponents-20260908/runtime-assets.json).
- Ruff, full mypy, and 22 related tests pass, including rejection of old IDs, source code tampering, and shared mutable sessions.

These are equivalence checks against the default official full-season configuration, not an exhaustive enumeration of all reachable states or arbitrary custom rules.

## Throughput

Intel Xeon Platinum 8558 host, 128-game complete season, one turn advanced per training iteration using `advance_programs`; warm-up round followed by three rounds taking the median. The learning agent uses PASS, timing includes environment and script execution, excluding model inference, observation encoding, and initialization; other tasks are still running on the same machine.

| Opponent | CPU workers | Environment advancement per second |
| --- | ---: | ---: |
| Thomas Router | 4 | 2,069,072 |
| Farming V4 | 4 | 2,036,455 |
| Kaito v58 | 4 | 500,196 |
| Boatlee v29 | 4 | 1,811,446 |
| New four uniform mixture | 1 | 294,847 |
| New four uniform mixture | 4 | 1,082,464 |
| New four uniform mixture | 8 | 1,826,498 |

Mixed 128 games with 8 workers, 92,032 environment advances, median time spent **0.05039 seconds**.
This is not the full-round throughput of PPO. [Original timing](../outputs/analysis/native-opponents-20260908/throughput.json).

## Reproduction Entry Point

```bash
python -m kagg_revue.native.build build.target=legacy build.jobs=8
python -m kagg_revue.opponents.portfolios.cli
python -m kagg_revue.opponents.portfolios.cli 'seeds=[1860908104,1860908105]' perturb=true output=outputs/analysis/native-opponents-20260908/perturbed
python -m kagg_revue.opponents.portfolios.cli mode=training output=outputs/analysis/native-opponents-20260908
python -m kagg_revue.opponents.portfolios.cli mode=throughput output=outputs/analysis/native-opponents-20260908
```

Hydra configuration see [native_opponents.yaml](../configs/native_opponents.yaml).
`mode=extract asset_destination=tmp/native-opponents-extracted` can reconstruct assets for hash comparison.
Enable the script pool training configuration to inherit the new four IDs from [learning_long.yaml](../configs/learning_long.yaml);
The current [learning_context_selfplay.yaml](../configs/learning_context_selfplay.yaml) will still set the script pool to null.
