# MMPQ BC Rewrite (September 30)

## Conclusion

The old MMPQ clone is weak, **mainly due to data design issues, not network or decoder capacity problems**. The v3 data mixes together the two distinct playing styles of MMPQ (56594027/56607039 and the current style initiated by 56612150), and lacks two of the latest and strongest versions (56679033 and 56680759). After replacing the v3 data with the "current style across six versions" from v4, while keeping all other training configurations identical (U0 starting point, fixed 1e-5 learning rate, early stopping on validation), the average win rate at T=0 against four fixed reference opponents increases from **48.4% to 77.6%**, and directly against the v3 clone reaches **82.8%**.

Two additional conclusions:

- **T=0 is clearly superior to T=1**: v3 clone improves by +10.2 percentage points, v4 clone by +15 to +22 percentage points.
  Clones should be used with T=0 (condition argmax).
- **Validation of NLL cannot be used to select clones**: The joint decoding variant with doubled learning rate achieves the lowest NLL (0.2036), but performs worst in closed-loop (average of four references at 65.4%). Joint decoding with cosine learning rate and "per-slot autoregressive" units shows no measurable gain; the code is retained as an optional feature and remains disabled by default.

Recommended for use as an MMPQ clone: **v4 P (s101001, epoch 9, T=0)**: cosine recipe with consistent seed twice, and performs best when compared to our strongest RL weights at T=0 (mean 62.7%, versus s100901 U480 at 57.0%).
v5-scratch (s101005) is equally strong and can serve as an alternative.

All of the following are local proxy panels, with **no Kaggle submissions**.
v4 P has since connected to RL s101101; see [subsequent RL](s101101_mmpq_clone_rl_20260930.md).

## Stop training

At 02:31:19 UTC, a normal stop signal is sent to the `derived-v5b-s99001u1061-dsm2d-bc-to-rl-20260929` workflow:
s100901 stops at **U756** (`checkpoints/update-000756.pt`, status `stopped`), workflow `cancelled`,
all historical products are retained. The replay collection process is not stopped.

## Diagnosis

In live Kaggle games, the actual MMPQ policy recorded **6 wins and 0 losses** against s99001 U200 (submission 56658433), with an average cash margin of +9,813. The old clone achieved only 26.6% against U200 on the clone evaluation panel. This gap comes from cloning fidelity; the following sections investigate it component by component.

| Check | Result |
| --- | --- |
| Temperature | v3 clone T=0 48.4%, T=1 38.3% (four references, 128 games per opponent); T=0 helps but is far from sufficient |
| Fitting | v3 training NLL 0.24 → 0.165 continuously decreasing, validation NLL stabilized around 0.220 from epoch 7: overfitting, not underfitting |
| Teacher-forced error | Moving target 92.9% correct, operation 97.9% correct, market 89.5% correct; target error rate increases with hand order (farmer 5.8% → 7th hand 8.8%), higher during nighttime periods |
| Data composition | MMPQ exhibits two distinct strategies: A (56594027, 56607039) and B (from 56612150 onward: add tomatoes, buy third quadrant on day 10, approximately 10.2 hires per day); v3 combines both strategies and excludes 56679033/56680759 |
| Monetary precision | Monetary features are money/1e5 and log1p(money)/12; in BF16, the latter cannot distinguish between 604 and 614 coins, and MMPQ exactly uses these thresholds to decide whether to buy melon seeds at turn 4 |

MMPQ behavior is deterministic (with identical opening positions), but highly sensitive to monetary thresholds; mixing two sets of strategies causes the model to average the two decisions at critical decision points.

## Design and Implementation

1. **Data v4** (`configs/sequences_team_clone_mmpq_v4_20260930.yaml`): Only take current playstyle
   Six versions: 56612150, 56624842, 56640167, 56658903, 56679033, 56680759,
   **714 games**, training/validation on 676/38 (same split seed as v3, split by game hash; v4 validation set has no overlap with v3 training set). In Bradley–Terry strength, these six versions rank among the top in the full leaderboard (56679033 has 123 wins, 0 losses, strength 7.24; DSM strongest version has strength 4.37).
2. **Evaluation at T=0**.
3. **Optional BC learning rate schedule**: `demonstrations.schedule` (linear warmup followed by cosine decay to `final_fraction`); default behavior preserves protocol identity.
4. **Optional joint unit decoding** (`experiment.joint_units=true`, `policy/grounded/joint.py`):
   Units are decoded in slot order (farmer, subordinate 1…), and each unit sees through attention the target cells, actions, and quantities selected by previous units. Output projections are zero-initialized; when expanded from U0, the policy remains bit-wise unchanged; under teacher forcing, parallel computation is performed, and during sampling, decoding proceeds slot-by-slot, resulting in identical distributions (`policy/grounded/tests/test_joint.py`).
   New parameters can use an independent learning rate `demonstrations.joint_learning_rate`.
   Checkpoints do not write this field when disabled; old checkpoints and protocol identity remain unaffected; the panel allows only this one difference in opponent and candidate within the same game.
