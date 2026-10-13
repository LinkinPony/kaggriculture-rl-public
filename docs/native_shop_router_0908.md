# Shop Router 0908 Native Integration

2026-09-08 Upon user request, integrate [yhay81 / Shop Router 0908](https://www.kaggle.com/code/yhay81/shop-router-0908) into the existing C++ opponent batch, and retire Boatlee v29 from active training factories and the trusted registry.
Active IDs: `router_95`, `farming_v4`, `kaito_v58`, `shop_router_0908`.
Current active turn and recovery evidence are available at [Current Mainline](CURRENT_MAINLINE.md).

## Freeze Source and Behavior

Download notebooks and metadata via Kaggle CLI; statically extract base64 from a single code cell within the notebook.
`submission.tar.gz`, no notebook cells were executed. The original notebook, submission package, and four unpacked files are permanently preserved in
`data/external/kaggriculture-shop-router-0908-20260908/`, with file hashes recorded sequentially in the directory at
`provenance.json`. [Training manifest](../data/external/kaggriculture-shop-router-0908-20260908/manifest.json)
Reuse existing frozen sources from other scripts; the old manifest remains unchanged.

`main.py` SHA-256 is `66585d1a5dbfe11c946a3c400278592f860342bc4a8f5e5f87f2a9293348984b`.
`actions.json`, `model.json`, and `observation.py` also participate in trusted identity verification; any modification or omission of dependencies will result in rejection. The scale of source declarations and win rate are not considered as independent evidence of strength in this instance.

[C++ implementation](../src/kagg_revue/native/csrc/opponents/shop.cpp) execute according to the freeze model:

| Time point (zero-based step) | Public status condition | Route selection |
| --- | --- | --- |
| Initialization | None | 0 |
| 144 | Number of already appeared Yarn Store ≤ 0.5 | 0, otherwise 1 |
| 648 | Market EGG inventory ≤ 9888 | 2, otherwise 3 |

The decision in Turn 648 overrides previous trajectories. All four trajectories consist of 719 actions; no new fixes, protection sales, or strategy optimizations are introduced. The implementation preserves the original observation adapter's eight-store capacity limit, int32 inventory conversion, same-turn repeated calls, step 0 reset, market empty slot support, and per-seat private state. Batch fork copies mutable state while sharing immutable trajectory assets.

Python authenticates and loads approximately 37 KiB of compressed assets only at initialization. The execution path continues as
`create_native_opponent_session` → `create_batch` → `ParallelBatch.advance_programs`;
C++ directly reads engine state, releases the GIL in bulk, with no Python opponent callback per turn.
[Static Extractor](../src/kagg_revue/opponents/portfolios/shop.py) rejects unsupported model shapes.

The old C++ implementation of Boatlee v29 and its route asset retention are preserved for historical replay; the factory currently rejects its ID.
The migration tool allows retired IDs only when reading the old protocol; the new protocol still requires active opponents. The original archived source code, checkpoint, optimizer, RNG, and historical metrics are retained.

## Acceptance

- 8 types of initial store seeds, all ordered opponent combinations and their mirrors, totaling **128 games, 184,064 actions**.
  Full action parsing, complete state representation, and clone output from original Python and C++ implementations are entirely consistent.
  [Report](../outputs/analysis/shop-router-0908-20260908/shop-coverage/report.json).
- In every 37 turns, 32 games with **46,016 actions** showing interference on one side are fully consistent.
  [Report](../outputs/analysis/shop-router-0908-20260908/perturbed/report.json).
- Actual training batches of **8 games, 5,752 script turns** match the frozen official environment 1.32.7; additionally covering
  numerical batches, 16 independent fork trajectories generated at turn 360, and physical field counts.
  [Report](../outputs/analysis/shop-router-0908-20260908/training-parity.json).
- Specialized testing covers four decision branches, threshold boundaries of EGG inventory at 9887/9888/9889, repeated calls, cloning before decisions, and session reset across games; also verifies resistance to multi-file tampering and migration of retirement protocols.
- Ruff, 640 source files passed mypy, 15 related Python tests, and 5 frontend tests.

These are equivalence checks for the porting and training interface, not independent conclusions on win rate improvements.
CPU throughput throughout the season seen in [timing report](../outputs/analysis/shop-router-0908-20260908/throughput.json),
excluding model inference, feature encoding, and initialization.

## Reproduction

```bash
python -m kagg_revue.native.build build.target=legacy build.jobs=8
python -m kagg_revue.opponents.portfolios.cli
python -m kagg_revue.opponents.portfolios.cli mode=training output=outputs/analysis/shop-router-0908-20260908
python -m kagg_revue.opponents.portfolios.cli 'seeds=[1860908500,1860908501]' perturb=true output=outputs/analysis/shop-router-0908-20260908/perturbed
python -m kagg_revue.opponents.portfolios.cli mode=throughput output=outputs/analysis/shop-router-0908-20260908
```

`mode=extract asset_destination=tmp/shop-router-extracted` allows reconstruction of four active assets for hash verification.
Future initialization with the same recipe will still use [learning_context_scripts.yaml](../configs/learning_context_scripts.yaml);
the current formal run migration uses [learning_shop_router_change.yaml](../configs/learning_shop_router_change.yaml),
restores using its own archive entry point and does not re-run BC.
