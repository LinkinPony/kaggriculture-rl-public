# Optimization of Dual H200 Training Execution

2026-09-08, online PPO optimization for `long-100k-20260908-s61001`.
Training originally terminated normally at update 93 (11,904 games). The complete model, Adam state, learning rate, RNG, historical pool, and original source code archive are preserved. Execution of the changes resumes from this original recovery point.

## Measurement

Similarly, in each turn of 128 complete games, the global logical minibatch consists of 5,760 rows with 24 actor/critic updates.
The table below shows measurements taken after compilation; the first compilation, periodic evaluation, and checkpoint writing occur separately.

| Execution Plan | Sampling Seconds/turn | Learning Seconds/turn | Total Seconds/turn |
| --- | ---: | ---: | ---: |
| Original single GPU, microbatch 256 | 4.46 | 11.14 | 15.7 |
| Single GPU, compiled inference, microbatch 1,440 | 2.37 | 4.93 | 7.31 |
| Single GPU, compiled inference, microbatch 5,760 | 2.37 | 4.45 | 6.82 |
| Dual GPUs, 2,880 rows per GPU, fused loss, 8 environment threads per GPU | 1.80 | 2.42 | 4.23 |

The stable baseline increased from approximately 8.2 games/second to approximately 30.3 games/second, a factor of about **3.7x**.
The original measurement is from [dual-h200](../outputs/analysis/dual-h200/), while the final scheme's [per-turn baseline](../outputs/analysis/dual-h200/dual-fused-workers8.json) includes per-GPU metrics and parameter consistency checks (maximum parameter difference between the two GPUs is 0). These are throughput measurement results and do not represent gains in strategy strength.

## Execution Method

- Two independent CUDA processes jointly train a strategy; each GPU performs 32 self-play games and 32 historical matches against opponents.
  The split preserves the game type and opponent seat distribution from the original environment seed, without double-counting trajectories from both sides.

- Gradients, advantage moments weighted by physical match counts, KL divergence, rollback decisions, and loss summaries are globally synchronized.
  The global logical batch size remains at 5,760; the microbatch is expanded from 256 to 5,760, with each GPU processing 2,880 rows.
  This eliminates excessive small-batch gradient accumulation while retaining full minibatch post-step KL protection.

- After compiling `policy.act`, the CUDA graph is captured; sampling and current parameter updates share the original policy distribution.
  The actor's probability, entropy, and prefix PPO loss, as well as the critic's target reduction, are fused together.

- CPU affinity is divided across the available 48 cores of the actual container: GPU 0 uses cores 144–167, GPU 1 uses cores 168–191.
  Each GPU enables 8 environment threads, 2 Torch CPU threads, and up to 8 compilation threads.
  Enabling 24 environment threads per GPU directly increases scheduling overhead for these short tasks, resulting in slower baseline performance and greater variance.

- The complete rollout runs persistently on the corresponding GPU, avoiding the need to transfer full trajectories between the two GPUs.
  The final design allocates approximately 18.6 GiB peak memory per GPU; the host RAM caches authenticated weights from the current history pool, avoiding per-round deserialization of the optimizer to the GPU.
  The long-budget ledger uses compact atomic JSON writes, reducing serialization overhead after growth.

Resources are allocated based on actual bottleneck measurements. This model and a fixed 128-game budget do not require filling every card's 141 GiB of GPU memory or every container's 1 TiB of RAM; further increasing environment threads cannot eliminate model computation and turn-to-turn causal waiting.

## Identity, Verification, and Recovery

Statistical control remains unchanged: random root, four-round demonstration endpoints, 100,000 PPO update iterations, 128 games per round,
model, reward, learning rate recipe, KL threshold, historical pool capacity/period, and evaluation panel remain unaltered.
Hardware switching alters the sampling random stream, minibatch sharding order, and floating-point reduction; **it is not claimed to be bit-equivalent to single-GPU operation**.
Rank 0 restores the original RNG; the initial RNG for new ranks is determined by the root seed, rank, and stop update number;
subsequently, each checkpoint fully saves the CPU/CUDA RNG for both ranks.

Execution configuration is managed by Hydra's `experiment.execution`, with the default mainline configuration already employing a dual-GPU setup.
Existing runs cannot be directly bypassed without passing source code and configuration identity checks. Dedicated entry point
`python -m kagg_revue.learning.recovery.upgrade` first verifies the original source code archive, hash values of all members, and native binaries, then confirms binding of the qualification report to the source code, recovery points, and execution configuration. It retains the original archive, writes an unobfuscatable record of changes to `runtime-revisions/`, and then proceeds with normal recovery under the requirement of precise identity.
`python -m kagg_revue.learning.recovery.cli` also supports recovery from the execution version archive of this run record.

Verification entry is `python -m kagg_revue.learning.performance.qualification`.
It creates a clearly marked independent copy from the original update 93, restarts the two-GPU setup after normal shutdown, and verifies each update number, complete optimizer, independent RNG, checkpoint parent hash chain, and source run integrity remains unaltered.
It simultaneously compares compiled sampling with eager teacher forcing, and validates CUDA graph updates through in-place weight modifications.
Qualification report available at [qualification.json](../outputs/analysis/dual-h200/qualification.json).

Component checks cover sharding, gradient fusion, identity recovery, periodic saving, KL rollback, native complete game, and monitoring read; Ruff, mypy pass. Independent performance-qualified artifacts are not considered as recovery models or deployment candidates for the mainline.
