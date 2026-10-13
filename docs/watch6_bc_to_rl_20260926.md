# Latest Six-Party BC → PPO, inheriting complete s82001 historical pool

**Subsequent Reward Revision:** Based on user request, the process will be halted at U10 on 2026-09-26, retaining full state; starting from **U11**, it will switch to **`WDL + delta / (abs(delta) + 10000)`** and continue the current operation.
See [Cash Difference Reward Explanation](watch6_rl_margin_20260926.md). The original startup protocol and verification records are retained below.

Stop the six-party BC as per user request; at the time of stop, initiate a new RL with the latest Actor; inherit the complete activity history pool from the previous RL, and additionally include the final U3243 strategy from the previous RL itself.

## Latest Weights

`derived-v5b-m384-u3243-watch6-bc100-20260926-s90001` stopped normally on turn **7,293 / 41,854,607** at **2026-09-26 02:16:04 UTC**.
29 epochs completed, and 130 batches of the 30th epoch completed. The most recent full checkpoint at termination is retained.
Original BC Adam, dual rank RNG, epoch weights, and training records are preserved.

Starts at `pretraining/shard-007293.pt`, SHA256:
`872dd30c59081c63a7140a07f164c3e34b8eb550037cb558497284ab40dbfd22`.
Stop ledger SHA256:
`347b89e7733d6f7222c5db16bc7cd104c4ed8d63e158a548287f6c454b5649cc`.
The new RL initial Actor's **351 tensor**s match bit-by-bit with this checkpoint; full v5b, 27,915-dimensional input,
384 turn memory. New Critic, PPO Adam, and RNG.
See [Stop Verification](../outputs/analysis/watch6-bc-to-rl-20260926/stop-verification.json) and
[Start Verification](../outputs/analysis/watch6-bc-to-rl-20260926/initialization-verification.json).

## Historical Pool and Protocol

The previous round RL was `agronomy-v4-m384-dsm-games-ppo50-20260924-s82001`,
stopped at **U3243 / 415,104 games**, stop ledger SHA256:
`3423476f6cd31bbf26caa75fe6a25bf4ab2b00acff4d99658073a8d63835bdc8`.

Inherits all **355 active strategies**: 304 external historical ones, 51 from its own origin and snapshots;
Adds the final **U3243** not present in the active pool, totaling **356 external strategies**.
Plus the new BC origin, totaling **357 strategies + 7 native C++ scripts**.
The identity of the final U3243 is
`ece90a347c5864dbccb0fcf322102feaefffeab5ebd8b0baee04ca15128b6f7f`.
Strategy capacity is **492**, retaining 136 slots for its own historical records, with a new RL snapshot added every 64 turns.

Continue using `ahmed_v45`, `metacounter_r1`, `shop_router_0913`, `rayk_v38_low_pressure`,
`farming_v4_0914`, `ahmed_v53`, `thomas_metav4`.
Verify each item of the previous strategy identity and origin; retain native engine evidence for v2/v4 feature compatibility.
Preserve the previous PFSP game evidence in original operation, and the new learner uses new priors.
See [Selection List](../outputs/analysis/watch6-bc-to-rl-20260926/opponent-selection.json).

Retain the RL protocol effective at s82001 termination: pure terminal game **WDL: win +1, draw 0, loss -1**.
Each turn consists of **64 self-play games + 64 uniformly applied PFSP games**; the script has no independent quota or guaranteed allocation.
Actor/Critic learning rates: **7.5e-6 / 1e-4**, gamma = lambda = 1, no warmup.
Dual-GPU BF16, 48-turn gradient batches, 100,000 turn budget, full checkpoint saved every 4 turns.
No automatic evaluation at startup, periodic intervals, or end of run. The protocol only modifies the starting point, running identity/seed, and source/capacity of the historical pool.

Configuration see [learning_watch6_ppo50_20260926.yaml](../configs/learning_watch6_ppo50_20260926.yaml),
differences see [Agreement Verification](../outputs/analysis/watch6-bc-to-rl-20260926/protocol-diff.json).

## Startup and Recovery

**2026-09-26 02:22:56 UTC** Startup
`derived-v5b-m384-watch6-ppo50-20260926-s91001`,
run ID `aefa5349e25e44ceb948971f0b86f2ce`. First import the complete historical pool via bootstrap, then execute PPO from the new initial state. Before startup, verify the actual file hashes, configurations, and source code identities of all active weights; the original BC, RL ledgers have not been modified, and the script execution during this round is identical to the previous one.
All four import modules passed Ruff and mypy checks.

See [Historical Pool Verification](../outputs/analysis/watch6-bc-to-rl-20260926/pool-verification.json),
[Startup Log](../outputs/analysis/watch6-bc-to-rl-20260926/launch.json), and
[Real-time Progress](../outputs/learning/derived-v5b-m384-watch6-ppo50-20260926-s91001/learning-progress.json).

**02:32:53 UTC** Full verification completed for **U4 / 512 games** checkpoint, SHA256:
`9c7c638470d764d2d15bb048a7dc6e4af980720c982702b5a1aaef7b7b4c5b20`.
Actor / Critic Adam each completed 16 steps, 339 Actor tensor updates performed, all model and optimizer tensors bounded,
dual rank RNG fully intact. In the first four rounds, each round actually executed 64/64, with pure WDL rewards per rank.
Learning rates set at 7.5e-6 / 1e-4. All PFSP sampling and post-game statistics can be exactly replayed from a fresh run start.
Old BC, RL ledger hashes remain unchanged; training continues, verification completed at U5.
See [formal run verification](../outputs/analysis/watch6-bc-to-rl-20260926/running-verification.json).

After normal shutdown, restore the archived code and complete state from this run:

```bash
CUDA_VISIBLE_DEVICES=0,1 TMPDIR="$PWD/tmp" PYTHONPATH=src \
  .venv/bin/python -m kagg_revue.learning.recovery.cli \
  recovery.run=outputs/learning/derived-v5b-m384-watch6-ppo50-20260926-s91001
```