5. **Teacher-forced error classification tool**: `python -m kagg_revue.evaluation.diagnosis.errors` (`configs/diagnosis_errors.yaml`).

## Round one: v4 data with four variants

Start entirely from U0 (s99001 `initial.pt`), single card BF16, 8 complete trajectories per step, select the optimal based on NLL early stopping validation.

| Variant | Run | Learning Rate | Optimal Epoch | Validation NLL |
| --- | --- | --- | --- | --- |
| P-const (v3 recipe) | s101004 | Constant 1e-5 | 11 | 0.2089 |
| P | s101001 | Cosine, peak 2e-5 | 9 | 0.2065 |
| J (Joint decoding) | s101002 | Cosine 2e-5, new parameter 2e-4 | 8 | 0.2058 |
| J-hi | s101003 | Cosine 4e-5, new parameter 4e-4 | 6 | 0.2036 |

Closed loop (T=0, 128 games per opponent = 64 common seeds × two slots, BF16, reference opponent at T=1):

| Candidate | clone-dsm | clone-mm-pq-v1 | s100201 U200 | s99001 U200 | Four-reference average | vs v3 clone T=0 |
| --- | --- | --- | --- | --- | --- | --- |
| v3 T=0 | 40.6% | 68.8% | 38.3% | 46.1% | 48.4% | — |
| v3 T=1 | 32.0% | 53.9% | 31.2% | 35.9% | 38.3% | — |
| v4 P-const T=0 | 68.8% | 93.0% | 68.0% | 80.5% | **77.6%** | 82.8% |
| v4 P T=0 | 68.8% | 91.4% | 69.5% | 76.6% | 76.6% | 88.3% |
| v4 J T=0 | 71.1% | 93.8% | 67.2% | 76.6% | 77.2% | 84.4% |
| v4 J-hi T=0 | 59.4% | 89.1% | 52.3% | 60.9% | 65.4% | 76.6% |
| v4 P T=1 | 55.5% | 86.7% | 51.6% | 53.9% | 61.9% | 68.8% |
| v4 P-const T=1 | 46.1% | 75.0% | 42.2% | 55.5% | 54.7% | 64.8% |

v4 clone vs. s99001 U200 average cash difference: +2.6k to +3.0k (actual MMPQ on Kaggle: +9.8k, over 6 games).
Each candidate has 512 games in the four-reference mean, with a 95% interval of approximately ±3.7 percentage points: the gap between v4 and v3 is highly significant, while P-const, P, and J are indistinguishable.

Teacher Forcing (v4 validation set, 38 games, same batch of games):

| Model | Mobile Target | Operation | Market | Market Quantity Precision |
| --- | --- | --- | --- | --- |
| v3 | 92.86% | 97.87% | 89.53% | 82.61% |
| v4 P-const | 93.38% | 98.05% | 90.08% | 83.59% |
| v4 P | 93.46% | 98.08% | 90.31% | 83.52% |
| v4 J | 93.50% | 98.05% | 90.31% | 83.48% |
| v4 J-hi | 93.66% | 98.10% | 90.23% | 83.81% |

Turn-by-turn accuracy improves by only about 0.6 percentage points, while the closed-loop win rate increases by nearly 30 percentage points: after removing another set of strategies, remaining errors no longer systematically drive the situation toward an alternative plan. Even with joint decoding observing the teacher's prior unit selections, the target error rate still increases with the sequence number of subsequent moves, indicating that errors made by backline players primarily arise from more difficult positions, rather than from coordination deficiencies.

## Round two: Narrower data and repeated seeds

Data v5 (`configs/sequences_team_clone_mmpq_v5_20260930.yaml`) only takes submissions from 9/29, 56658903, 56679033, and 56680759, **331 games**, for training/validation (316/15).

| Variant | Run | Start and Recipe | Optimal Epoch | Validation NLL |
| --- | --- | --- | --- | --- |
| v5-scratch | s101005 | U0, constant 1e-5 | 12 | 0.2237 (v5 validation set) |
| v5-from-v4 | s101006 | v4 P-const optimal, constant 5e-6 | 2 | 0.2145 (v5 validation set) |
| v4 P-const Second Seed | s101007 | Same as s101004 | 11 | 0.2086 |
| v4 P Second Seed | s101008 | Same as s101001 | 9 | 0.2071 |

