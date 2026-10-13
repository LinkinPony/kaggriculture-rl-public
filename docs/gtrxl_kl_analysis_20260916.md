# KL, Learning Rate, and Throughput Analysis of GTrXL, 2026-09-16

**Follow-up execution updates:** The user has authorized maintaining LR, increasing KL, enabling early stopping only, and disabling rollback.
Formal operation begins from U9 with Actor LR at 7.5e-6, Critic LR at 1e-4, KL at 0.05, pure self-play,
32 full trajectories per GPU. The four-round save/restore validation for the new pipeline has passed, and formal training has been resumed.
The following diagnostics and candidate recommendations retain the authorization prior to the update; terms such as "not yet applied" or "paused" reflect their status at that time.
Current facts are available at [mainline](CURRENT_MAINLINE.md) and
[resume verification](../outputs/analysis/gtrxl-20260916/selfplay-checkpoint-verification.json).

Analysis completed; LR remains unchanged. Formal training is still paused at U8.
Actor LR = 7.5e-6, Critic LR = 1e-4, KL threshold = 0.01, clip = 0.1 remain unmodified.
Five rounds of BC have been completed; subsequent RL explicitly requires pure self-play, with script and PFSP history pool temporarily disabled.
The isolation performance test at 3e-6 has been canceled; no measurement was conducted, and it has not been recorded in the formal training status.

## Existing Evidence

| Project | Observation |
| --- | --- |
| Formal U1–U8 | 1,024 games, Actor receives 0 steps, Critic receives 168 steps |
| U8 Actor Adam | state is empty; after the first step rollback in each round, the optimizer remains in RL cold-start state |
| Mixed opponent diagnosis replica | U9 and U10 candidate first-step KL values are 0.02211 and 0.02299, respectively |
| Pure self-play, 32 full trajectories per GPU | Three repeated measurements under the same checkpoint and same sampling seed yield a first-step KL of approximately 0.03060–0.03061 |
| KL between sampling and replay without weight updates | Approximately 0.00015–0.00017, significantly smaller than the offset after candidate weight updates |
| Formal LR and KL | 7.5e-6 and 0.01; neither reduced nor relaxed |

Diagnosis copy: `outputs/learning/gtrxl-m384-kl-diagnostic-20260916-v1`.
Pure self-play measurement: `outputs/analysis/gtrxl-20260916/pure-batch32.json`.
The repeated measurements are calculations based on numerical diagnosis, not independent learning curves or win rate comparisons.

## Why Protection Mechanisms Might Block Cold Start

The order for each complete trajectory minibatch is: accumulate gradients, perform one Adam candidate update, reload the empty replay memory with the full prefix, compute KL; if it exceeds 0.01, roll back the weights and Adam states, and halt all remaining Actor updates in this turn. In the next round, resample anew, but the Actor still starts from the same parameters and empty Adam states.
This explains the observed zero updates over eight rounds. It does not prove that the strategy corresponding to KL values of 0.022–0.031 is necessarily safe or necessarily improves win rate, but it also does not justify the need to reduce the learning rate.

The current KL calculation is the sum over all valid action fields within each observation of `exp(log_ratio)-1-log_ratio`, followed by an averaging over observations weighted by trajectory weights. It does not involve direct summation across 719 turns or 384 turns of memory, nor is it the mean of individual valid fields. Since complete actions consist of multiple fields, it cannot be directly compared to the KL value of a single discrete action; the summation over fields inherently carries the meaning of a joint action distribution, and it is not valid to arbitrarily divide by the number of fields based on a threshold.

The current implementation simultaneously applies conditional probability clip = 0.1, KL stopping before update and strict rollback after update, with both KL controls sharing a value of 0.01. The clip has no limiting effect on the gradient when the ratio ≈ 1 at the first step update; it is actually the rollback after update that causes zero acceptance in the first step. In contrast, the reference implementation from OpenAI Spinning Up checks approximately 1.5×target_kl before subsequent iterations and stops, without reversing the just-occurred KL violation, indicating a difference in protection strength between the two approaches.
Reference code: https://github.com/openai/spinningup/blob/master/spinup/algos/pytorch/ppo/ppo.py

## Learning Rate and Learning Efficiency

Current evidence more supports "KL protection and initial step update scale mismatch". The actual acceptance of updates is zero, making it impossible to evaluate whether 7.5e-6 is overly conservative during normal learning. The nominal LR of Adam cannot directly represent the speed of strategy distribution movement; the current initial step has already generated approximately 0.02–0.03 in full-action KL.

When maintaining the same hard threshold, significantly increasing the LR is likely to make the initial step more prone to rejection. Lowering the LR might allow candidates to pass, but it has not yet been proven to improve strategy improvement per unit time, so we do not lower it at this stage.

Prioritize recalibrating the KL divergence protection: retain LR = 7.5e-6, distinguishing between soft targets that one wishes to stop updating (around 0.03) and hard upper bounds that require candidate rejection (around 0.05). These values—proposed based on current numbers—are **not yet implemented or applied, and are not proven to be optimal**. It is necessary to observe actual acceptance rates, tail behavior of action probabilities, entropy, clip fraction, and the performance of the strategy over continued training.

The original GTrXL paper uses V-MPO; discrete action constraint parameters are sampled from [0.001, 0.1).
This supports re-calibrating the constraints, but does not support directly transferring V-MPO values to our PPO rollback logic.
See the paper, page 5 and Appendix Table 8: https://arxiv.org/pdf/1910.06764

## Hardware throughput and effective learning progress need to be measured separately

Pure self-play, 128 games per turn, 32 trajectories per GPU, with two warm-up repetitions each taking approximately 25.0 seconds.
Average power consumption for two GPUs during sampling is 523–544 W, during training it is 619–654 W, with training utilization at 98–99%; peak allocated GPU memory is approximately 99.9 GB per GPU. Power consumption refers to full-card sampling; GPU 1 has unrelated tasks and cannot have its entire power consumption attributed to this training; GPU 0 also independently reaches approximately 619–626 W.
See `outputs/analysis/gtrxl-20260916/pure-batch32-power-summary.json`.

These measurements still reject the Actor candidate, so 25 seconds is not a normal throughput for continuous Actor updates.
Additionally, under pure self-play, increasing the per-GPU minibatch from 4 to 32 reduces the optimizer batch size per round from 32 to 4, while maintaining full sample coverage; it improves parallelism but alters the statistical batch size, and thus cannot equate hardware throughput to learning acceleration. The newly implemented K/V cache, compilation, and loss fusion optimizations have not yet achieved GPU consistency or formal acceptance and are not yet in formal operation.
