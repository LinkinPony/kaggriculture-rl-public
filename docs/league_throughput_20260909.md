# Three-Expert League Throughput Optimization

This analysis targets `league3-20260909-s63001-fixed`, starting from the complete joint recovery point of Round 93.
Each round still consists of 192 games: 32 games of each of the three mutual battles and three self-play games; each model has 64 trajectory entries per GPU, with 16 optimization updates for both Actor and Critic. Network states, BC endpoints, optimizer states, learning rate schedules, rewards, sampling weights, logical batch sizes, micro-batches, and a total budget of 100k are all preserved.

## Measurement at the Same Recovery Point

| Metric | Original Implementation | Optimized |
| --- | ---: | ---: |
| Sampling | 10.29 seconds | 8.26 seconds |
| Three-model PPO update total | 30.16 seconds | 21.85 seconds |
| Full turn | 40.46 seconds | 30.00 / 30.23 seconds |
| Physical game throughput | 4.75 games/second | 6.38 games/second |

After preheating, the average time per turn is **30.12 seconds/turn**, achieving a **34.3% increase in throughput** and a **25.6% reduction in per-turn time**.
The compilation preheating, periodic evaluation, and checkpoint writing are not included in this steady-state baseline; the previous formal training over the last 10 turns averaged about 40.7 seconds, consistent with the independent benchmark. During optimization measurement, all 16 updates were completed by each of the three Actor/Critic components, and the maximum parameter differences across the six networks on two GPUs are 0, with no learning skips used to gain speed.

Restore point SHA256:
`9d53715cdbd8c7c6a448a777b0dc60e3b9412532750981bcd65a250b99b69c02`.
Turn-by-turn data see [Original Baseline](../outputs/analysis/league-throughput-20260909/baseline.json),
[Optimized Baseline](../outputs/analysis/league-throughput-20260909/flex-streams.json), and
[Comparison Summary](../outputs/analysis/league-throughput-20260909/performance.json).

The stable turn duration for independent continuous training replicas is **30.05 seconds**. In this turn, power telemetry sampled at 250 ms intervals shows that the average power consumption during the PPO phase for GPU0/GPU1 is **663.9 / 655.2 W**, with average GPU utilization of **92.8% / 93.6%**; the maximum power limit for both GPUs remains at 700 W. The overall average power consumption per turn is 605.2 / 595.1 W, which includes the sampling phase requiring waiting for environmental responses.
See [Per-sample Telemetry](../outputs/analysis/league-throughput-20260909/power.csv) and [Statistical Window](../outputs/analysis/league-throughput-20260909/power-summary.json).

## Bottlenecks and Modifications

The profiler shows that in a model update, key masking attention resides in the SM80 CUTLASS kernel, accounting for approximately **52.6%** of GPU compute time during both forward and backward passes; native environment progress consumes only about 0.17 seconds per round. [Original profiler](../outputs/analysis/league-throughput-20260909/baseline.rank1.profile.txt)
Includes operator and CPU submission overhead.

Large-batch CUDA compilation of CUDA attention now uses the Triton backend of PyTorch FlexAttention, applying the original per-sample key mask during score computation. Softmax, scaling, effective tokens, and model parameters remain as originally defined; no additional large attention matrices are constructed. 64-row sampling still uses the original SDPA; CPU and uncompiled calls continue to follow existing paths. The actual forward and backward pass for a single instance with 2,880 rows, 286 tokens, and head width 40/48 has been reduced from 11.7–11.9 ms to 5.4–5.5 ms.
See [Single-instance Measurement and Gradient Error](../outputs/analysis/league-throughput-20260909/attention.json).
Interface based on [PyTorch FlexAttention Documentation](https://docs.pytorch.org/docs/main/nn.attention.flex_attention.html); no additional FlashAttention package is installed, and no Torch/CUDA upgrade or replacement is performed.

During sampling, three strategies execute their respective graphs independently within separate CUDA streams, and uniformly wait for action execution and tape writing before proceeding to native environment. Each graph also captures its own pre-warm stream to avoid sharing cuBLAS workspace. PyTorch's default graph capture stream is reused across multiple graphs; only concurrent replay leads to limited but erroneous outputs. The initial trial indeed triggered an abnormal KL, and the Actor's protection logic skipped this candidate, which was deemed failed—its 14.9-second timing is invalid, and the weights did not enter formal runtime.
See [Failure Record](../outputs/analysis/league-throughput-20260909/rejected-candidate.json),
[PyTorch workspace implementation](https://github.com/pytorch/pytorch/blob/main/aten/src/ATen/cuda/CublasHandlePool.cpp).

Removed the redundant and subsequently unused action field mask caused by duplicate computation of the fused PPO loss.
The post-step KL check and rollback logic for complete minibatches are still executed, preserving the independent native LayerNorm boundaries previously fixed by the decoder.

## Verification and Recovery

GPU coverage width comparison 40/48, 286 tokens, complete and irregular masks, and same compiled function read-through
Updated mask; forward and gradient consistent with FP32 reference within BF16 tolerance, gradient of masked keys is 0.
33 related regression tests, 2 GPU numerical tests, mypy passed for Ruff and 678 source files.

Execute revision using `python -m kagg_revue.learning.league.upgrade`, accepting only binding of the current turn's checkpoint, complete original protocol, native, and final source code qualification reports. Old source code and recovery points are retained.
In `runtime-revisions/`, no existing weight files are rewritten. Updates to qualification copies cannot serve as official recovery weights. The order of floating-point attention reduction is changed, and no commitment is made to bit-level consistency with prior kernels during long-term training.

The official recovery entry point remains:

```bash
CUDA_VISIBLE_DEVICES=0,1 .venv/bin/python -m kagg_revue.learning.league.recovery
```

Independent replica completed Round 94 and 95, normally saved and stopped; then, after archiving recovery, completed Round 96.
All six networks were actually updated; all three models, six optimizers, dual-GPU RNG, and BC identities passed verification;
Additionally, 384 fixed-panel evaluations were completed. The first full training compilation took 280.09 seconds, and the archiving recovery first round took 97.24 seconds—both including compilation warm-up. Full records are available at
[qualification.json](../outputs/analysis/league-throughput-20260909/qualification.json).

Formal operation has continued from Round 93 originally, with the activated source code SHA256 being
`7cc8cd84b6fb39d601496af206f768434b4782a1b51c70869158ce463726129f`.
See [Execution Revision](../outputs/analysis/league-throughput-20260909/transition.json) and
[Official Launch](../outputs/analysis/league-throughput-20260909/formal-launch.json).

Formal Rounds 94–96 have been completed and the joint checkpoint has been submitted. The preheated 95/96 round achieved a time of **30.11 / 30.01 seconds**, with an average power consumption of **663.6 / 656.3 W** for the two-GPU PPO phase, and GPU utilization approximately **93.9% / 93.7%**. All three Actor/Critic models were updated, and each of the six optimizers advanced by 48 steps. The original parameter set, protocol, and BC identity were preserved, and both CUDA RNGs were advanced. The checkpoint includes all model and state tensor components. See
[Formal Checkpoint Verification](../outputs/analysis/league-throughput-20260909/formal-verification.json) and
[Formal Power Consumption Statistics](../outputs/analysis/league-throughput-20260909/formal-power-summary.json).
