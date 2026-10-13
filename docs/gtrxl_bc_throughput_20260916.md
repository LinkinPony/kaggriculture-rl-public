# BC host-loading repair, 2026-09-16

The user reported extremely low BC throughput and requested a fix. The formal
run remains `gtrxl-m384-bc100-3d-20260916-s71001` with the same random root,
100-epoch cap, patience 10, minimum meaningful selection-NLL decrease 0.001,
best-epoch selection and automatic pure-self-play WDL RL handoff.

## Cause and repair

The earlier five-epoch BC and the new BC used the identical loader source hash.
The slowdown was in CPU batch assembly: the final 20 batches before repair had
median loading time 43.63 seconds and median total time 47.94 seconds, while
learning still took about 4.07 seconds. Both GPUs waited for the host.

The loader copied 32 trajectories and then used `np.stack` to allocate another
612,749,056-byte observation array per rank and batch. Profiling placed 15.11 of
15.55 seconds inside three stack calls. A focused observation-only probe took
13.89 seconds in `np.stack`, versus 0.42 seconds copying identical values into a
Torch-owned allocation. With `NUMPY_MADVISE_HUGEPAGE=0` set only in a separate
probe process, the same NumPy stack took 0.86 seconds. The machine's transparent
huge-page policy uses `madvise`, and memory pressure was present. The evidence
identifies the NumPy huge-page allocation path as the trigger; disk reads and
model computation were not the measured bottleneck.

`datasets/sequences/loading.py` now retains read-only mapped observation views
and copies directly into reusable pinned Torch host buffers. It avoids both
large temporary trajectory copies and newly allocated NumPy stack outputs.
Blocking host-to-device transfers make buffer reuse safe. CPU-returned batches
retain independent ownership. No global kernel setting or unrelated process
environment was changed.

## Verification

Full-size training, partial training and partial validation batches were compared
on both rank slices. Observations, actions, masks, dtypes and layouts match the
legacy packing exactly; missing and padded supervision remains masked.
The existing regression now also checks equality against legacy packing and
retention of independent CPU outputs. Ruff, full mypy (810 files), and eight
targeted tests pass.

The first isolated implementation removed the stack output but still showed
occasional stalls from intermediate NumPy trajectory copies. Its artifacts are
retained in `gtrxl-bc-loader-qualification-20260916`. The final implementation
removes those copies too. Final qualification resumed the formal cursor-144
checkpoint in `gtrxl-bc-loader-qualification-20260916-v2`, using the original
protocol except for the output directory. It ran nine real dual-GPU BC steps
and stopped normally at cursor 153, preserving the existing epoch records and
patience state. No huge-page environment override was used for these runs.

Excluding the first compilation/warmup batch, eight batches measured:

| Median timing | Before repair | Final qualification |
| --- | ---: | ---: |
| Host loading | 43.630 s | 0.310 s |
| Learning | 4.069 s | 3.802 s |
| Whole batch | 47.937 s | 4.110 s |

The measured whole-batch speedup is 11.66x. This is an execution measurement.
All model/Adam tensors are finite, every Adam state reached step 153, and actor
encoder/temporal/fusion weights updated. Both worker CPU/CUDA RNG states were
preserved (this BC step has no stochastic Torch operation). No bitwise weight
replay claim is made for the nondeterministic BF16 optimizer.

See [qualification](../outputs/analysis/gtrxl-bc-throughput-20260916/qualification.json),
[input equivalence](../outputs/analysis/gtrxl-bc-throughput-20260916/final-loader-equivalence.json),
[original profile](../outputs/analysis/gtrxl-bc-throughput-20260916/loader-before.json),
and [huge-page probe](../outputs/analysis/gtrxl-bc-throughput-20260916/hugepage-probe.json).

## Formal continuation

Formal BC stopped normally at cursor **144**, after 6,490,121 supervised turns.
Checkpoint SHA256:
`5cd7c7fb07dd27656b4e52c2fef5507247a9ebe7268cb51351b1545e877a6c4e`.
The existing source-repair mechanism was extended to accept unfinished BC and
require qualification bound to its exact pretraining progress. Revision
`source-revisions/0001` preserves the previous source archive and ledger, every
registered checkpoint, model, Adam, RNG, data cursor, early-stopping state and
all protocol fields. The new source hash is
`ba963af53c1840ecbce59d885880b9af21304380ab1073d379aaa1297d90f6b0`.

The formal run has been restarted through its authenticated archive at cursor
144. See [restart record](../outputs/analysis/gtrxl-bc-throughput-20260916/formal-restart.json)
and the run's `recovery-status.json` for the active process and log.

The formal cursor-160 checkpoint has now passed verification: all model/Adam
tensors are finite, optimizer steps equal 160, encoder/temporal/fusion parameters
continue updating, both rank RNG states are preserved, and the original
cursor-144 checkpoint and protocol are unchanged. Training remains active.
Across 25 formal batches after the first warmup batch, median total time is
**4.199 seconds**, median load time **0.241 seconds**, and maximum load time
**0.275 seconds**. The actual formal median speedup is **11.42x**. See
[formal verification](../outputs/analysis/gtrxl-bc-throughput-20260916/formal-verification.json).
