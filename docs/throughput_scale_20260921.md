# Full PPO Throughput and H200 Utilization of the 2.89M Model

## Confirmed Constraints

Latest restriction: **No modifications to model architecture or features; only constant and performance optimizations allowed**.
User has accepted current optimizations, experiment concluded, final fixed value of **56.82 seconds per 1024 games**; single-card 30-second target not achieved.
Map/unit summary candidates have only been coded, not run in experiments;
all experiments have now been fully revoked; all 286 scene tokens are retained.
User confirms that training hardware consists solely of H200, allowing specialized optimization for Hopper kernel, compilation, and execution configurations.

- Actor + Critic total 2–3M; user selects a wide, shallow, memory-free model with 2,887,708 parameters.
- Actor: 256-wide / 3 layers / 4 heads, 2,507,162 parameters; Critic: 128-wide / 1 layer, 380,546 parameters.
- Retain shared historical features from observations and remove learned memory.
- Precision is selected based on throughput; current mixed computation in BF16, with parameters and Adam states maintained in FP32.
  The user previously proposed FP32 temporarily, but later explicitly withdrew this request.
- Approximately 80% self-play + 20% independent frozen models of the same architecture; no need to include old large-model opponents in the hot path.
- **All decisions collected over a full turn participate in PPO, without sampling or setting a decision count limit.**
  The 131,072-row sampling scheme has been canceled and the corresponding experiment has not been initiated.
- Sample size per update can be increased. Currently, after accumulating all micro-batches per turn, Actor and Critic each update once.
- During the experiment, GPU0 continues with the original formal training, while GPU1 runs the independent experiment; after completion, the original training is stopped on U7820, and both GPUs have been transferred to [compact289 BC100](compact_bc_selected8_20260921.md).
- Simultaneously monitor power consumption, device activity rate, and throughput for warm-start sampling and learning, without including cold compilation in steady-state performance.

## Formal training has been migrated to GPU0

Formal S73001 runs successfully and exits normally on U7703 / 985,984 games, and proceeds from U7704 onward.
`runtime-revisions/0003` uses only GPU0; the original model, optimizer, reward, and unified PFSP evidence are carried forward.
After the first round recovery, both Actor/Critic Adam steps increase from 23721 to 23727, and the model boundedness check passes.
The formal run continues using its archived source code; this experiment does not alter its model configuration or reward.
The new experiment uses pure terminal WDL; the previous formal run retains the authorized WDL with bounded cash difference reward.

## Performance Benchmarks and Comparison Criteria

| Benchmark | Physical Game Count | Warm-up Seconds per Turn | Games per Second |
| --- | ---: | ---: | ---: |
| Median of Original Dual-GPU Formal Training U7604–U7703 | 128 | 29.42 | 4.35 |
| GPU1: Original Large Model with Fixed Old Opponents | 128 | 53.46 | 2.39 |
| Selected 2.89M Model, Old Kernel Selection Rule | 512 | 95.45 | 5.36 |
| 2.89M Model, 64-Dimensional Attention Heads Using SDPA | 512 | 31.34 | 16.34 |
| Same Model, Full Inference Compilation, 4096-Token Microbatch | 1024 | 59.77 | 17.13 |
| Equivalent Elimination of Fixed Action Padding, 4096-Token Microbatch | 1024 | 58.93 | 17.38 |
| Same Implementation, 6144-Token Microbatch | 1024 | 57.92 | 17.68 |
| Final Choice: 6144-Token + Large Training Batch 64×64 Attention Tiling | 1024 | **56.82** | **18.02** |
| Independent CUDA Streams for Concurrent Sampling, Not Adopted | 1024 | 63.55 | 16.11 |

10–20x relative to the original dual-GPU setup, the target is **43.5–87.0 games/second**; relative to the original single-GPU model, the target is 23.9–47.9 games/second. These two denominators must not be mixed.
Each model experiment includes a full 719 turns of sampling and real PPO updates, with all collected samples participating in learning.
The first round includes compilation, graph capture, and cache allocation; only the subsequent two rounds are used for warm-start comparison.
The baseline does not include evaluation, checkpoint saving, or switching among multiple frozen opponents.

## Kernel Bottlenecks Identified and Fixed

The old rule uniformly adopts Flex Attention when batch ≥ 80. It selects an inefficient kernel on the 64-dimensional attention head of the chosen Actor. Retain the original 32/40/48 head path; the 64-dimensional head switches to PyTorch's native SDPA, with the attention equation and key mask remaining unchanged, and parameter count unchanged.

| Attention single-layer test, 4 devices, 286 tokens | Old Flex | Native SDPA |
| --- | ---: | ---: |
| 460 rows, 64-dimensional heads, forward only | 7.58 ms | 0.324 ms |
| 8192 rows, 64-dimensional heads, forward and Q/K/V backward | 141.15 ms | 19.09 ms |
| 8192 rows, 32-dimensional heads, forward and backward | 11.46 ms | 18.13 ms |

