# Shop Router 0909 Native Opponent

Original source from [yhay81 / Shop Router 0909](https://www.kaggle.com/code/yhay81/shop-router-0909),
Notebook ID `133670867`. Downloaded notebook and metadata via Kaggle CLI on 2026-09-09,
used AST to parse source code cells and base64/gzip constant data, without executing notebook cells.
Reusable original content, Apache 2.0 license, manifest, and file hashes are preserved in
`data/external/kaggriculture-shop-router-0909-20260909/`.

File identity:

| File | SHA-256 |
| --- | --- |
| main.py | `d6d74997dc5b483db63d8e39cafa1afeec0f366824e75107e109123f111e866b` |
| actions.json | `17d503f2fd20d59f9c0f14024d1e74a8add8bb9b5561d4d908b45deecb5495ef` |
| Compressed native assets | `eab3ee1ef7e4b2b40830b835fdd785db19e2fdfd7366ec2aa94d5f3e9171f52b` |
| Five-script manifest | `1e7c8958cc41e003ca80778a3fddb502a49599426352e2085aa25e3b49a73c8b` |
| Verified _revue_native | `d7149aeb96acbeb954764120196fc9efdee524aa8004c184fecb6df16f1f7dad` |

Implemented at `src/kagg_revue/native/csrc/opponents/shop_reactive.{hpp,cpp}`,
Registered separately with 0908. 13 complete 719-turn action trajectories are shared via the existing portfolio loader,
each game and each seat maintains independent queues and pre-sale memory, with state forked via deep copy.
Training continues to use `create_native_opponent_session` and `opponents.batches.create_batch`;
the entire `advance_programs` runs in C++ with GIL release.

Original strategy semantics are preserved: at turn 144, select path based on ordered store; at turn 648, switch to route 2;
When PLANT, BUILD_COOP, or BUILD_PASTURE are blocked by weeds, insert DIG, delaying only the worker's action for that day;
Clear the queue at day boundary; pre-deduct sales from the next turn's order; retain empty order slots, inventory insertion order,
a maximum of 10 orders, and final terminal liquidation sorting. Repeated calls within the same turn will reset the strategy state, differing from 0908.
The warehouse projection reuses previously verified native helper functions, preserving the source script's fixed capacity and animal PLACE handling.

Verification result:

- All five scripts are fully ordered paired and mirrored, with 4 independent seeds, 100 complete games, and 143,800 action comparisons passed.
- An additional 50 games with action perturbations every 37 turns, resulting in 71,900 action comparisons passed.
- Actual training of `ParallelBatch`, numerical batches, 20 forks, and comparison against official environment: 10 games, 7,190 script action comparisons passed.
- Regression coverage of 64 ordered store pairs, all 13 routes, actual non-empty mowing queues, early sale memory, day boundary, repeated calls, cross-game reset, and session clone.
- Mixed league batch validation of both model and script seat assignments; the relative gains of learners in script batches are explicitly reconstructed into physical seat order.

Reports available at [complete game](../outputs/opponents/shop-router-0909/conformance/report.json),
[disturbed game](../outputs/opponents/shop-router-0909/perturbed/report.json),
[official environment and training batch](../outputs/opponents/shop-router-0909/training/training-parity.json).
These results verify transplantation consistency and are not intended as an estimate of strategy strength improvement.

Reconstruction and Verification Command:

```bash
.venv/bin/python -m kagg_revue.opponents.portfolios.cli mode=extract \
  manifest=data/external/kaggriculture-shop-router-0909-20260909/manifest.json
.venv/bin/python -m kagg_revue.native.build build.target=legacy build.jobs=8
.venv/bin/python -m kagg_revue.opponents.portfolios.cli mode=training \
  manifest=data/external/kaggriculture-shop-router-0909-20260909/manifest.json \
  output=outputs/opponents/shop-router-0909/training
```
