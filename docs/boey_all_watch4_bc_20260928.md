# U1729 → Boey Full Volume and Recent Game Replays for Four Players BC

**Next state:** As requested by the user, normally stopped at
Round **2,047 / 11,748,182 supervision turns** on **2026-09-28 01:17:46 UTC**, with the latest weights used for
[New Cash Difference RL with full historical pool inheritance](boey_watch4_bc_to_rl_20260928.md).
The original startup log is retained below.

According to user requirements, use Boey's submission of all collected replays for **56521745**, combined with the collected games from the other four continuously tracked players, starting from Beijing Time **2026-09-27 08:00** (UTC **2026-09-27 00:00**) onward, to establish an independent BC dataset. Then, initiate BC using the latest RL weights currently available.

## Data Scope and Acceptance

**2026-09-28 00:38:07 UTC** Freeze input from five collectors; time filtering field is official.
`episode.createTime`, inclusive of boundaries. Boey uses only submission **56521745**, exempt from recent time window restrictions. The remaining teachers are DSM, M & M & P & Q, DECEM, Vadim Vasilenko.
Retain all win/loss records and ratings, deduplicate by episode ID; when both sides meet the criteria in the same game, retain two separate trajectories.
Continue excluding submissions `56414341`, `56484772`; supervise only the teacher seats selected by the corresponding collectors.

Frozen downloaded data consists of **1,652 games / 1,923 trajectories**. DSM also had 6 games with only metadata discovered and not downloaded, thus excluded from this freeze; specific IDs are listed in
[Selection List](../outputs/analysis/boey-all-watch4-bc-20260928/selection.json).
Each collector's original list, downloaded subset, final selection, and hash are retained in the data directory under `source-manifests/`. Ongoing collectors continue to operate, and no new replays are dynamically added to this BC.

DECEM game **114128546** has an opponent appearing from frame 601 onwards with 118 instances of `TIMEOUT`
Decision frame; the complete ACTIVE trajectory encoding rules exclude this game, original replay is retained.
Final training input is **1,651 games / 1,922 trajectories**:

| Teacher | Trajectory |
| --- | ---: |
| Boey 56521745 | 388 |
| DSM | 395 |
| M & M & P & Q | 389 |
| DECEM | 388 |
| Vadim Vasilenko | 362 |

Training set: **1,568 games / 1,828 trajectories / 1,314,301 effective supervised turns**;
Validation set: **83 games / 94 trajectories / 67,578 effective supervised turns**.
Retain full 719-turn context for each trajectory; only mask loss for 39 unsupervised turns.
Partition seed is **62001**, and environment seed does not cross between training and validation partitions.

[Data Entry Point](../outputs/datasets/derived-v5b-boey-all-watch4-since-20260927-train-val-q100/manifest.json)
SHA256: `40dcf1fb07f120d682639b1438d9e125b8b1ed719864bb0ed51a1edc84c8702f`.
**4,953 array hashes** all passed; independent spot checks covered teachers, submission versions, dates, and partitions.
Official observations of **44,640 entries** from 31 games and **27,322 lines of code** are all consistent.
See [Range Verification](../outputs/analysis/boey-all-watch4-bc-20260928/scope-verification.json),
[Data Acceptance](../outputs/analysis/boey-all-watch4-bc-20260928/data-verification.json), and
[Hydra Data Configuration](../configs/sequences_boey_all_watch4_20260928.yaml).

## RL Stop and BC Start

Old run `derived-v5b-m384-watch6-ppo50-warmup300-20260927-s95001` stopped normally at **00:44:41 UTC** after **U1729 / 221,312 games**.
Latest complete checkpoint `checkpoints/update-001729.pt`, SHA256:
`30f27cc28685fbecfa45a525a33031e2cabca073cf3dce9cafbdc0ea46c5e5b4`.
Each Adam ran for 6,916 steps; all model and optimizer states are finite, with dual rank RNG, 418 historical strategies, and full PFSP state preserved; supervision process restored and exited normally. See
[Stop Verification](../outputs/analysis/boey-all-watch4-bc-20260928/stop-verification.json).

**00:47:22 UTC** Startup
`derived-v5b-m384-u1729-boey388-watch4-bc100-20260928-s96001`.
Complete v5b, 27,915 input dimensions, 384 turn memory, directly inheriting U1729 Actor,
create BC Adam and random state. Carry over the most recent BC recipe:

- Two-GPU BF16, FP32 parameters, LR **1e-5**, grouped average and equally weighted loss across five action types.
- Global batch size of 8 trajectories, 4 per GPU; 48 turns gradient blocks.
- Maximum of **100 epoch**, full validation per round; early stopping if no validation loss improvement of at least **0.001** is observed for **6 consecutive rounds**.
- Weights saved every **4 epoch**, additionally preserving the validation best and recent full recovery points; recovery state saved every 16 batches.
- `pretraining_only: true`, stop after BC completes normally, retain best validation weights.

Configuration: [learning_boey_all_watch4_bc_20260928.yaml](../configs/learning_boey_all_watch4_bc_20260928.yaml).
See [startup log](../outputs/analysis/boey-all-watch4-bc-20260928/launch.json),
[initialization verification](../outputs/analysis/boey-all-watch4-bc-20260928/initialization-verification.json) and
[real-time progress](../outputs/learning/derived-v5b-m384-u1729-boey388-watch4-bc100-20260928-s96001/learning-progress.json).
This run reuses existing implementation; data and BC module Ruff passed; 59 source files passed mypy check.

**00:49:57 UTC** Verified the complete checkpoint of the **64th / 365,244th supervision turn**:
BC Adam consists of 64 steps, LR 1e-5; 339 Actor tensor updates completed; model and optimizer are finite,
dual rank RNG fully validated. The initialized 351 Actor tensors match U1729 bit-by-bit;
1,979 archived source code/configuration identities verified; the old RL ledger remains unchanged.
Verification reached the 72nd batch of the 1st epoch (229 training batches per epoch); dual-GPU operation continues.
See [formal operation verification](../outputs/analysis/boey-all-watch4-bc-20260928/running-verification.json).