This is also the reason for retaining the Critic's 32-dimensional head Flex path. Both output and Q/K/V gradients are verified for finite behavior, and the BF16 relative L2 error passes the existing 0.015 threshold. Full training results will be measured separately, and it cannot be assumed that multiple kernel speedups translate to end-to-end acceleration.

## H200 Measurement and Subsequent Configuration

Each new experiment records every 0.5 seconds the GPU1 device utilization, memory utilization, power consumption, SM clock rate, and memory occupancy, and marks the prepare/collect/learn phases. The first second after phase transitions is excluded from the summary.
`nvidia-smi utilization.gpu` **does not equal SM achieved occupancy**, and memory activity rate also does not equal peak bandwidth utilization. CUDA profiler is used for confirmation of primary kernels and their execution times; one cannot simply claim that the H200 is fully utilized based on 100% GPU activity.

512-game sampling with the old kernel takes approximately 44 seconds, and the power consumption remains around 325W even when GPU utilization reaches 100%.

After switching to native SDPA, sampling takes about 10.12 seconds and learning takes about 21.21 seconds.

For 512-game warm-up sampling/learning, the average power consumption is **442W / 631W**; for 1024-game full compilation, it is **536W / 622W**. The device utilization is 100% in both phases. The hardware power limit is 700W.

The learning time for 1024 games is approximately 43.75 seconds, which is the main bottleneck in the entire turn.

Nvprof Compute actual return is `ERR_NVGPUCTRPERM`. Driver is `RmProfilingAdminOnly=1`, container has no `CAP_SYS_ADMIN`. Therefore, true SM hardware counters are not obtained, and 100% SM utilization is not claimed; no modifications to driver permissions or power limits were made.

Running independent CUDA streams to replay two groups of Actors simultaneously actually reduces throughput: sampling time increases from approximately 16.01 seconds to 19.75 seconds, power consumption is about 461W, and device utilization is around 75%. The full PPO steady-state measurement has been completed; additional full trajectory equivalence comparisons could not be performed due to GPU memory exhaustion caused by temporary tensor comparisons, and thus equivalence was not achieved. The experiment implementation has been revoked, and the final code retains the original ordered GPU startup and CPU environment pipeline.

1024 games still collect all 719 turns, approximately 1,320,000 training lines entering PPO.
Micro-batches are constrained by both observation cache and activation GPU memory, requiring empirical measurement; increasing the number of physical games alone does not guarantee an increase in games per second, and relying on fewer PPO lines cannot improve reported numbers.

## Equivalent Compression of Fixed Action Filling

In the 276-column action ABI of Typed Actor, each unit has only three valid choices: target, operation, and quantity; all other fixed fields and future task slots remain zero. PPO computes log-softmax, entropy, and ratio only for the 116 semantically valid columns; all unit and market selections are preserved, **without reducing the number of decision rows**. Prefix Critic omits the hidden layer computations for zero-weight padding, then restores the full 276-column output, retaining the original loss divisor and exclusive prefix definition. Inference, native action ABI, and parameter count remain unchanged.

Independent verification covers non-zero learned prefix reads, entropy terms, unequal sample weights, and all parameter gradients;
Matches the fully padded reference implementation. Real BF16 complete PPO achieves an average of **58.93 seconds per 1024 games** over two warm-up rounds, with learning taking approximately **42.73 seconds**, involving all **1,325,836** lines; KL divergence, value loss, and terminal liquidation cash measurements are consistent with those before compression. Peak allocated GPU memory is approximately **93.31 GiB**; average power consumption during warm-up sampling and learning is about **530W / 621W**. Compared to the original two-GPU throughput per second, it is approximately **3.99 times faster**; compared to the original single-GPU model, it is approximately **7.26 times faster**. It has not yet reached 30 seconds per 1024 games.

## H200 Dedicated Constants and Kernel Testing

Increase the computation micro-batch size from 4096 to 6144, without altering the logical batch size, optimization steps, sample coverage, or model.
Two warm-up turns take **57.944 / 57.895 seconds**, averaging **57.919 seconds per 1024 games**; learning takes an average of **41.901 seconds**. Peak allocated GPU memory is approximately **110.91 GiB**, with sampling and learning power consumption around **536W / 632W**, respectively. All 1,325,836 lines remain active, with each optimizer updating once and no early stopping.
The micro-batch change alters GEMM shapes and floating-point reduction order; no bit-level consistency is claimed.

Forward and backward testing of H200's 4096 rows, 286 token, 64-dimensional heads:

| Kernel Configuration | Milliseconds |
| --- | ---: |
| Native SDPA | 9.610 |
| Triton, 64×64 tiling | 9.027 |
| Same tiling, enable TMA | 13.095 |
| 128×64 tiling | 9.350 |
| 64×128 tiling | 26.538 |
| 64×64, adjusted backward tiling | 10.922 |
| 64×64, fixed 4 warps | 18.765 |

