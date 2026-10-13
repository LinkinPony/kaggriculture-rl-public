# PFSP Inheriting the Predecessor's Discount Win Rate Evidence (2026-09-28)

In PFSP, inherit the historical win rate of the previous ledger, discounted by the user's requirement, for both current and future training,
to avoid each new learner having to go through hundreds of past opponents again in order to identify opponents that have already been consistently defeated.

## Problem

New learners previously started from empty evidence (prior 8 games, 50%). s99001 has played against 242 distinct opponents up to U280, of which 193 are already known; in the first 235 turns, 78% of PFSP turn outcomes were heavily skewed toward one side, exceeding 90%. At U307 boundary, among 180 opponents never played against and sampled according to prior, 75.3% of PFSP probabilities were assigned to the next turn, while the ledgers of s97001 and s95001 have covered 429 out of 436 opponents in the opponent pool.

## Rules

Add configuration `population.pfsp.inheritance.discount`, default value **0.5**:

- Provide evidence only to opponents in the current pool and script for which there is **no existing record** of this learner; records already present remain unchanged.
- The donation ledger is sorted from most recent to oldest. The evidence from the k-th donor is first decayed by its own 128-turn half-life down to its last recorded game, then multiplied by `0.5 ** k`, to yield the effective number of games and score for this learner.
- The lifetime win/loss count still only includes games played by this learner themselves.
- Established judgment rule: Before any game between this learner and the opponent, use the evidence from the opponent's **last real game** (at least 64 games, win rate at or above 95%), consistent with the existing principle of "time decay does not reverse established knowledge". After the first encounter, normal judgment is applied using "decayed inherited evidence + new game data"; if performance deteriorates, it reverts to normal sampling.
- Chain inheritance: Evidence inherited by a predecessor but not directly played against will be passed down together with the initial real observation, with decay factors multiplied cumulatively across generations.

The historical pool bootstrap defaults to inheriting from historical records (i.e., predecessors); the BC→RL workflow automatically acquires this behavior.
Historical protocols without this configuration retain their original identity, and the restoration of prior operations is unaffected.

## Current s99001 Switching

s99001 received a stop signal at **11:45 UTC**, normally stopped at **U307**, with full checkpoint, two sets of Adam, dual rank RNG, and historical pool preserved. The revision was executed by donors s97001 (first generation) and s95001 (second generation):

| Item | Value |
| --- | ---: |
| Opponents in pool (including 7 scripts) | 443 |
| Existing learner records, unchanged | 263 |
| Inheritance (s97001 / s95001) | 179 (164 / 15) |
| Directly judged as mastered | 118 |
| Next turn opponents already mastered | 209 → 327 (total still at 5% confirmation probability) |
| Next turn normally sampled opponents | 234 → 116 |
| Sampling probability for opponents not yet faced | 75.3% → 1.6% |

Check point bytes remain unchanged; the ledger records replayable boundary events, which are replayed in memory by `restored_statistics` during recovery, thus passing the recovery check. The protocol only changes `population.pfsp.inheritance`; the source code revision is archived in the runtime directory `pfsp-inheritance-revisions/0001/`. **11:52 UTC** training is resumed via the recovery entry.

## Verification

- Boundary: After replay, the statistics match the ledger; the current learner's 263 records remain unchanged; the new source code is unpackable, and the next round sampling can be precisely reproduced, see [Boundary Verification](../outputs/analysis/pfsp-inheritance-20260928/qualification.json).
- Continuation training: The opponents drawn for U308 match the predictions; the PFSP statistics at the U312 checkpoint match the ledger and include all 179 inheritance records; both Adam optimizers progress continuously from step 1,228 to 1,248, with the model and Critic having finite values and complete dual rank RNG, see [Run Verification](../outputs/analysis/pfsp-inheritance-20260928/running-verification.json).
- Code: 3 new inheritance tests and default value tests have been added; all 18 matching and workflow tests pass; Ruff and mypy pass. All previously running ledger protocols retain their identities when parsed by the new code (differences in existing runs stem from earlier additions of other fields and are unrelated to this update).

## Code and Operations

- `learning/matchmaking/config.py`: `Inheritance` configuration.
- `learning/matchmaking/statistics.py`: `Record.inherited` and mastery determination.
- `learning/matchmaking/inheritance.py`: Supplement evidence from donation ledger and record event.
- `learning/matchmaking/migration.py`: Replay recorded events during recovery.
- `learning/matchmaking/bootstrap.py`, `defaults.py`: New training enabled by default.
- `learning/recovery/inheritance.py`: Apply boundary revisions to already stopped instances.

```bash
PYTHONPATH=src .venv/bin/python -m kagg_revue.learning.recovery.inheritance \
  --config-name pfsp_inheritance_s99001_20260928
```

s99001 is currently running in tmux session `rl-s99001`, and the supervision process PID 1779394 is being restored. Sending SIGTERM to this process will save and terminate it after the current update ends; thereafter, training will continue using `learning.recovery.cli recovery.run=<run-directory>`.

## Limitations

This change was directly requested by the user; no ablation was performed. Inherited mastery status is not revalidated until the first encounter. The review budget is only 5%, so old opponents are reviewed infrequently. Some opponents remain below the 64-game / 95% threshold (for example, around 90%) and continue to participate in the normal sampling pool.
