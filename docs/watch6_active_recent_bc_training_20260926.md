# U3243 → BC on active and recent data from six opponents

**Next State:** Stopped normally as per user request at
**2026-09-26 02:16:04 UTC** at
Turn **7,293 / 41,854,607** of supervision, full state preserved.
Latest Actor for [new RL and historical pool inheritance](watch6_bc_to_rl_20260926.md).
The original startup and verification records of this BC are retained below.

After completing all acceptance tests on the [Six-Party Dataset](watch6_active_recent_bc_20260926.md) as per user requirements,
send a normal stop signal to s82001 RL at **2026-09-26 00:27:44 UTC**.
The original training was saved and stopped at **00:28:14 UTC** at **U3243 / 415,104 games**, with the restored supervision process exiting with code 0.
The complete Actor, Critic, two sets of Adam optimizers, dual rank RNG, PFSP, and historical data are all preserved.
See [Stop Verification](../outputs/analysis/watch6-active-bc-20260926/stop-verification.json).

Latest complete weights at latest fixed stop for new BC:
`agronomy-v4-m384-dsm-games-ppo50-20260924-s82001/checkpoints/update-003243.pt`,
SHA256 **`ece90a347c5864dbccb0fcf322102feaefffeab5ebd8b0baee04ca15128b6f7f`**.
Original running stop ledger SHA256:
`3423476f6cd31bbf26caa75fe6a25bf4ab2b00acff4d99658073a8d63835bdc8`.

**00:29:57 UTC** Launching dual-GPU BC
`derived-v5b-m384-u3243-watch6-bc100-20260926-s90001`,
run ID **`49397af989324c24bf03c59ef52862c0`**.
Using full v5b, 27,915-dimensional input, 384-turn memory; initial Actor's 351 tensors match U3243 bit-by-bit.
The complete parent checkpoint is saved in the new run `weight-transfer/parent.pt`; BC creates a new Adam optimizer and random seed.
See [Launch Log](../outputs/analysis/watch6-active-bc-20260926/launch.json) and
[Start Verification](../outputs/analysis/watch6-active-bc-20260926/initialization-verification.json).

## Data and Training Agreement

Fixed **1,874 games / 2,078 trajectories / 22 submission versions**, including 108 trajectories from our side.
Five opponents use the union of the currently active public versions and submission versions starting from Beijing Time 9/25 00:01;
Our side uses existing games starting from that time, supplemented only with our own seats.
Training on **1,972 trajectories**, validation on **106 trajectories**, all data has passed hash, identity, split, and official replay confirmation.
Data manifest SHA256:
`e931b6bd87ec3546b20ece61220b2ea11bef17c6f445da05af544009917c7ea7`.

Continue using the recent BC protocol: learning rate **1e-5**, **100 epochs, no early stopping**,
five action groups with equal weights, BF16 computation, FP32 parameters and Adam optimizer.
Global 8 complete trajectories, 4 per GPU, 48 turns per gradient block; **247 training batches and 14 validation batches per epoch**.
Save full state every 16 batches and at epoch boundaries, and retain epoch weights. Stop after BC completion.

Configuration see [learning_watch6_active_recent_bc_20260926.yaml](../configs/learning_watch6_active_recent_bc_20260926.yaml),
real-time status see [learning-progress.json](../outputs/learning/derived-v5b-m384-u3243-watch6-bc100-20260926-s90001/learning-progress.json).
Continuous data collection will continue to run; subsequent replay additions will not alter the data frozen in this instance.

**00:34:28 UTC** Full checkpoint verified for the **80th / 460,074 cumulative supervision turns**.
Adam's state is 80 steps, actual LR **1e-5**, 339 actor tensors updated;
Model is FP32, all model and optimizer tensors are finite, double rank RNG is complete.
Training reader re-verified all data arrays, two GPU workers are running normally, original RL has stopped and ledger hash remains unchanged.
See [run verification](../outputs/analysis/watch6-active-bc-20260926/running-verification.json).

After normal shutdown, restore the archived source code and complete state from this run:

```bash
CUDA_VISIBLE_DEVICES=0,1 TMPDIR="$PWD/tmp" PYTHONPATH=src \
  .venv/bin/python -m kagg_revue.learning.recovery.cli \
  recovery.run=outputs/learning/derived-v5b-m384-u3243-watch6-bc100-20260926-s90001
```