All candidate outputs have finite Q/K/V gradients, and relative L2 error is below a 0.015 threshold.
The largest error among the fastest candidates is approximately 0.00147. TMA and manually fixed warp counts are actually slower on this shape and are not adopted.
64×64 tiling has been adopted: used only for CUDA training compilation, batch ≥ 4096, 286 tokens, 64-dimensional heads.
Native SDPA is retained for 64-dimensional head inference.

Final complete PPO warm-up turns respectively **56.650 / 56.990 seconds**, averaging **56.8197 seconds per 1024 games**.
Training took approximately **40.8–40.95 seconds**, with peak allocated GPU memory reaching about **110.90 GiB**.
A total of **1,325,836 lines** participated; Actor/Critic each updated once, without early stopping, KL is
`1.3935174e-6`, value loss is `1.005905032`. Relative to the original dual-GPU throughput, this is about **4.14 times**, and relative to the original large model single-GPU setup, it is about **7.53 times**. This final configuration has been solidified into the compact289 setup and source code.

Additionally, real-world testing of 1,171,456 rows × 256→768, 256→512, 512→256 GEMM operations
with original configuration, ATen/Triton automatic search, and persistent TMA search, including forward passes and gradients for all linear layers.
The search selects existing cuBLAS implementations; packaging timing shows minor variations but no new winning kernels,
and this is not considered a verified training speedup, nor does it increase default compilation overhead.

## Experimental Limitations and What Is Needed to Achieve 10–20 Times

The new model and frozen opponents of the same specification are randomly initialized. This report measures computational and execution costs and does not represent the win rate of the trained model, nor does it guarantee that more active, mature strategies will produce the same native environment execution time.
Original large model weights cannot be precisely restored for models of different sizes; formal small model training should be conducted on a new branch.

The adopted methods include shrinking the Actor/Critic, removing learned memory, increasing the proportion of self-play, using historically matched opponents, large micro-batches, fused PPO targets, CUDA Graph sampling, and two native C++ pipeline setups.
CUDA Graph already exists and cannot be counted again as additional gain.

This experiment round has ended, and no further performance search will be conducted. It is prohibited to achieve the timing goal by compressing scene tokens, discarding features, reducing PPO samples, or introducing outdated policy samples.
Actual results have not met the target of 30 seconds per 1024 games or a relative improvement of 10–20 times compared to the original dual-card setup.

## Results and Reproduction

Experiment directory: `outputs/analysis/throughput-scale-20260921/`.

- [Formal GPU0 Recovery Check](../outputs/analysis/throughput-scale-20260921/production-verification.json)
- [Original Dual-GPU Baseline](../outputs/analysis/throughput-scale-20260921/production-dual-baseline.json)
- [Original Model Single-GPU Baseline](../outputs/analysis/throughput-scale-20260921/baseline.json)
- [2.89M Old Kernel Complete Baseline](../outputs/analysis/throughput-scale-20260921/compact289_peer512.json)
- [Attention Forward Comparison](../outputs/analysis/throughput-scale-20260921/compact-attention-inference.json)
- [Attention Backward Comparison](../outputs/analysis/throughput-scale-20260921/compact-attention-training.json)
- [Complete Measurement After Fixed Padding Omission](../outputs/analysis/throughput-scale-20260921/compact289_peer1024_semantic.json)
- [Complete Measurement with 6144-Row Microbatch](../outputs/analysis/throughput-scale-20260921/compact289_peer1024_micro6144.json)
- [Final H200 Blockwise Complete Measurement](../outputs/analysis/throughput-scale-20260921/compact289_peer1024_hopper_tiles.json)
- [H200 Attention Blockwise Comparison](../outputs/analysis/throughput-scale-20260921/compact-attention-hopper.json)
- [H200 GEMM Search](../outputs/analysis/throughput-scale-20260921/compact-matmul-hopper.json)
- [Solidified Model Hydra Configuration](../configs/model/compact289.yaml)
- [Fixed Training Preset](../configs/learning_compact_20260921.yaml)
- [Independent Experiment Configuration](../configs/learning_compact_throughput.yaml)
- [Complete Game and PPO Measurement](../src/kagg_revue/learning/performance/scaling.py)

Entry forcibly requires `CUDA_VISIBLE_DEVICES=1`. For example:

```bash
CUDA_VISIBLE_DEVICES=1 TMPDIR="$PWD/tmp" \
TORCHINDUCTOR_CACHE_DIR="$PWD/tmp/torchinductor" \
TRITON_CACHE_DIR="$PWD/tmp/triton" \
.venv/bin/python -m kagg_revue.learning.performance.scaling \
  --config-name=learning_compact_throughput \
  benchmark.output=outputs/analysis/throughput-scale-20260921/reproduction.json
```

The actual startup parameters, environments, and PID are separately stored in the corresponding `*-launch.json`.
