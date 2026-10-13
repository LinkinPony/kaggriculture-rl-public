# GTrXL Mixed Opponent and Bounded Terminal Cash Difference

User requests to restore the original script + PFSP + self-play, and explicitly selects the reward.
`WDL + Δ / (|Δ| + 10000)`. Formal operation remains
`outputs/learning/gtrxl-m384-bc100-3d-20260916-s71001`,
Operation ID: `247a1750dfd54ae9ba7cf4ef87537028`.

## Continuation and Opponent

Pure self-play stopped normally after **U922 / 118,016 games**, with continued weights being
`checkpoints/update-000922.pt`, SHA-256
`cac5408bd8a53d652a7bd2e9e06f5480636514a848e162eacb405d10ec01c616`.
Actor / Critic Adam steps at **3685 / 3688**, two-GPU RNG, BC cursor 1240,
training records and historical outputs preserved.

The target ratio is **20% native scripts, 50% historical PFSP, 30% self-play**.
Each turn consists of 128 games, with 64 games fixed from history; native scripts are taken as rounded up totals of 24 or 28 games based on two GPUs and two seats, and self-play accordingly amounts to 40 or 36 games. Native scripts and historical data are independently sampled via PFSP.

Five scripts are `ahmed_v45`, `metacounter_r1`, `shop_router_0913`, `rayk_v38_low_pressure`, `farming_v4_0914`; training directly invokes native C++ implementation.
Restore the original five source runs' 137 frozen models, plus 22 retained models from this run, with migration pool size 159, capacity 177, and snapshots added every 64 turns. PFSP parameters retain original settings: power 2, uniform 0.2, latest 0.1, prior 8, half-life 128, maximum effective games 256.
Complete model selection see [Opponent Switch Configuration](../configs/learning_gtrxl_mixed_change.yaml).

Opponent migration has been registered as `population-revisions/0001`, effective from U923.
Official dual-seat 10-game validation covers all five scripts, with 7,190 script actions and consistent actor features.
Isolated replica completed U923–U930 / 1,024 games, including U926 stop and archival recovery;
Actor and Critic each increased by 24 steps, precise replay of PFSP passed, and all tensor boundedness verified.

## Rewards

`Δ = own terminal cash − opponent terminal cash`, `WDL = sign(Δ)`.
Add explicit configuration `cash_margin: {beta: 1.0, cash_scale: 10000.0}`,
Continue to maintain `cash_weight=0`, `win_weight=1`.
For example, when Δ=10000, the return is 1.5; when Δ=−10000, the return is −1.5; a draw yields 0;
the returns of both sides are opposites, and under finite cash difference, the returns strictly lie in (−2, 2).
The cash difference term uses only the terminal amount; the training optimization objective and the Critic objective use the same combined return.

The absolute amount meaning of old `cash_weight` remains compatible; the archiving protocol of `cash_margin` is not enabled.
Retain original identity. Each actual return is individually verified against the existing independent scalar cash difference, covering all turns, self-play two-seat scenarios, and seats for the learning player facing frozen opponents.
See [Reward Switch Configuration](../configs/learning_margin_change.yaml).

GTrXL architecture, 384 turn memory, Actor LR 7.5e-6, Critic LR 1e-4,
KL 0.05 / early_stop, trajectory and optimizer states preserved per card, 32 trajectories per card.

## Validation and Runtime Status

Reward code passes Ruff, full mypy (812 files), and 39 related tests.
Cash difference replica completes **U923–U926 / 512 games**, including U924 stop and archival recovery.
Actor/Critic each increases by 12 steps; PFSP exact replay, complete optimizer and RNG preservation,
All tensor boundedness passes; for all learning agents across two-GPU four-round scenarios, actual terminal returns in all turns match the independent cash difference formula with a maximum error of **0**.

`reward-revisions/0001` has been registered; only the `cash_margin` protocol field is added.
Source checkpoint, two optimizers, dual-GPU RNG, full recording, pool, and PFSP initial statistics are fully preserved.
Both migrations take effect from **U923**. The formal **U924** checkpoint has passed verification:
256 additional games added, Actor/Critic each advancing 6 steps, parameters updated in both memory modules,
full network and optimizer tensor limits are maintained, dual-GPU RNG independently advances, PFSP exact replay passes.
Actual reward range: −1.922395 to +1.810943; cash difference per-item formula error is 0.
U924 parent checkpoint hash precisely points to U922; BC, source checkpoint, and historical outputs are retained.
**Dual-GPU formal training is running continuously.**

- [Stop Verification](../outputs/analysis/gtrxl-mixed-20260917/stop-verification.json)
- [Mixed Opponent Acceptance Verification](../outputs/analysis/gtrxl-mixed-20260917/qualification.json)
- [Opponent Migration Verification](../outputs/analysis/gtrxl-mixed-20260917/transition-verification.json)
- [Cash Difference Code and Testing](../outputs/analysis/gtrxl-margin-20260917/static-checks.json)
- [Cash Difference Training and Recovery Verification](../outputs/analysis/gtrxl-margin-20260917/qualification.json)
- [Reward Migration Verification](../outputs/analysis/gtrxl-margin-20260917/transition-verification.json)
- [Initiate Official Recording](../outputs/analysis/gtrxl-margin-20260917/launch.json)
- [Official U924 Savepoint Verification](../outputs/analysis/gtrxl-margin-20260917/formal-verification.json)
- [Official Real-time Status](../outputs/learning/gtrxl-m384-bc100-3d-20260916-s71001/learning-progress.json)

Deployment strategy remains unchanged; the above acceptance is for training the correctness of continuation, and does not indicate an improvement in strategy strength.
