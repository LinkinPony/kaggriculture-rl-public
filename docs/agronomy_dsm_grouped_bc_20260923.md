# U1609: Grouped Loss BC on DSM Six Version Data

Stop the current PPO according to user request, take the latest complete Actor at the time of stop, and use the specified DSM to start an independent BC with the train / val data. The loss employs the newly implemented five-action-wise normalization scheme.

**Post-status:** The user requested a transfer to PPO on September 23. This BC has been normally terminated at the latest **batch 977** at **01:50:47 UTC**, completing **12 epochs + 5 batches / 5,591,663 supervised turns**.
The checkpoint has been used to initiate [s80001 PPO](agronomy_dsm_grouped_ppo_20260923.md), and the full BC historical output is preserved.

## Parent Run and Initial Weights

`agronomy-v4-m384-watch2-ppo-20260922-s78001` at **2026-09-23 01:33 UTC**
Normal save and stop, ending at **U1609 / 205,952 games RL**.
Supervision process and two GPU worker processes have exited, write lock has been released. Actor/Critic Adam took 4,827 steps each,
double rank RNG, PFSP, and full checkpoint passed verification, historical outputs retained.

Parent checkpoint: `checkpoints/update-001609.pt`, SHA256:
`9b5bd8d1e2a51f292e384900af0f6c5ed168741d695a651b1f19bc2b5afd4d60`.
The new run's initial Actor consists of exactly 347 tensors and is identical to the parent Actor.
Create a new BC Adam, using a new seed; the optimizer and RNG of the parent PPO are not used as the initial state of BC.

See [Stop Verification](../outputs/analysis/dsm-grouped-bc-20260923/stop-verification.json),
[Initial Weight and Recovery Verification](../outputs/analysis/dsm-grouped-bc-20260923/initial-verification.json).

## Data and Training Agreement

Fixed usage of [DSM six-version dataset](dsm_bc_20260921_23.md): official submission time coverage
**9/21 00:00 to 9/23 01:07 UTC** of 6 versions, supervising only DSM.
The game with timeout anomaly `112052628` has been excluded; 2,040 array hashes have passed reconfirmation and are retained;
10 full official replays, 14,400 observations have been verified.

Entry: [manifest.json](../outputs/datasets/agronomy-v4-dsm-20260921-23-train-val-q100/manifest.json),
SHA256: `1ec40de77e1f17045e33b4cedabb199ed815c6b036f56ff4d96e511d65e98475`.

| Project | Configuration |
| --- | --- |
| Training set | 645 trajectories, 463,755 supervised turns |
| Validation set | 35 trajectories, 25,165 supervised turns |
| Test | None; original confirmation has been incorporated into train as per user request |
| Actor | 16 × 384, 384-turn memory, v4 features, q100 |
| Loss | `domain_mean`, all five weight categories set to 1 |
| Budget | 100 epochs, 8,100 Adam steps, 46,375,500 supervised turns |
| Learning rate | Fixed at 1e-4 |
| Hardware and precision | GPU0 + GPU1, BF16 computation, FP32 parameters/Adam |
| Batch size | 8 full trajectories globally, 4 trajectories per card, 48 turn sequence blocks |
| Per epoch | 81 training batches, 5 full validation batches |
| Saving | Saved every 16 batches and at epoch boundaries, including Adam states, dual rank RNG, data cursor, and loss identity |
| Termination | No early stopping; automatically stops after 100 epochs, does not automatically enter PPO |

Five categories: target unit, unit operation, unit quantity, market operation, market quantity. The denominator covers the entire global scope.

Optimize batch size; for training, include 5 trajectory samples in the tail batch, and 3 trajectory samples in the validation tail batch; all other filled samples are not counted toward loss.

Validation first aggregates counts across all categories based on the entire val partition, then combines NLL. See [Loss Description](grouped_bc.md).

This is a purely supervised training run, with no cash or intermediate rewards added, and no SE-specific weights included.

## Run and Recovery

New run `agronomy-v4-m384-u1609-dsm-grouped-bc100-20260923-s79001`
Started at **01:36 UTC**, run ID `a3ffc4610a0d4d30a904929156f362fb`.
Configuration: [learning_agronomy_dsm_grouped_bc_20260923.yaml](../configs/learning_agronomy_dsm_grouped_bc_20260923.yaml).
See [Data and Batch Verification](../outputs/analysis/dsm-grouped-bc-20260923/data-verification.json),
[Configuration Parsing](../outputs/analysis/dsm-grouped-bc-20260923/resolved-training-config.json)
and [Startup Log](../outputs/analysis/dsm-grouped-bc-20260923/launch.json).

After normal termination, recovery should be performed via source code archive, preserving the original loss, data, Adam states, and random states:

```bash
CUDA_VISIBLE_DEVICES=0,1 TMPDIR="$PWD/tmp" \
  .venv/bin/python -m kagg_revue.learning.recovery.cli \
  recovery.run=outputs/learning/agronomy-v4-m384-u1609-dsm-grouped-bc100-20260923-s79001
```

## Official Training Acceptance

**Batch 96 / 550,035 turns** complete checkpoint verified and a copy preserved in the analysis directory.
1 epoch completed; group-weighted NLL for full-val in Round one is **0.1732197785**; independent recalculations of the five validation metrics confirm consistency. Adam steps: 96, learning rate: 1e-4, all tensors finite, double rank RNG fully intact. Encoder: 218 tensors, memory: 69 tensors, unit action heads: 12 tensors, market action heads: 8 tensors updated.

Grouped by actual trajectory, randomized by round and re-calculated in reverse order; supervision turn count is fully consistent. Parent run ledger and U1609 hash are preserved, source code archive can be fully restored. Warm-state median **0.740 seconds/batch**; this RL update is 0, no test partition. Monitoring audit of batch 125, type BC, status running, training continues. See [formal verification](../outputs/analysis/dsm-grouped-bc-20260923/formal-verification.json) and [monitoring audit](../outputs/analysis/dsm-grouped-bc-20260923/monitor-response.json).
