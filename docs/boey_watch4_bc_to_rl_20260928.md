# Latest Boey and four-opponent BC → cash-margin RL, inheriting the complete history pool

Pause the current BC according to user request, launch a new RL using the latest complete weights at the time of pause, with terminal cash difference version and inheritance of historical opponent pool. The user further requests that both the current and subsequent training sessions enable high-win-rate opponent frequency reduction.

## BC Stop and New Beginning

`derived-v5b-m384-u1729-boey388-watch4-bc100-20260928-s96001` stopped normally on turn **2,047 / 11,748,182 supervision turns** at **2026-09-28 01:17:46 UTC**.
8 epochs completed, 215 batches completed in the 9th epoch.
The latest full checkpoint is `pretraining/shard-002047.pt`, SHA256:
`04cd1c7e9617a5d50c942399da4ce61f5044f15d4d3f2b6ad04d4b7e02c7d0e0`.
BC Adam is at 2,047 steps; the model and optimizer are both finite, and both rank RNGs are complete; all original run outputs are preserved.
The latest weights were explicitly used; weights from the optimal 7th epoch are separately retained for validation.
See [checkpoint verification](../outputs/analysis/boey-watch4-bc-to-rl-20260928/stop-verification.json).

**01:26:25 UTC** Startup
`derived-v5b-m384-boey-watch4-ppo50-warmup300-20260928-s97001`,
run ID `b8f91e6f10f642969170a94439027cf3`.
Complete v5b, 27,915-dimensional input, 384-turn memory, 351 initial Actor tensors, and latest BC bit-by-bit consistent. New Critic, two sets of PPO Adam and random state.
See [Initialization Verification](../outputs/analysis/boey-watch4-bc-to-rl-20260928/initialization-verification.json).

## Historical Pool and High Win Rate Opponents

Fully inherit s95001's **419 active strategies**, and additionally include the final **U1729**.
With the current BC starting point, the initial pool consists of **421 strategies + 7 native scripts**.
All 420 external strategies are retained with their original identities and sources, with a capacity of **556**, preserving **136 of its historical slots**.
A RL snapshot is added every 64 updates. The scripts remain as `ahmed_v45`, `metacounter_r1`, `shop_router_0913`, `rayk_v38_low_pressure`, `farming_v4_0914`, `ahmed_v53`, `thomas_metav4`.
The archival path is updated, but the actual runtime files and hashes remain unchanged.

Old PFSP game evidence is retained in the original run, while the new Actor begins accumulating opponent win rates from a fresh prior.
Each turn consists of **64 self-play games + 64 unified PFSP games**; the script has no independent quota or minimum allocation.
The high-win-rate opponent rule is explicitly enabled: after the most recent test, if at least **64 valid games** have been played and the effective score rate is at least **95%**, the games enter a review set with a combined **5% PFSP probability**.
Win counts as 1, draw counts as 0.5; time decay does not automatically revoke the held state; if review criteria are no longer met, normal sampling resumes.
The latest snapshot maintains normal coverage. The script and strategy follow the same rules.
See [Pool Verification](../outputs/analysis/boey-watch4-bc-to-rl-20260928/pool-verification.json).

User requests default enablement for subsequent operations; `mastery` settings previously omitted in the new training startup entrypoints for ordinary training, historical pool bootstrap, and BC→RL workflow have been added and written to `AGENTS.md`. Configuration from the old protocol is preserved as saved during recovery. 11 targeted tests, Ruff, and mypy passed; implementation and compatibility details are available in [PFSP Mastery Rules](pfsp_mastery_20260927.md).

## RL Formula and Operation

Starting from **U1**: `reward = WDL + delta / (abs(delta) + 10000)`,
`delta = own terminal cash − opponent terminal cash`, WDL is +1 for a win, 0 for a draw, and -1 for a loss.
`cash_margin={beta: 1.0, cash_scale: 10000.0}`, `cash_weight=0`;
This terminal reward is used for the PPO policy advantage and Critic target.

Reuse the Actor/Critic learning rates from the most recent RL round: **7.5e-6 / 1e-4**,
**300 update linear warmup**, with both learning rates multiplied by `min(update / 300, 1)`.
gamma=lambda=1, dual-GPU BF16, 48 turn gradient steps, 100,000 update budget,
save full state every 4 updates, no automatic evaluation.

The complete source code and configuration with explicit mastery enabled have been frozen during bootstrap. Subsequently, default rules for future training have been added, allowing this session to restart from the prepared U0 checkpoint via archival recovery. A total of 1,980 source files passed identity verification. The training temporary source code directory is part of the active runtime and must not be cleaned during operation. See [Hydra Configuration](../configs/learning_boey_watch4_ppo50_20260928.yaml), [Startup Log](../outputs/analysis/boey-watch4-bc-to-rl-20260928/launch.json), and [Real-time Progress](../outputs/learning/derived-v5b-m384-boey-watch4-ppo50-warmup300-20260928-s97001/learning-progress.json).

**01:32:53 UTC** Full verification completed for **U4 / 512 games** checkpoint: Actor / Critic Adam
Each completed 16 steps, 339 Actor tensors updated, model and optimizer fully finite, dual rank RNG intact.
Terminal cash difference formula error is 0 across all four rounds with two GPUs; 64/64 allocation and PFSP sampling, post-match statistics precisely replayed.
Actual Actor / Critic learning rates for U4 are **1e-7 / 1.333333333e-6**, consistent with 300-round warmup; mastery parameters 64 / 0.95 / 0.05 remain enabled.
U1729 inherited in Round one has been successfully drawn. Old BC and RL ledger hashes unchanged; verification completed U6; training continues. See [formal run verification](../outputs/analysis/boey-watch4-bc-to-rl-20260928/running-verification.json) and [subsequent default rules verification](../outputs/analysis/boey-watch4-bc-to-rl-20260928/defaults-verification.json).

After normal termination, recovery can be achieved through complete self-archival:

```bash
CUDA_VISIBLE_DEVICES=0,1 TMPDIR="$PWD/tmp" PYTHONPATH=src \
  .venv/bin/python -m kagg_revue.learning.recovery.cli \
  recovery.run=outputs/learning/derived-v5b-m384-boey-watch4-ppo50-warmup300-20260928-s97001
```
