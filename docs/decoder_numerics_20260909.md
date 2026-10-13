# Decoder Numerical Fault in Three-Expert Training

2026-09-09 07:22:48 UTC, `league3-20260909-s63001` stopped in the 4th BC epoch of B+C due to non-finite likelihood. A has completed 6 epochs, B+C has completed 3 epochs, shard cursor saved at 728, real-time completed cursor at 730; SpaTaro and formal RL have not yet started. The failed next shard is manifest index 141. Faulty run, model, and optimizer are retained.

## Root Cause Evidence

Input, parameter saving, and regular BF16 execution are all limited. Compared to compiled execution and regular execution, the first NaN appears after LayerNorm in the shared conditional network, then propagates to the market decoder. The previous measures of disabling cuDNN attention and BF16 low-precision accumulation have not fully resolved the issue; replacing the compilation cache also does not prove the fix.

Fill the temporarily allocated memory with NaN during compilation to reliably trigger an exception. Further, extract the generated fused normalization kernel and execute it with identical finite random inputs, varying only the initial content of the temporary buffer: when filled with 0, the output remains finite but differs from native normalization by at most 6.28125; when filled with 123, the maximum difference reaches 161; when filled with NaN, the output becomes NaN.
The result depends on data that has not yet been properly written, indicating this is not a data labeling issue or gradient explosion.

Merge two adjacent normalization steps and the saved backward statistics into multiple reduction loops; the intermediate buffer writes first, then reads, and is overwritten again; the actual compiled result incorrectly uses the previous buffer content.
Disabling `inplace_buffers` still reproduces the issue and cannot serve as a fix.

Detailed evidence and the SHA256 of the original generated code are available at [root-cause.json](../outputs/analysis/league-failure-20260909/root-cause.json).

## Direct Fix

`policy/grounded/normalization.py` provides independent native forward and backward operator boundaries for the typed grounded decoder, preventing the compiler from incorrectly fusing adjacent normalizations.
Module parameter names, shapes, epsilon, normalization formula, and gradients are preserved and consistent, while the rest of the network is still compiled, supporting CUDA Graph. No exception retries, eager fallback, sample discards, or NaN replacements are performed.
In PPO, non-finite KL values directly trigger errors and are not treated as ordinary KL overflow cases that would skip the actor or reduce the learning rate.

The fixed original erroneous batch, under both regular temporary allocation and NaN filling allocation, exhibits compilation loss of
0.45764076709747314, with all forward and gradient values being finite. The native BF16 reference is
0.4575560986995697; all other compiled operations show normal rounding differences.
Independent unit tests verify bit-level consistency with native LayerNorm outputs and inputs, as well as weight and bias gradients, for both two-dimensional and unit-dimensional inputs, and cover AOT autograd.

## Training Processing

Since this fault may produce limited but erroneous results, the BC runs with faults cannot be considered valid terminal points. After repair, use the new directory `league3-20260909-s63001-fixed`, and retrain A, B+C, and SpaTaro for 6 BC epochs each from the same random seed, then perform a full 100k turn RL. The original run will not automatically resume; the training data, model size, learning rate, two GPUs, sampling quantity, and training budget remain unchanged from the original request.

The actual training-weighted double-GPU PPO verification is executed only on isolated in-memory copies, using isolated 3780000000 starting seeds; its weights do not enter formal new runs. The verification includes full real-game play, CUDA Graph sampling, prefix critic, three-model PPO updates, and parameter and optimizer checks. Results are available in [ppo-verification.json](../outputs/analysis/league-failure-20260909/ppo-verification.json).

Final source code `ed97378a7fe65380cf5ab139171627c7836c4a892987b04b87b97ba87c892fb8`
Passed full NaN filling checks across all 18 fault injection shards, and 2 rounds of 384 real-world two-GPU matchups.
The Actor for A, B+C, and SpaTaro updated 16, 21, and 32 steps respectively, while the Critic updated 32 steps for each.
Post-warmup, 41.13 seconds per turn, peak of 94.16 GiB per GPU. All earlier three-round explorations also passed.
Ruff, mypy full (669 files), and 10 related tests passed.
See [complete acceptance record](../outputs/analysis/league-failure-20260909/repair-qualification.json).

The formal new runs have also been completed for A, B+C, and SpaTaro, each for 6 epochs of BC, using 4,283,832, 11,218,098, and 974,952 training records respectively, with optimization steps of 4,830, 11,628, and 1,290. The final held-out NLL values are 0.0454118, 0.3180635, and 0.5663024. The parameters, optimizers, epoch-by-epoch step counts, and checkpoint hashes at the end of each BC have all been confirmed.

Subsequently, three formal RL rounds were completed. The A/B+C/SpaTaro Actor accumulated 20/46/32 steps, while the Critic reached 48 steps each. In the first two rounds, when first encountering new training/KL computation graphs, additional warm-up was included; in the third round, the duration was 40.42 seconds with a peak memory usage of 94.14 GiB per card. A joint checkpoint saved the entire model, six optimizers, and two worker RNGs. After restoring from the archive entry in Round 3, Round 4 was also completed and submitted, with limited parameters and optimizers, continuous step count and checkpoint parent chain. Training is now continuing on GPU0 + GPU1 for a total of 100,000 rounds. See [Formal Verification Record](../outputs/learning/league3-20260909-s63001-fixed/formal-verification.json).
