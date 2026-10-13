# DSM Game BC Transition to 50% Self-Play PPO

Stop s81001 BC as per user request, to halt the latest Actor from launching new PPO at the time of stop; fully reuse the historical pool from the previous round. Retain s80001's historical pool and add s80001 itself to the historical opponent pool, increasing self-play to 50%.

**Current Status:** The user subsequently requested to resume this run, and a full-state continuation was initiated from U113 on **2026-09-24 09:10:46 UTC**, maintaining the original pure WDL and 50% self-play, with automatic baseline evaluation removed.
See [Resumption Instructions](s82001_resume_no_evaluation_20260924.md).

**Previous switch:** This RL was previously stopped normally as per user request on **2026-09-24 08:30:09 UTC** at
**U113 / 14,464 games**, with the latest Actor used for startup
[s83001 third-party BC](agronomy_watch3_bc_20260924.md). The complete runtime status and historical pool are retained.

## BC Endpoint and Weights

`agronomy-v4-m384-u3207-dsm-games-bc100-20260924-s81001` stopped normally at
**Batch 737 / 7 full epochs + 65 batches / 4,239,224 supervised turns**.
Latest checkpoint `pretraining/shard-000737.pt`, SHA256:
`ac992f9563930a2ba75355e78ba0035b990b17d3f4c43bd0ac22a19cb63fa882`.
BC Adam step 737, dual rank RNG, data cursor, and historical artifacts fully preserved.
The validation group NLL of the last complete epoch 7 is **0.1832565071**; latest weights were used.
See [BC Stop Verification](../outputs/analysis/dsm-games-bc-to-ppo-20260924/bc-stop-verification.json).

## Complete History Pool

Source stops at U3207: `agronomy-v4-m384-dsm-grouped-ppo-20260923-s80001`

- Incorporate all **252 external historical strategies**, preserving source, member identity, and hash.
- Add **52 strategies** from s80001 itself: starting point, U64 to U3200 comprising 50 regular snapshots, and final U3207.
- Retain **7 native C++ scripts**, unified with all historical strategies under PFSP, with no independent script quotas.
- Together with the new initial Actor, a total of **312 initial candidates** are formed (305 strategies + 7 scripts).

Capacity of **440**, of which 304 external strategies are fixedly retained, and 136 slots are allocated for new runs of its own historical records.
The new learner reaccumulates PFSP match statistics, while the evidence of the original learner is preserved in the original ledger.
See [Selection of Members](../outputs/analysis/dsm-games-bc-to-ppo-20260924/opponent-selection.json).

Upon initial import, it was discovered that the original path for the cross-version native engine compatibility report had been lost, and identity checks were not skipped.
Using the preserved legacy version alongside the current native binary, the 12 replay matches from the officially verified new DSM dataset were re-compared:
**17,280 observations**, legacy features, action labels, supervised masks, and full engine trajectory are all identical.
The new report is generated with an independent path and SHA256 binding, without rewriting the frozen ledger of s80001.
See [New Compatibility Verification](../outputs/analysis/dsm-games-bc-to-ppo-20260924/native-compatibility.json) and
[Evidence Replacement Record](../outputs/analysis/dsm-games-bc-to-ppo-20260924/native-evidence-replacement.json).

## PPO Protocol

Run: `agronomy-v4-m384-dsm-games-ppo50-20260924-s82001`.
Configuration: [learning_agronomy_dsm_games_ppo50_20260924.yaml](../configs/learning_agronomy_dsm_games_ppo50_20260924.yaml).

**2026-09-24 07:17:55 UTC** Start dual GPU, run ID `61a90ab34b384a91aa752cf4ee27cb9c`. The initial Actor's **347 tensor**s are completely consistent with BC's latest Batch 737; all 312 candidate samples in the actual sampling pool have been verified, and s80001's final U3207 has been included.
1,889 source files, along with native and script binaries, are fully recoverable.
See [Initialization Verification](../outputs/analysis/dsm-games-bc-to-ppo-20260924/initialization-verification.json),
[Complete Pool Verification](../outputs/analysis/dsm-games-bc-to-ppo-20260924/pool-verification.json),
[Source Code Verification](../outputs/analysis/dsm-games-bc-to-ppo-20260924/source-recovery-verification.json), and
[Startup Log](../outputs/analysis/dsm-games-bc-to-ppo-20260924/launch.json).

| Project | Configuration |
| --- | --- |
| Actor | 16 × 384, 384 turn memory, v4 features, q100 |
| Device | GPU0 + GPU1, BF16 computation, FP32 parameters and Adam |
| Reward | Pure terminal WDL: win +1, draw 0, loss -1; γ=λ=1 |
| Each game | **64 self-play games + 64 unified PFSP games**, totaling 128 games |
| Learning rate | Actor 7.5e-6, Critic 1e-4 |
| Optimization | 1 epoch, 28 trajectories per card, KL 0.05 |
| Budget | 100,000 updates |
| Save / Self-snapshot | Fully save every 4 updates, add to pool every 64 updates |

Create new PPO Actor/Critic Adam and Critic; do not include BC rehearsal. Except for new weights, historical source, 50% ratio, capacity, and new run seed, the training protocol is identical to s80001.
See [Configuration Analysis](../outputs/analysis/dsm-games-bc-to-ppo-20260924/resolved-training-config.json) and
[Protocol Differences](../outputs/analysis/dsm-games-bc-to-ppo-20260924/protocol-differences.json).

11 historical pool/PFSP test cases passed, including using new hash to bind reports when old verification reports are missing, rejecting corrupted evidence, regression checks without altering the source ledger; code modifications for Ruff and mypy passed.

## Official Operation Verification

**07:25:46 UTC** Full verification completed for **U4 / 512 games** checkpoint, SHA256
`534e5cb0b659082b31285e55df5d2fb222fdc631594f02ccf9fdde621cb76d01`.
Actor/Critic Adam each advanced **16 steps**, with full double rank RNG, all model and optimizer tensors finite,
335 Actor tensors updated. In the first 4 rounds, each consisting of **64 self-play games + 64 PFSP matchups**;
sampling and win/loss statistics independently replayed consistently, checkpoint statistics match ledger.
BC and s80001's frozen ledger hashes remain unchanged, both two-GPU worker processes and supervision processes are running normally.
See [formal verification](../outputs/analysis/dsm-games-bc-to-ppo-20260924/formal-verification.json).

After normal shutdown, continue the same run using the source code archive entry:

```bash
CUDA_VISIBLE_DEVICES=0,1 TMPDIR="$PWD/tmp" PYTHONPATH=src \
  .venv/bin/python -m kagg_revue.learning.recovery.cli \
  recovery.run=outputs/learning/agronomy-v4-m384-dsm-games-ppo50-20260924-s82001
```
