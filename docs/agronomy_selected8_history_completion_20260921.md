# Current PPO Completion of s73001 Historical Pool Usage

Objective operation: `agronomy-v4-m384-selected8-ppo-20260921-s76001`.
User request to complete the historical members used by previous `agronomy-v4-m384-bc100-3d-20260917-s73001`.

The original startup configuration only imported the 41 BC/PPO weights of s73001 itself, without recursively including the five historical runs it had already imported. This time, from s73001's authentication freeze archive, the following **137 weights** are being supplemented:

| Original Run | Quantity |
| --- | ---: |
| `context-26m-3d-20260910-s65001` | 27 |
| `context-26m-20260908-s62001` | 5 |
| `budget-q100-3d-20260912-s67001` | 25 |
| `budget-q100-top10-2d-20260915-s69001` | 29 |
| `budget-q100-top10-2d-20260913-s68001` | 51 |

Each weight retains its original run ID, checkpoint identity, original ledger hash, and independent storage hash.
The original ledger of s68001 has changed, so the frozen copy authenticated and saved at s73001 is used.
Old selections are not reinterpreted. Verification has passed for all members' byte hashes, sources, observation/action interfaces, and parameter constraints.
The existing 12,960 observation-compatible evidence from v2/v4 native environments and the implemented previous observation projections are retained.

External historical members increased from **41 to 178**. The historical pool capacity expanded from **177 to 314**, maintaining the original budget of **136 snapshots of the current run**; initial Actor and U64/U128/U192/U256 snapshots are retained.
At switch time, there are a total of **183 neural strategies + 7 native scripts = 190 unified candidates**.
Checkpoints retired during this run will not be re-entered into the pool due to capacity expansion, and ordinary recovery points will not be promoted to periodic snapshots.

**70% unified PFSP, 30% self-gambling**, script with no separate quota.
The current learner retains all accumulated PFSP evidence item by item; new members start from a neutral prior,
without copying the win/loss statistics from another learner. Pure terminal WDL, model, Actor/Critic Adam, dual rank RNG,
learning rate, 128 games per turn, GPU0+GPU1, and save/snapshot intervals are all retained.

Training completed successfully on **U259 / 33,152 games**, fully saved and exited normally with exit code 0.
Boundary checkpoint SHA256: `005a8f1ab14d03814e0f3e1562cc614d8282ff91d375e113643a4eb74630c4e8`.
Old checkpoint complete copy, old ledger, and old source code are retained; pool revision takes effect from **U260**.

Revise configuration: [learning_agronomy_selected8_history_20260921.yaml](../configs/learning_agronomy_selected8_history_20260921.yaml).
Add archive import and validation entrypoints, and reuse the existing policy root authentication to enable pool revisions to support PPO initialization from checkpoints.
The source code differs from the startup archive in only these five implementation/configuration files; the native environment and script runtime library remain unchanged.
Source code identity: `7ff96eed79e872adbe8ab29ee75a89b9b530aea97b66e837b010e71795eec820`.

Offline validation covers all 137 historical Actors, complete boundary checkpoints, and the next round of sampling.
18 related tests passed, and mypy checks for the full 908 source code files (Ruff and full coverage).
The old script directory test is missing the manifest for the newly added V53/Thomas; there is already one `KeyError: ahmed_v53`;
This is unrelated to the current completion, and the expired directory test is not counted toward the pass rate.
No claim is made that independent GPU updates were performed during the offline phase; formal checks after recovery will be recorded separately.

Evidence Directory: [Verify and Complete](../outputs/analysis/agronomy-selected8-history-completion-20260921/).
Includes [Pre-inspection of All Members](../outputs/analysis/agronomy-selected8-history-completion-20260921/preflight.json),
[Stop Saving](../outputs/analysis/agronomy-selected8-history-completion-20260921/stopped.json),
[Checkpoint Eligibility Certification](../outputs/analysis/agronomy-selected8-history-completion-20260921/qualification.json).

## Official Training Continuation Verification

Revision `population-revisions/0001` has been released, and after restoring entry validation, archiving source code, and runtime library, the system has been started with GPU0+GPU1. The first complete checkpoint **U260 / 33,280 games** has passed verification:

- Actually drew a newly inserted `budget-q100-3d-20260912-s67001` U512, completing **88 games** of historical matches
  (learning side: 84 wins, 4 losses), with an additional 40 self-play games; this is training sampling record.
- Sampling, probability, pool membership, and win/loss statistics from U259's original evidence replay U260 match exactly align with the ledger and checkpoints.
- Actor/Critic Adam each takes **3 steps**, both parameters are updated, all checkpoint tensors are finite, and dual rank RNG is intact.
- Original parent checkpoint SHA256 chain is correct; pure terminal WDL, cash/BC rewards are zero, and learning rate remains unchanged.
- s73001 original ledger hash remains unchanged; training continues as scheduled.

The first turn includes computation graph preparation, whose duration is not considered as a benchmark for stable throughput; no additional independent GPU qualification training is performed.
The monitoring interface shows the system running with 190 candidate entries.
See [State Persistence Verification](../outputs/analysis/agronomy-selected8-history-completion-20260921/transition-verification.json),
[Startup Log](../outputs/analysis/agronomy-selected8-history-completion-20260921/launch.json),
and [Full Formal Verification](../outputs/analysis/agronomy-selected8-history-completion-20260921/formal-verification.json).
