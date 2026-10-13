# Independent Script Research: Enterprise P1 (September 15, 2026)

## Conclusion

Completed independent production planning, financial management, and worker scheduling implementation, and exported a standalone Python script. **No stronger opponent was developed in this round**: 0 wins, 192 losses against six public scripts, and 0 wins, 16 losses against the frozen U5312. Registered as a failed research attempt and not integrated into the official training pool.

Unlike the previous [Revenue Lead R1](script_opponent_research_20260915.md) which inherited Ahmed V43's strategy,
P1's strategy module was independently developed this time, without importing notebook controllers, route tables, or their optimized parameters.
The public script is used solely for evaluating opponents; the reuse repository's rule engine, game records, and evaluation facilities is maintained.

## Independent Design

This issue will be broken down into three parts: production return, working capital turnover, and limited working hours.

1. **Production Return Model**: Predicts future supply and demand based on crops, animals, market inventory, and open shops visible to both sides. Price calculations use a nonlinear inventory curve derived from actual game rules; new production is ranked according to expected revenue, seed cost, time to occupy land, and capital recovery speed. The model recalculates every 6 actions, without considering future random events or the opponent's private inventory.

2. **Funds Management**: Prioritizes currently sellable goods, reserves feed and working capital, and then decides on seeds, animals, land, and labor. When restocking, accounts for feed already carried by workers. Fertilizer procurement is treated as a separate experimental toggle.

3. **Real-time Task Allocation**: Generates tasks such as sowing, watering, harvesting, and animal care from the current farm, scores them by expected return and travel distance, assigns tasks to workers, and retains task ownership. Tested variants include specialized animal workers, daily spatial zoning, and centralized return of workers to a single location. The frozen version retains task ownership and single-location return, while disabling specialized labor roles and spatial zoning.

We also tested a second independent path: using a new daily marginal production target allocator to drive the existing native `NativePlanner` scheduler, with all strategy parameters explicitly passed in. This branch did not yield advantages and was not adopted for the final P1.

Core source code located at [enterprise](../src/kagg_revue/opponents/enterprise/):
[Economic Model](../src/kagg_revue/opponents/enterprise/economy.py),
[Fund Management](../src/kagg_revue/opponents/enterprise/finance.py),
[Task Generation](../src/kagg_revue/opponents/enterprise/tasks.py),
[Scheduler](../src/kagg_revue/opponents/enterprise/agent.py),
[Native Scheduler Experiment](../src/kagg_revue/opponents/enterprise/allocation.py).

## Development Process and Selection Bias

A total of **1,220 complete development game sessions** are retained, including repeated control groups and ledger confirmation; the primary use of two development seeds, `1860917101` and `1860917102`, is repeatedly applied. This is not evidence of strength across 1,220 independent worlds.

Two rounds of evolutionary search include 120 and 128 candidate evaluation records, totaling 992 games; the records retain duplicate superior parameters and thus cannot be considered as 248 distinct strategies. The search covers production preferences, workforce scale, capital recovery, task prioritization, and mobility costs. The configuration, source code snapshots, and full results from each generation in the first round are preserved; the second round includes a complete [search protocol](../outputs/analysis/enterprise-20260915/evolution-02/search-protocol.json).

The best average fund difference on the first development set was −52,217.5. After modifying the transportation logic, the initial candidate for the second round was −45,414.0, which was not exceeded by subsequent searches; this candidate remained 0 wins and 4 losses on the development set.
These values include implementation changes and cannot be interpreted as a strict single-parameter causal comparison.

Dedicated task division, spatial zoning, economic fertilizer procurement, and native scheduling branches have all failed to yield usable results.
The first two native scheduling experiments failed due to parameter interface errors; after correction, 12 games were completed, all resulting in losses; failed startups are not included in the above total game count. In the fertilizer procurement experiment, a recurring issue of fertilizers being repeatedly retrieved and placed in the warehouse was identified and fixed; however, the procurement strategy still lacks an advantage after the fix.

Development record root directory: [enterprise-20260915](../outputs/analysis/enterprise-20260915/).
Each complete experiment panel retains a source code snapshot, configuration, turn-by-turn results, and summary.

## Independent Verification After Freeze

Freeze the [script](../outputs/opponents/enterprise-20260915/enterprise-p1/main.py),
[source record](../outputs/opponents/enterprise-20260915/enterprise-p1/provenance.json), and
[selection and validation plan](../outputs/opponents/enterprise-20260915/enterprise-p1/selection.json)
before the new seed test.
Script SHA-256:

```text
c4c0f5d2dda0c4faacf149ac321eddd9f981b95219ffb79c7b2a5308cad76661
```

Both parties act based on real-time observations, with each complete game consisting of 719 actions. The public script uses frozen original Python source code.
Public verification is conducted using 16 new seeds `1860917401`–`1860917416`, with each opponent swapping seats.
The funding difference is defined as P1's final funds minus the opponent's final funds.

