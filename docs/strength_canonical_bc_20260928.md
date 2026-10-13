# Intensity Selection Version, Market Tag Standardization, and Field-Weighted BC (2026-09-28)

**Next status:** 08:14 UTC completed normally due to early stopping (13 epoch), verification of optimal at epoch 11 already automatically proceeded as per user request to connect [s99001 RL](strength_canonical_bc_to_rl_20260928.md). The original startup log below is retained.

According to user request, stop s97001 RL and start the new BC design using its latest complete **U590** weights:
`derived-v5b-m384-u590-strength-canonical-bc-20260928-s98001`.
No ablation will be performed. The three modifications target issues identified in the previous quantization round: inverted influence of teacher strength and loss impact, excessive format noise in market labels, and overfitting of the small-sized domains by amplifying them by approximately 30 times under equal weighting across five domains.

## 1. Teacher Selection: Choose the recent version based on measured strength

The top five (MMPQ 3030.1, DSM 3028.4, Boey 2991.0, DECEM 2972.2, Vadim 2965.4) are exactly the teams tracked by the five continuous data collectors, so there is no need to add new teacher sources—the issue lies in selecting which **versions**.

Online ratings for fixed versions decline as the opponent pool grows stronger: Boey 56521745's rating has remained unchanged from 9/24, dropping from a peak of 3116 to 2991. Therefore, ratings from different periods cannot be directly compared; instead, actual win/loss records from contemporaneous games should be used.

Rules (`VersionSettings`, frozen at 07:42 UTC of five collector snapshots):

1. Use all **4,339** decisive public games from 9/25 00:00 UTC onward to fit Bradley–Terry logit strengths for **1,790 submissions**, with an N(0, 4) prior. Opponent submissions are also model parameters.
2. Restrict candidates to versions from the five teams **submitted from 9/26 00:00 UTC onward**, reflecting the prior that newer versions are stronger.
3. Select strengths no lower than the strongest candidate minus **0.5 logit** (threshold 4.494, approximately a 38% expected score against the strongest version).
4. Also include the latest version of an already selected team if it has not converged, provided that its strength plus 2 standard deviations still reaches the threshold.

| Version | Submission Time (UTC) | Strength ± Standard Deviation | Training Steps | Win Rate | Selection Reason |
| --- | --- | ---: | ---: | ---: | --- |
| DSM 56582621 | 9/26 15:15 | 4.99 ± 0.33 | 128 | 92.2% | Within threshold |
| DSM 56606993 | 9/27 11:17 | 4.96 ± 0.42 | 93 | 93.5% | Within threshold |
| DSM 56619023 | 9/27 20:44 | 4.89 ± 0.37 | 101 | 91.1% | Within threshold |
| DSM 56582776 | 9/26 15:21 | 4.88 ± 0.31 | 128 | 90.6% | Within threshold |
| MMPQ 56624842 | 9/28 01:12 | 4.85 ± 0.44 | 86 | 93.0% | Within threshold |
| DSM 56571979 | 9/26 06:46 | 4.60 ± 0.43 | 96 | 93.8% | Within threshold |
| DSM 56614734 | 9/27 17:07 | 4.60 ± 0.34 | 120 | 90.0% | Within threshold |
| MMPQ 56612150 | 9/27 15:03 | 4.57 ± 0.27 | 120 | 82.5% | Within threshold |
| DSM 56629969 | 9/28 05:22 | 3.40 ± 0.96 | 30 | 100% | Latest version not converged |

The best versions of the eliminated teams: DECEM 56622102 at 4.19, Vadim 56614976 at 3.92; Boey has not submitted any new versions since 9/24, thus failing the recent submission criterion; his only version under the same model is 3.86. When only using 9/26 retraining after 12:00, all top seven teams belong to the first eight rows of the above table (56571979 has very few matches in this time window). Within the same time window, team matchups: DSM vs. MMPQ, DECEM, Vadim, and Boey yield 42/57, 26/31, 59/69, and 38/53 respectively; MMPQ beats all other three teams by a majority.

All previously downloaded games from the selected version are included in the data, without filtering by win/loss or opponent: DSM 696 games, MMPQ 206 games. The 20 games where both sides are selected retain two trajectories. The standard deviation is taken from the diagonal of the posterior curvature, ignoring covariance between versions. [Select and Full Rating Table](../outputs/datasets/derived-v5b-strength-top-canonical-20260928-train-val-q100/source-manifests/selection.json).

