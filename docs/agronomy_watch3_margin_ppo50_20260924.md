# Three-party BC Transition to 50% Self-play PPO with Cash Differential Reward

**Next state:** User requested to halt this run, which was normally stopped on **2026-09-24 09:05:12 UTC** at
**U12 / 1,536 games**. The current setting is now [resume s82001 and disable automatic baseline evaluation](s82001_resume_no_evaluation_20260924.md),
the full status of this run is retained.

User requests to terminate the current BC, initiate a new RL with the latest weights, inherit the opponent pool from the previous round, and switch to the previous cash difference version.
The currently running setup uses an explicitly authorized terminal reward:

`WDL + delta / (abs(delta) + 10000)`, where `delta = own terminal cash - opponent terminal cash`.

Configured as `cash_margin={beta: 1.0, cash_scale: 10000.0}`, `cash_weight=0`,
WDL coefficient is 1; absolute cash or intermediate cash rewards are not used. Other loss settings for PPO are inherited from s82001.

## BC Endpoint and New Operation

s83001 `agronomy-v4-m384-u113-watch3-bc100-20260924-s83001` at
**2026-09-24 08:45:18 UTC** normally stopped at **turn 720 / 7 complete epochs + 62 turns**,
with a total of **4,130,174 valid supervised turns**, BC Adam at 720 steps, dual rank RNG and original products preserved.
Latest checkpoint `pretraining/shard-000720.pt`, SHA256:
`9ff5aee5ae67c85f0b3aa78c80dbddf8f3bcfcd8ebcf8577e7ac9c2dff3d759b`.
See [BC Stop Verification](../outputs/analysis/watch3-bc-to-ppo-20260924/bc-stop-verification.json).

New run **`agronomy-v4-m384-watch3-margin-ppo50-20260924-s84001`** started at
**08:49:36 UTC** running GPU0 + GPU1, run ID `ef8038d98c514b1781c79b179b7a0e9f`.
The initial Actor's **347 tensors** match exactly with BC Batch 720; new PPO Actor/Critic Adam and Critic are created, with new run seed 84001. See [Start Verification](../outputs/analysis/watch3-bc-to-ppo-20260924/initialization-verification.json),
[Startup Log](../outputs/analysis/watch3-bc-to-ppo-20260924/launch.json) and
[Hydra Configuration](../configs/learning_agronomy_watch3_margin_ppo50_20260924.yaml).

## Inherited Opponent Pool

Import ledger from frozen ledger of s82001 `agronomy-v4-m384-dsm-games-ppo50-20260924-s82001`:

- 304 external historical strategies, fully preserving original member hashes, sources, and layouts.
- s82001's own starting point with U64, covering all 306 of its active historical strategies.
- Incorporating s82001's final U113, totaling 307 external strategies.
- Retaining the original 7 native C++ scripts; unified with strategies under PFSP, with no separate script quotas.
- Adding the new Actor's starting point, resulting in **308 strategies / 315 initial candidates**.

Capacity adjusted to **443**, maintaining 136 historical slot positions for existing records. The new learner reaccumulates match results from the PFSP prior knowledge; statistical evidence for s82001 is retained in the original ledger; neither the BC nor s82001's ledger is modified.
Reuses s82001's previously authenticated native cross-version compatibility evidence, without re-generation or skipping authentication.
See [Member Selection](../outputs/analysis/watch3-bc-to-ppo-20260924/opponent-selection.json) and
[Pool Verification](../outputs/analysis/watch3-bc-to-ppo-20260924/pool-verification.json).

## PPO Protocol

| Project | Setting |
| --- | --- |
| Network | Actor 16 × 384, 384 turn memory, agronomy v4, q100 |
| Device | GPU0 + GPU1, BF16 computation, FP32 parameters and Adam |
| Reward | Terminal WDL + bounded cash difference, β=1, scale 10000 |
| Game Allocation | 64 self-play games + 64 unified PFSP games per round |
| Learning Rate | Actor 7.5e-6, Critic 1e-4 |
| Optimization | 1 epoch, 28 trajectories per card, KL 0.05, γ=λ=1 |
| Budget | 100,000 updates |
| Saving | Fully save every 4 updates; add own history every 64 updates |

Except for the new starting point, seeds, opponent source/capacity, and user-specified cash differential reward, the protocol is consistent with s82001.
BC data is used for starting point training, and new RL does not mix in BC rehearsal.
See [Configuration Analysis](../outputs/analysis/watch3-bc-to-ppo-20260924/resolved-training-config.json) and
[Configuration Differences](../outputs/analysis/watch3-bc-to-ppo-20260924/protocol-differences.json).
The 5 targeted tests for cash differential and base rewards have passed, see
[Test Records](../outputs/analysis/watch3-bc-to-ppo-20260924/reward-tests.log).

## Official Operation Verification

**09:01:47 UTC** Full verification of **U4 / 512 games** checkpoint, SHA256
`9c5e0bc11b4290cc762d4766f360f3507d023561517cdfa4840b00df3de7694a`.
Actor/Critic Adam optimizers each took 16 steps, dual rank RNG fully validated, all checkpoint tensors finite,
335 Actor tensors updated. First four rounds consisted of 64 self-play + 64 PFSP games;
Independent replay sampling and win/loss statistics are consistent, full pool and parent run ledger remain unchanged.

The terminal liquidation rewards for each card per turn are independently verified using separate reference formulas,
`cash_margin={beta: 1.0, cash_scale: 10000.0}`, **maximum error of 0**.
See [formal verification](../outputs/analysis/watch3-bc-to-ppo-20260924/formal-verification.json).
1,895 source code archive files and native binary hashes have passed, see
[source code recovery verification](../outputs/analysis/watch3-bc-to-ppo-20260924/source-verification.json).

## Recovery

After normal termination, the same run can be continued via the archive entry:

```bash
CUDA_VISIBLE_DEVICES=0,1 TMPDIR="$PWD/tmp" PYTHONPATH=src \
  .venv/bin/python -m kagg_revue.learning.recovery.cli \
  recovery.run=outputs/learning/agronomy-v4-m384-watch3-margin-ppo50-20260924-s84001
```