| Opponent | Games | Wins / Draws / Losses | Average Fund Difference |
|---------|------:|----------------------:|-------------------------:|
| Ahmed V43 | 32 | 0 / 0 / 32 | −76,326.3 |
| Ahmed V42 | 32 | 0 / 0 / 32 | −76,305.9 |
| Farming V4 0914 | 32 | 0 / 0 / 32 | −75,988.3 |
| Shop Router 0913 | 32 | 0 / 0 / 32 | −74,448.3 |
| Rayk V38 Low Pressure | 32 | 0 / 0 / 32 | −75,755.7 |
| MetaCounter R1 | 32 | 0 / 0 / 32 | −76,309.3 |
| **Total Public Scripts** | **192** | **0 / 0 / 192** | **−75,855.6** |
| **Frozen U5312** | **16** | **0 / 0 / 16** | **−96,571.5** |

Original Summary: [Public Panel](../outputs/analysis/enterprise-20260915/public-confirmation/summary.json),
[Neural Network Panel](../outputs/analysis/enterprise-20260915/neural-confirmation/summary.json).

U5312 uses an additional 8 new seeds `1860917501`–`1860917508`, swapping seats, CPU FP32, T=1,
random seed is `2 × world_seed + neural_seat`; actor and script hashes are both checked before execution.
Refer to model identity and environment in [Protocol](../outputs/analysis/enterprise-20260915/neural-confirmation/protocol.json).
Here, U5312 is a frozen reference and does not represent the latest checkpoint of the formal training run at this moment.

Seats and opponents share world seeds, and statistics are aggregated by world seed; the public board cannot be considered 192 independent worlds.
Large failure margins exist, and improvements inferred from the development set cannot be used to deduce actual strength gains.

## Failure Analysis and Boundaries

The revenue model accurately implements single-location pricing, but **future demand and supply, production fulfillment, and labor costs remain rough estimates**.
It does not fully simulate the opponent's future replanting, price shocks from both sides, labor required for cultivation and fertilization, and delays in product return to storage.
Sorting by expected return per plot cannot guarantee that the entire field plan can be fulfilled within a limited labor timeframe.

Ledger observation also supports insufficient scheduling efficiency. In the development set `1860917101`, version `default` for seat 0,
P1 prototype submitted 1,846 PASS events and 3,666 moves, with labor cost of 6,761; the opponent corresponded to 452, 2,843, and 3,986.
Prototype FEED/CARE ratios were 169/152, versus 310/410 for the opponent.
These are **early version per-game action statistics**, not successful labor volume, final version averages, or causal attribution.
See [Complete Ledger](../outputs/analysis/enterprise-20260915/accounting-04/games/0000.json).

This result refutes the claim that the current implementation possesses superior capabilities, but it does not undermine the economic planning direction itself.
The next valuable structural improvement should link production decisions with executable work hours, paths, and delivery timelines for joint evaluation—first calibrating short-term forecasts with actual execution outcomes, then considering longer-term planning. Continuing to expand the parameter search of the current scorer lacks justification. This direction has not yet been realized or validated and is therefore not considered part of the delivery capability.

P1 is solely targeted at the standard 10×10, 30-day environment. The final candidate is a pure Python research prototype;
**C++ strategy porting, native batch training acceptance, or submission deadline certification have not been completed**; offline games played on the native engine do not imply that the strategy has been nativeized. Formal training continues to use the already-deployed five-script pool.

## Verification and Reproduction

- Official `kaggle-environments==1.32.7` confirmation of 4 games: public validation of the first two seeds, seat assignments, and against V43.
  All 719 candidate actions' hashes, final funds of both parties, and local outcomes match game by game; all terminal states are DONE.
  These are repeat confirmations and do not add independent strength samples. See
  [Official Confirmation](../outputs/analysis/enterprise-20260915/public-confirmation/official-verification.json).
- 3 targeted tests passed: inventory price curve, fertilizer intake/withdrawal regression, export script full-season action-by-action consistency.
- Full-position Ruff, full mypy (771 source files) passed.
- Freeze script can be byte-for-byte reconstructed from the current five strategy modules and saved parameters; module hashes match source records.
- [Final Research Record](../outputs/opponents/enterprise-20260915/enterprise-p1/qualification.json)
  Binds source code, results, and validation, clearly documenting decisions on research failure and non-migration of training.

The following command is executed from the repository root, reproducing output using a new directory to preserve original records:

```bash
.venv/bin/python -m kagg_revue.opponents.enterprise.experiment \
  --config-name enterprise_confirmation \
  panel.output=outputs/analysis/enterprise-20260915/public-reproduction

.venv/bin/python -m kagg_revue.opponents.enterprise.neural \
  panel.output=outputs/analysis/enterprise-20260915/neural-reproduction

PYTHONPATH=src python -m kagg_revue.opponents.enterprise.verification \
  panel.output=outputs/analysis/enterprise-20260915/public-reproduction

.venv/bin/pytest -q src/kagg_revue/opponents/enterprise/tests
.venv/bin/ruff check .
.venv/bin/mypy
```

Official confirmation requires installation of the corresponding version of `kaggle-environments`; the local `python` has the `rl` environment with this dependency, while project `.venv` does not. The original public source code and manifest are located in gitignored `data/external/`; experimental, model references, and freezing scripts are located in gitignored `outputs/`. Cloning Git separately does not include these local assets.