Same panel (the first five opponents are identical to the first round, plus v4 P-const T=0 as the sixth opponent):

| Candidate (T=0) | clone-dsm | clone-mm-pq-v1 | s100201 U200 | s99001 U200 | Four-reference average | vs v3 T=0 | vs v4 P-const T=0 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| v5-scratch | 75.0% | 91.4% | 70.3% | 75.0% | 77.9% | 89.8% | **61.7%** |
| v5-from-v4 | 67.2% | 93.8% | 66.4% | 79.7% | 76.8% | 78.1% | 53.1% |
| v4 P-const Second seed | 74.2% | 93.0% | 63.3% | 59.4% | 72.5% | 80.5% | 45.3% |
| v4 P Second seed | 68.0% | 95.3% | 67.2% | 78.9% | 77.4% | 85.9% | 49.2% |

v4 cosine tuning with two seed heights consistent (four references: 76.6% / 77.4%, vs. v3: 88.3% / 85.9%); constant learning rate
Tuning seed differences are significant (77.6% / 72.5%). All v4/v5 clones significantly outperform v3's 48.4%.
v5-scratch matches v4 on four reference opponents, achieving 61.7% win rate against v4 P-const in direct matchups (128 games, 95% confidence interval approximately 53%–70%). Continuing training from v4 clones to 9/29 version yields no improvement.

## Comparison with Our Strongest RL Weights (All T=0)

Four opponents are at T=0 (deployment decoding): s100901 U480, which is Kaggle submission 56689315, U756 is the current stopping point.

| Candidate (T=0) | s100901 U480 | s100901 U756 | s100201 U200 | s99001 U200 | Mean |
| --- | --- | --- | --- | --- | --- |
| v4 P | 57.0% | 59.4% | 67.2% | 67.2% | **62.7%** |
| v5-scratch | 51.6% | 52.3% | 64.1% | 64.1% | 58.0% |
| v4 P-const | 48.4% | 53.1% | 55.5% | 69.5% | 56.6% |

The cloned model is roughly comparable to or slightly stronger than our strongest RL weights (with a cash difference of only +0.4k to +0.6k against U480/U756, and a 95% confidence interval of approximately ±9 percentage points across 128 individual opponent games). However, for s99001 U200, the real MMPQ on Kaggle achieves 6 wins, 0 losses, +9.8k, while the clone reaches 64% to 70% with +1.9k to +2.3k: **the clone is still significantly weaker than the real MMPQ**.

## Products

- Data: `outputs/datasets/team-clone-v4-mm-pq-20260930-train-val-q100`
  (manifest sha256 `063e56ec…617ca9`); `outputs/datasets/team-clone-v5-mm-pq-20260930-train-val-q100`
  (`4a12fb79…217f75`).
- Execution: `outputs/learning/mmpq-clone-v4-{parallel-const,parallel,joint,joint-hi}-bc-20260930-s10100{4,1,2,3}`,
  `mmpq-clone-v5-{scratch,from-v4}-bc-20260930-s10100{5,6}`,
  `mmpq-clone-v4-{parallel-const,parallel}-r2-bc-20260930-s10100{7,8}`;
  optimal members see respective `state.json`'s `rl_initial`.
- Panel and error: `outputs/analysis/mmpq-bc-redesign-20260930/`
  (`temperature/`, `v4-parallel/`, `v4-joint/`, `v4-parallel-t1/`, `v5/`, `v4-reseed/`,
  `vs-rl-t0/`, `errors-v4val-*/`, logs in `logs/`).
- Configuration: `configs/learning_mmpq_clone_{v4,v5}_bc_20260930.yaml`,
  `configs/evaluation_mmpq_clone_{v4_parallel,v4_joint,v4_t1,v5,v4_reseed,vs_rl}_20260930.yaml`,
  `configs/evaluation_mmpq_bc_temperature_20260930.yaml`.

Reproduction (example):

```bash
PYTHONPATH=src python -m kagg_revue.datasets.sequences.versions --config-name sequences_team_clone_mmpq_v4_20260930
PYTHONPATH=src python -m kagg_revue.datasets.sequences.prepare --config-name sequences_team_clone_mmpq_v4_20260930
PYTHONPATH=src python -m kagg_revue.learning.cli --config-name learning_mmpq_clone_v4_bc_20260930 \
  experiment.output_dir=outputs/learning/mmpq-clone-v4-parallel-bc-20260930-s101001 experiment.seed=101001
PYTHONPATH=src python -m kagg_revue.evaluation.checkpoints.panel --config-name evaluation_mmpq_clone_v4_parallel_20260930
```