## 2. Market Label Normalization: Keep Only Valid Requests That Are Actually Effective

Native settlement is conducted by **slot**: both parties process the k-th slot simultaneously, with laborers and land purchases executed first, followed by remaining orders being matched unit by unit in alternating fashion; sell orders terminate if the warehouse is empty, buy orders if cash is insufficient or the warehouse is full. Empty slots have no effect on themselves but still occupy the slot.
The normalized process uses the native engine to replay the entire game according to official actions, reading the actual volume traded at each slot:

1. Remove requests that cannot be parsed and requests with a volume of 0;
2. Merge only adjacent requests of the same type and same commodity quantity, such that the merged single request does not exceed 100;
3. The relative order and number of remaining requests are preserved unchanged.

Do not reorder different requests, as cash and warehouse capacity give order economic significance: for example, in Game 5 of Boey's match, cash is only 2–227, relying on the cycle "buy wheat → sell wheat → buy fertilizer → sell wheat → buy wheat". Normalization only modifies labels; encoded features are entirely derived from official observations, and the array bits remain unchanged.

For each turn, execute the original and normalized actions from the same official state and compare (also confirm that the engine replay matches the official state):

| Metric | Value |
| --- | ---: |
| Teacher turn | 634,158 |
| Teacher's farm and warehouse completely consistent | 99.79% |
| Full state consistency between both sides | 99.75% |
| Original request → Normalized order | 868,974 → 798,562 |
| Discarded zero trades / Merged adjacent orders | 20,069 / 50,343 |
| Maximum cash difference per teacher turn | 82 |

The differences arise from alternating price path changes when sharing the same hand with opponents; on the opponent side, the maximum per turn is 398, due to a 2-yuan difference resulting in one less cow being purchased.
The newly selected DSM and MMPQ versions have no empty slots left, so the gains primarily come from no longer using high-noise teachers: in a trial game, Boey had 6,004 requests, of which 1,472 were empty slots and 3,000 had zero trades; after normalization, only 1,389 orders remained.

## 3. Loss: by field mean, market field multiplier 3.5

Add `field_mean` normalization: weights are multipliers for each field, with the denominator being the weighted sum of all supervised fields across the entire batch.
The unit side and market side apply equal weighting per field internally, and the combined market domains maintain the original 40% of the five-domain equal-weight target.
An exact multiplier of 3.49 is derived from the number of fields in the training set, rounded to **3.5**:

| Domain | Training Field Count | Old: Field Relative Weight | New: Field Relative Weight | New: Target Share |
| --- | ---: | ---: | ---: | ---: |
| Target Cell (Movement) | 6,181,761 | 1.0 | 1.0 | 38.39% |
| Unit Operations | 3,265,185 | 1.9 | 1.0 | 20.28% |
| Unit Count | 204,090 | **30.0** | 1.0 | 1.27% |
| Market Operations | 1,340,288 | 2.6 | 3.5 | 29.13% |
| Market Count | 503,336 | 4.6 | 3.5 | 10.94% |

The "old" column is derived from the s96001 data of the previous turn. In the old design, the quantity field began training from the 2nd epoch with NLL going from 0.20 to 0.066 on training and 0.205 to 0.251 on validation. In the new design, this field is only counted according to its natural frequency. The number of field entries per trajectory differs by no more than 15% between the two teams, so additional teacher normalization is no longer performed. No weighting is applied to rare categories such as "buying geese," because amplifying only the positive cases would systematically increase the purchase frequency during sampling.

[Derivation Record](../outputs/analysis/strength-canonical-bc-20260928/loss-weights.json)

## 4. Data and Training Agreement

[Data Entry Point](../outputs/datasets/derived-v5b-strength-top-canonical-20260928-train-val-q100/manifest.json)
SHA256 `052d0f7883259bc064be9dcc6738c90746cbab19965bb172ddf0fab548b09b5c`:
882 games / 902 trajectories, DSM 696, MMPQ 206. Training: 829 games / 847 trajectories / 608,993 turns,
Validation: 53 games / 55 trajectories / 39,545 turns; all turns are supervised, 146 turns have q100 truncation.

