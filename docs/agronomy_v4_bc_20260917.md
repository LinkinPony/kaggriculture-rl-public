# v4 three-day complete-trajectory BC: September 17, 2026

After the user requests submission of v4, initiate 100 epoch BC using data from the last three complete dates, and monitor conversion and training efficiency.
Feature submission is `32ef8e5`; the current conversion and full budget configuration submission is `e0efd23`.
`agronomy: true` uses `grounded-production-context-v4`, with each observation having 22,003 features.

## Data and Conversion

03:52 UTC regained the official daily index; the latest complete date remains 9/14, 9/15, 9/16, with 654, 652, and 639 games respectively, totaling 1,945 games. The new index and source information are located at `data/external/kaggriculture-agronomy-v4-20260917/raw/daily/`, with compressed replay reusing the original path.
The previous complete encoded array no longer exists, so the data is directly reconstructed from the original replay without relying on the v3 array or checkpoints.
The teacher selection continues to use the historically verifiable top ten list; this is not a re-fetch of today's leaderboard.

48 processes perform native batch encoding, with each process limiting the number of math library threads and disabling NumPy hugepage suggestions.
A total of 1,767 selected game replays are encoded, taking **118.62 seconds / 14.90 games per second**, generating
**86,695,292,754 bytes** of arrays. Full observations are used as temporal memory context, and invalid actions are only masked in the supervision loss.

| Partition | Game | Trajectory | Supervision Turn |
| --- | ---: | ---: | ---: |
| Training | 1,606 | 2,456 | 1,764,824 |
| Validation | 81 | 129 | 92,695 |
| Confirmation | 80 | 121 | 86,951 |

Coverage volume is consistent with the three-day data from the previous version. By environment seed isolation partitioning, 1,767 source seeds have no overlap with the new run retention intervals; additionally, there is no overlap with the retention intervals of 92 historical protocols.
manifest SHA256: `d2b8d381b4cb33cde404e438f17ad922baa5e1367ff8df6cfbe1876c2179f812`.
See [Conversion Record](../outputs/analysis/agronomy-v4-20260917/conversion.json) and
[Seed Verification](../outputs/analysis/agronomy-v4-20260917/seeds.json).

## Training Configuration

New directory: `outputs/learning/agronomy-v4-m384-bc100-3d-20260917-s73001`.
Fully random initialization, Actor maintains a standard residual block of **16 × 384**, totaling **24,944,666** parameters,
time memory retains **2 × 256 / 384 turns**. Dual H200, BF16, compilation enabled, reusing
`tmp/torchinductor` compilation cache; reading employs existing mmap and reuses pinned host buffers.

Global: 8 complete trajectories per batch, 4 per GPU, segmented into 48 turns; Adam updated after processing complete trajectories, learning rate 1e-4. 307 steps per epoch, totaling 30,700 steps and 176,482,400 supervised turns over 100 epochs. This run explicitly sets `early_stopping: null`, with no inheritance of the previous configuration's patience of 10. `pretraining_only: true`: BC completed, save and stop. Cash is used only for observation and diagnosis. Each round continues to record validation NLL, 4 self-play games for operational diagnosis, and 16 games each against two fixed random models.

The original s72001 had normally stopped at BC cursor 2101 prior to this task, with old weights and historical products retained; see [Confirmation of Previous Operation Stop](../outputs/analysis/agronomy-20260917/old-stop-verification.json).

## Operation Entry

```bash
.venv/bin/python -m kagg_revue.datasets.sequences.prepare --config-name sequences_agronomy
.venv/bin/python -m kagg_revue.datasets.sequences.verification --config-name sequences_agronomy
.venv/bin/python -m kagg_revue.learning.cli --config-name learning_agronomy_bc_20260917
```

Use the source code archive entry for breakpoint resumption to avoid subsequent work tree modifications affecting execution:

```bash
.venv/bin/python -m kagg_revue.learning.recovery.cli \
  recovery.run=outputs/learning/agronomy-v4-m384-bc100-3d-20260917-s73001
```

Already passed Ruff, full-scale mypy (817 files), and 10 v4/sequence loading tests before official launch.

All **5,301 array hashes** passed; 9 complete official replays agree on **12,960 observations**.
Additional verification of 126 native engine v4 feature observations, 12,223 legacy observation fields match the pre-reconstruction interface;
Sampled action labels and supervision masks remain identical before and after v4 activation.
See [Data Verification](../outputs/analysis/agronomy-v4-20260917/data-verification.json).

Double-GPU small dataset acceptance completed for 2 rounds, two Adam updates, 11,504 supervision turns, final status complete, RL update set to 0. The model and Adam are limited; the entity encoder, temporal memory, and fusion parameters continue to be updated; all four v4 input projections have been updated. Checkpoint parent hash and dual-GPU RNG preservation have passed. Teacher-enforced BC has no random sampling; the two CUDA RNG states are identical, and they cannot be claimed to independently advance. Two rounds of operational diagnostics and random model panels have been generated. See [Double-GPU Acceptance](../outputs/analysis/agronomy-v4-20260917/qualification.json).

The acceptance testing revealed that the BF16 reduction settings declared in the old BC initialization were not applied, and the first evaluation only changed the settings on rank 0. A global switch caused additional compilation, leading to different configurations across two GPUs. `03db45f` applies the settings before compilation during BC optimizer construction; in formal runs, both GPUs start from the declared precision. The two acceptance rounds mentioned above occurred before this fix. After the fix, training is verified using formal checkpoints and throughput records.

Formally launched at **04:03 UTC**, PID **558566**, runtime ID `d4dc95a8bf204e2f997455a16576707d`, source code archive bound to `03db45f`.
Complete startup command and environment variables available at [Startup Log](../outputs/analysis/agronomy-v4-20260917/formal-launch.json),
real-time status available at [Progress](../outputs/learning/agronomy-v4-m384-bc100-3d-20260917-s73001/learning-progress.json).

**Formal Turn 48 has been verified**: 384 distinct trajectories, 275,976 supervised turns, data ordering and mask counting precisely matched, Adam step at 48, model and optimizer tensor limits applied; compared to Turn 16, entity encoder, temporal memory, and fusion parameters continue to be updated, 4 types of v4 feature input projections are updated, and both rank RNGs are preserved. Precision initialization fixes are included in the actual running source code archive, and the checkpoint declares BF16 reduction set to false. Ruff/mypy and four existing BC training tests pass for the fixed file.

Official cursor **38–61, total 24 batches** has median latency **1.420 seconds per batch**, loading median **0.054 seconds per batch**, maximum **0.105 seconds**, throughput **4,071 supervised turns per second**.
Rank 0 peak GPU memory allocation is approximately 11.44 GB. This metric includes loading and dual-GPU gradient synchronization, excludes initial startup, checkpoint writing, and end-of-turn evaluation; GPUs are concurrently running other project tasks. See [Official Checkpoint and Throughput Verification](../outputs/analysis/agronomy-v4-20260917/formal-verification.json).
