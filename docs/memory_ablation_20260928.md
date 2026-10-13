# Equal-Weight Memory Switch Ablation (2026-09-28)

Performing ablation analysis during the inference period for the fixed U116 of current s97001 as per user request. Formal results are available at
[Machine-readable report](../outputs/analysis/memory-ablation-s97001-20260928/main/report.json),
detailed game-by-game results are available at [games.jsonl](../outputs/analysis/memory-ablation-s97001-20260928/main/games.jsonl).

**Conclusion: The fixed weight clearly benefits from cross-turn memory.** In the full 1,024-game evaluation, the model with memory versus the model without memory directly pitted results in **104 wins and 24 losses, a win rate of 81.25%**. When clustered by 64 environment seeds, the 95% confidence interval is **[75.00%, 87.50%]**. The script panel win rate approaches saturation, primarily showing minor improvements in cash flow.
Current evidence supports retaining memory; this is the inference-period intervention result for fixed U116, and does not generalize to the retraining upper bound of memory-free models.

## Equal-weighted Direct Combat

64 environment seeds exchange positions, resulting in 128 games, with the memory side as the statistical subject:

| Metric | Result | 95% Environment Seed Clustering Interval |
| --- | ---: | ---: |
| Wins / Draws / Losses | 104 / 0 / 24 | — |
| Win Rate | 81.25% | 75.00%～87.50% |
| Average Final Cash at Opening Memory | 108,738.41 | — |
| Average Final Cash at Closing Memory | 105,109.20 | — |
| Cash Difference per Game (Opening minus Closing) | +3,629.21 | +2,801.88～+4,477.66 |

Win rate interval is completely above 50%, and cash difference interval is completely above zero. Both sides use the same Actor object's full learning weights, with independent historical caching and alternating first-move turns; the side that is disabled clears its history at each turn.

## Opponent Panel Results

64 games per line and mode, win/draw/loss determined directly by terminal cash, no draws.

| Opponent | Wins with Memory On | Wins with Memory Off | Avg Cash On | Avg Cash Off | Cash Increment |
| --- | ---: | ---: | ---: | ---: | ---: |
| Ahmed v45 | 64 | 63 | 114,269 | 110,222 | +4,047 |
| MetaCounter r1 | 64 | 64 | 113,562 | 109,699 | +3,863 |
| Shop Router 0913 | 64 | 64 | 119,829 | 117,847 | +1,982 |
| Rayk v38 | 64 | 64 | 114,085 | 112,348 | +1,737 |
| Farming 0914 | 64 | 64 | 114,118 | 111,456 | +2,663 |
| Ahmed v53 | 64 | 64 | 110,142 | 109,387 | +756 |
| Thomas Meta v4 | 64 | 61 | 111,088 | 110,433 | +655 |
| **Total / Weighted Average** | **448/448** | **444/448** | **113,870** | **111,627** | **+2,243** |

Enable relative close:

- Win rate: 100% vs. 99.107%, difference of **+0.893 percentage points**, 95% interval **[0.000, 2.009]**.
- Terminal cash balance of own account: average **+2,243.20 (+2.01%)**, 95% interval **[271.60, 4,250.42]**.
- Difference in terminal cash balance relative to opponents in the same game: 31,703.03 vs. 29,168.83, an improvement of **+2,534.20**,
  95% interval **[1,128.82, 4,030.81]**.

The script panel exhibits a clearly saturated win rate. This panel supports only minor cash improvements, with win rate increments including zero.
The sample of 448/448 cannot be treated as a guarantee of victory for the overall population. The script uses a fixed opponent drawn from the training history, and the results do not represent the win rate against the external Kaggle overall population.

## Fixed Objects and Interventions

- Run: `derived-v5b-m384-boey-watch4-ppo50-warmup300-20260928-s97001`.
- Fixed weights: Full U116, SHA256
  `26a20d3d51a799339e778ab3480d3ba5574821076082914d56414e4f262ba5c4`.
- Enable: Retain up to 384 turns with 4 summaries per turn for time memory.
- Disable: Clear the two-layer history K/V and valid turn markers before each decision; still fully execute the current turn's summary, time network, memory fusion, and action decoding. All weights and input observation features remain unchanged.
- This response answers whether the trained strategy depends on cross-turn hidden states, which does not equate to comparing a retrained memory-free model, nor does it remove the publicly available historical statistics carried by the input itself.
- Both groups use CUDA BF16, T=1 random sampling, the same execution path, 32 games per batch. Same opponent, same environment seed, same seat, same batch position with paired random streams.

## Reserved Sample

7 native opponent activities: `ahmed_v45`, `metacounter_r1`, `shop_router_0913`,
`rayk_v38_low_pressure`, `farming_v4_0914`, `ahmed_v53`, `thomas_metav4`.
Each opponent uses 32 environment seeds with seat swapping; for each memory mode, there are 448 games, totaling 896 games.
Additionally, 64 independent environment seeds are used for seat swapping to directly compare on-weight memory modes (on/off), resulting in 128 games.
The total formal sample is 1,024 games, with an additional 12 technical qualification games not counted in the results.

Opponent panel environment seed is `9282000000..9282000031`; direct matchup is `9283000000..9283000063`. Sampling base seed is `92840001`, with an initial row offset added per batch; for direct matchups, add 100000. Both seats and all opponents are treated as part of the same environment seed cluster and resampled together using 4096 bootstrap samples to compute a 95% confidence interval. Opponents are equally weighted, and sampling is fixed in size without expanding based on intermediate results.

## Correctness and Reproducibility

Targeted test confirmation: Enabled mode matches normal inference bit-by-bit; disabled mode matches the fresh empty cache state bit-by-bit for the current turn, even when polluted values are written to the cache initially; two seat states are isolated but share original weights.
Real GPU path validation matches RNG-generated first-turn action. At game end, enabled cache contains 1536 valid summaries; disabled cache contains only 4 summaries from the current turn. Weight tensors match bit-by-bit without change. Ruff, mypy, and 1 test pass.

Model, native environment, and opponent source code match the original runtime archive with no differences; the `_revue_core` binary hash is identical.
See [Runtime Identity Verification](../outputs/analysis/memory-ablation-s97001-20260928/runtime-identity.json),
[Checkpoint Identity](../outputs/analysis/memory-ablation-s97001-20260928/checkpoint-identity.json), and
[Technical Qualification Report](../outputs/analysis/memory-ablation-s97001-20260928/qualification/report.json).
Formal output saves the complete parsed configuration, source code archive, source code and native binary hashes, opponent asset hashes, and game-by-game records.
Two actual native binaries and seven opponent assets are separately archived in
[runtime/manifest.json](../outputs/analysis/memory-ablation-s97001-20260928/runtime/manifest.json).

```bash
TMPDIR="$PWD/tmp" PYTHONPATH=src .venv/bin/python \
  -m kagg_revue.evaluation.memory.cli
```

Entry: [evaluation/memory/cli.py](../src/kagg_revue/evaluation/memory/cli.py),
Configuration: [evaluation_memory.yaml](../configs/evaluation_memory.yaml).
The evaluation is independent of the training ledger; the results apply only to fixed U116 and these test conditions.