Validation uses only the selection bucket of seed 62001. This bucket has never been part of any previous training; the confirmation bucket was previously used as training data for s96001, and the current weights inherit from it, thus it is not included in validation.

s97001 received a stop signal at **07:52:13 UTC** and normally stopped at **U590 / 75,520 games**,
`checkpoints/update-000590.pt` SHA256
`c9a5d536b3adeaf5dc7f74dbf51889f5841a479722f15d046868d9fbc780223e`,
the optimizer, dual rank RNG, historical pool, and PFSP state are all preserved.

**07:53:30 UTC** Start dual-card BC ([configuration](../configs/learning_strength_canonical_bc_20260928.yaml)):

- Inherit U590 Actor, create new BC Adam; keep LR at **1e-5** constant, with 8 full trajectories per batch and 48 turn gradient blocks.
- Perform 106 batches per epoch with full validation; maximum of **40 epochs**, and early stop if validation objective fails to improve by at least **0.0005** across 4 consecutive validation rounds; save weights every 2 epochs, and at termination, use the validation optimal point as `rl_initial`.
- `pretraining_only: true`, stop BC after completion, do not automatically proceed to RL.

## 5. Verification

- Data: 2,646 array hashes, 882 unique environment seeds; covers all 9 versions and two splits
  14 re-encoded (including normalization) bit-identical runs, totaling 10,066 lines; 20,160 official observations consistent.
  See [Data Verification](../outputs/analysis/strength-canonical-bc-20260928/data-verification.json).
- Initialization: 351 Actor tensors match U590 bit-for-bit, see
  [Initialization Verification](../outputs/analysis/strength-canonical-bc-20260928/initialization-verification.json).
- Runtime: 160th checkpoint saved at Adam step 160, LR 1e-5; 339 tensors updated; model and optimizer finite,
  both rank RNGs fully intact, loss identity as above `field_mean`, see
  [Runtime Verification](../outputs/analysis/strength-canonical-bc-20260928/running-verification.json).
- Training logs record the same number of training and validation fields as offline counts.

Epoch 1: U590's initial target on the first batch of new data is 0.440 (market operation accuracy 87.8%, market count 78.7%);
after epoch completion, validation target is 0.177, market operation NLL is 0.205 / accuracy 92.2%, market count is 0.41 / 86.2%.
These are per-field metrics under the teacher state, not indicative of competitive strength.

## 6. Code and Reproduction

- `datasets/sequences/strength.py`: Win/loss extraction, Bradley–Terry fitting, and version selection rules.
- `datasets/sequences/versions.py`: Freeze snapshot, output each team's `selected.json` and scoring report.
- `datasets/demonstrations/canonical.py`: Normalization based on settlement trajectory and turn-by-turn comparison.
- `datasets/sequences/prepare.py`, `verification.py`: `canonical_market` switch;
  When disabled, configuration identity is not entered, and existing datasets remain unaffected. During verification, native features and official audit continue to use official actions.
- `learning/pretraining/{config,objectives,telemetry}.py`: `field_mean` normalization,
  the original `domain_mean` numerical trajectory remains unchanged; `test_objectives.py` introduces block partitioning and validation target alignment.

```bash
PYTHONPATH=src .venv/bin/python -m kagg_revue.datasets.sequences.versions \
  --config-name sequences_strength_canonical_20260928
PYTHONPATH=src .venv/bin/python -m kagg_revue.datasets.sequences.prepare \
  --config-name sequences_strength_canonical_20260928
PYTHONPATH=src .venv/bin/python -m kagg_revue.datasets.sequences.verification \
  --config-name sequences_strength_canonical_20260928
CUDA_VISIBLE_DEVICES=0,1 TMPDIR="$PWD/tmp" PYTHONPATH=src \
  .venv/bin/python -u -m kagg_revue.learning.cli \
  --config-name learning_strength_canonical_bc_20260928
```

Ruff, mypy passed; BC target test 6 items passed.

## 7. Limitations

Without a control experiment, the individual contributions of the three modifications cannot be distinguished. The data is approximately half of the previous round, with DSM accounting for 77%; strategy diversity has decreased, which is intentionally chosen. The validation set contains only 55 trajectories. Version selection depends on snapshots at freeze moments, and the latest DSM version includes only 30 games. Normalization alters the alternating outcomes between opponents in about 0.2% of turns.
