# Two-day historical top-ten BC → formal RL

The user has accepted the [new BC dataset](top10_two_day_bc_20260913.md) and requests to pause the current training, retrain for 4 epochs of BC, then proceed to formal RL, and add the current training to the opponent pool.

## Prior Execution and Historical Pool

`budget-q100-3d-20260912-s67001` has normally stopped at **U1519**.
The Actor, Critic, two optimizers, and two independent GPU RNGs have been fully saved; each optimizer has accumulated **31,899 steps**, and all checkpoint tensors are finite. The parent process and two training workers have both exited, and the runtime lock has been released.
See [Stop Verification](../outputs/analysis/top10-training-20260913/old-stop-verification.json).

Historical opponents retain the original 32 external models, plus the 25 versions that have been terminated this time: the BC endpoint, all 23 snapshots from U64 to U1472 (every 64 turns), and the final U1519.
A total of **57 external models** are preserved, all verified by source state hash, checkpoint hash, and bloodline authentication.
These models are solely frozen as opponents; the new learners start from random initialization, and match statistics are reaccumulated.

The neural history pool capacity has increased from 64 to **96**, with 57 external versions fixed in retention, reserving 39 slots for the self-history of new runs; every 64 turns, a new snapshot is added, continuing the retention strategy of earlier stages and the most recent snapshot.
All selected model quantity tables, budget feature compatibility, and Actor finite value checks have passed.
See [Historical Source Acceptance](../outputs/analysis/top10-training-20260913/historical-preflight.json).

## BC and RL Formulations

Configured formally as [learning_top10_2d.yaml](../configs/learning_top10_2d.yaml), run directory is
`outputs/learning/budget-q100-top10-2d-20260913-s68001`.
Random root **68001**, run ID `db598303f1c047a188c6432544dad4a2`, no previous learning agent weight inputs.

BC uses [manifest.json](../outputs/datasets/grounded-v2-top10-20260911-12-q100/manifest.json),
SHA-256 `8f27747120b10c6de3aa907546a6b8857fb47a5febd3bc153632b871431249f9`.
451 training shards, 3,277,090 rows per epoch, 13,108,360 rows over 4 epochs,
52,244 optimization steps. Line-by-line uniformly weighted full traversal, batch size 256, AdamW LR 1e-4, two-GPU synchronized training;
NLL is computed using selection per epoch, and 4 behavior checks are completed per epoch.
Retains the grounded-v2 backbone and budget features, with a fixed quantity classification set ranging from 1 to 100.

After the complete BC ends, authenticate and import the historical model for the same official process, automatically initiating PPO:

- 100,000 update, 128 games per turn, two GPUs; logical batch 5,760, micro-batch 2,880.
- 30% self-play, 20% independent dynamic native scripts, 50% historical PFSP, precisely balanced over five turns.
- Scripts: router_95, farming_v4, kaito_v58, shop_router_0908, shop_router_0909.
- T=1, Actor LR 7.5e-6, Critic LR 1e-4; fully saved every 4 turns.
- Online training seed range is `[3,800,000,000, 3,812,800,000)`; selection, confirmation,
  BC behavior checks start from 3,820,000,000, 3,821,000,000, 3,822,000,000 respectively.
  Verified to have no overlap with any seed in the current BC matches, nor with the existing local training intervals.

## Acceptance and Operational Status

Training, strategy, native engine, demonstration loader, and Torch are consistent with the previous formal run, reusing previously validated components.
[Two-GPU BC → PPO → Archive Recovery Verification](../outputs/analysis/latest3d-20260912/qualification.json).
This round re-verified data identity, training budget, seed range, and all 57 external historical sources.
Ruff, mypy (733 files), and 12 PFSP/demonstration-related tests passed.
See [Configuration Verification](../outputs/analysis/top10-training-20260913/preflight.json) and
[Source Code Differences and Checks](../outputs/analysis/top10-training-20260913/checks.json).

Formal dual-GPU BC has begun actual parameter updates, with full array hash verification passed.
Initial complete checkpoints have been validated for new random root, data identity, Actor updates, optimizer steps, dual-GPU RNG preservation, and limited tensor.
See [BC Startup Verification](../outputs/analysis/top10-training-20260913/formal-bc-start-verification.json).
After completing 4 epochs, the current training workflow will automatically authenticate and import the aforementioned 57 external models and initiate formal RL.
This startup record does not indicate that BC has been completed or that RL has started.
Actual stage and progress should be referenced from [learning-progress.json](../outputs/learning/budget-q100-top10-2d-20260913-s68001/learning-progress.json) and [run-status.json](../outputs/learning/budget-q100-top10-2d-20260913-s68001/run-status.json).
See [Official Startup Record](../outputs/analysis/top10-training-20260913/formal-launch.json).
