# Why RL Becomes Stronger First, Then Degrades (Diagnosis on 2026-09-29)

**Conclusion:** Approximately 100–200 updates corrected systematic errors in the BC system, during which gradient directions were consistent and gains were significant. After that, about 97% of the energy in each update was noise, and the training process contained no force pulling the policy back toward strong team behaviors (the sequence learner `bc_weight` was fixed at 0, and PPO's clip/KL only constrained per-update changes). As a result, the parameters performed a random walk, and the likelihood of strong team actions degraded linearly with the number of updates; after warmup ended, the learning rate reached its maximum, accelerating the drift, and the performance eventually declined back to near the BC starting point.

## Evidence

**1. Parameter trajectory is a random walk** (`evaluation/diagnosis/geometry.py`, result `outputs/analysis/rl-drift-20260929/`).
Direction cosines of adjacent 64-update fragments: s99001 from U64→U128 is 0.098, then drops to 0.017–0.030; s100201 decreases from 0.086 to 0.031.
After learning rate reaches full value, step size per fragment stabilizes at approximately 0.38; predicting from U256 with initial value 0.445 over 6 steps via random walk yields 1.03, while actual measurement at U616 is 1.041.
A cosine of 0.025 implies that the portion of energy with consistent direction per update segment accounts for about 2.5%; over the first 100 updates, this amounts to approximately 10%.

**2. The Critic almost does not reduce variance.** The variance of pure WDL rewards is approximately 1; the standard deviation of advantages for s100201 and s100101 throughout training is about 0.95, explaining only about 5% of the reward variance (due to insufficient training of the new Critic and inadequate warmup); for s99001, the reward based on cash difference estimation accounts for approximately 30%.
The terminal ±1 is distributed via Monte Carlo method over all action fields across 719 turns with γ=λ=1, updating 192 trajectories per step using 4-step Adam.

**3. Deviation from strong team actions grows linearly with update count** (`evaluation/diagnosis/drift.py`, 9/29 MMPQ/DSM validation trajectory):

| Checkpoint | Unit Goal NLL | Market Operation NLL | Teacher Probability at Buy Goose Moment | Strength (Clone Panel / Opponent Panel) |
| --- | ---: | ---: | ---: | --- |
| s99001 U0 | 0.172 | 0.360 | 0.748 | 60.9% / — |
| s99001 U192 | 0.220 | 0.399 | 0.671 | 67.8% / — |
| s99001 U256 | 0.244 | 0.418 | 0.648 | 68.4% / — |
| s99001 U512 | 0.344 | 0.498 | 0.524 | 65.0% / — |
| s99001 U1061 | 0.517 | 0.678 | 0.549 | 59.8% / — |
| s100201 U0 (DSM Clone) | 0.189 | 0.356 | 0.674 | — / 56.6% |
| s100201 U100 | 0.209 | 0.378 | 0.707 | 73.3% / 65.2% |
| s100201 U200 | 0.242 | 0.412 | 0.695 | 76.4% / 66.4% |
| s100201 U300 | 0.273 | 0.442 | 0.736 | 78.0% / 62.3% |

During random walk around the BC optimal point, the likelihood loss grows quadratically with displacement, i.e., linearly with the number of updates, consistent with observations. Both trajectories reach a peak in unit target NLL around 0.22–0.24 (about 30% higher than the starting point), after which they diverge and weaken. s99001 simultaneously loses its buying preference, while the DSM clone starting from s100201 does not.

**4. Repeatability.** s100301 (seed changed from s100201) outside panel: U100 65.0%, U150 64.8%, U200 59.5%, U250 60.7%;
direct matchup: s100201 vs U200 achieves 55.7% and remains first, while s100301 vs U250 achieves 44.5%. Peak performance positions vary with seed (U100–U200).
s100201 U300 performs best against clones within the training pool (78.0%), but drops significantly against external opponents (62.3%), indicating overfitting to the training pool.

**5. The learning rate determines the drift speed.** s100101 restarted from U200, with the learning rate warmed up from 0; after 300 updates, there was neither improvement nor degradation;
s99001 began degrading after the learning rate reached its maximum on U300. The KL divergence increased from 0.0008 to 0.0035 with each update, and never triggered early stopping at 0.05.

**Exclusions:** Reward shaping (both cash difference and pure WDL exhibit the same pattern); entropy collapse (per-operation entropy drops from 0.045 to 0.032); KL constraint (never activated). Self-play accounts for 50%, and for s99001 after U308, 25%–38% of PFSP opponents are self-snapshots, resulting in a self-play win rate consistently around 50%, providing no corrective signal for "overall weakening".

## Improvement Directions (by Priority)

1. **Anchor Teacher:** Add KL or BC retention loss to the BC/teacher strategy, keeping the per-unit target NLL within about +30% of the starting point.
   Sequence learners are currently not supported (`learning/adapter.py` fixed as `bc_weight: 0.0`); implementation is required.

2. **Improve Signal-to-Noise Ratio:** Pre-train and strengthen the Critic using replay data, enabling the memory model to use GAE or daily bootstrapping; use more game trajectories (e.g., 512 games) per update.

3. **Maintain learning rate at warmup phase level or decay**, and use early stopping based on the pool's external dashboard (current practice).
