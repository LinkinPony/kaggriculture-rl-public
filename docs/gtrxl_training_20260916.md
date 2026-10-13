# Gated entity and temporal training, 2026-09-16

User authorized: stop s68001; implement the final gated entity + temporal architecture;
no ablations; temporal cache is 384 **turns**, with four summaries per turn;
BC on latest three complete daily dates, then start formal pure-terminal WDL RL.

Latest execution (10:12 UTC): five-epoch BC is complete. The same formal run has
resumed from U8 using pure self-play, actor LR 7.5e-6, critic LR 1e-4, KL 0.05,
and early stopping without rollback. Scripts and PFSP sampling are disabled;
their historical artifacts are preserved. This supersedes the original mixed-pool
and rollback settings recorded below. The final continuation record is at the end.

Current work: s68001 received SIGTERM via its verified recovery parent and stopped
normally at U6105. Existing dirty changes predate this task and must be preserved.
Stop request record: outputs/analysis/gtrxl-20260916/stop-request.json.

Implementation specification:
- Grounded-v2 observation/action semantics and native script opponents retained.
- Actor entity 6x384, critic entity 3x320, 8 heads, FFN expansion 2.
- Full GRU residual gates in both sublayers, update bias subtracted with initial 2.
- Actor and critic each have independent 2x256 temporal stacks, 8 heads,
  four learned summaries per turn, relative time positions, 384-turn sliding cache.
- Spatial representations remain available to the decoder through gated memory fusion.
- Preserve unsupported BC frames as context; mask only their supervised loss.
- Whole-episode prefix processing, causal chunking and detached temporal state;
  no single-row shuffle for recurrent learning and no stale state across optimizer steps.
- User subsequently extended formal BC to five epochs; same teacher screening
  and seed partition convention, strictly latest three daily dates (no older supplement).
- Retain pure terminal win/draw/loss +1/0/-1, 30/20/50 self/script/history,
  frozen previous actors as opponents, fresh random learner root.
- Necessary correctness/throughput/recovery checks are qualification, not ablations.
- Finish BC and verify actual formal RL checkpoint before declaring task complete.

## Implemented and checked

- New packages: policy/memory, learning/sequences, datasets/sequences.
- Temporal attention uses Transformer-XL content and sinusoidal relative-position terms;
  masks operate in turn units, allowing the four same-turn summaries to interact.
- Full-episode PPO minibatches (4 trajectories per rank), 48-turn gradient segments;
  optimizer changes only after the complete episode, so cached state never crosses
  an optimizer change. KL rollback recomputes complete prefixes using candidate weights.
- After the user's throughput request, BC packs 64 complete trajectories per step,
  32 on each H200. All context frames remain in order; only final-batch padding
  has zero loss. Five epochs expose 9,897,105 eligible rows in 220
  optimizer steps. Formal batch_rows is 46,016, with 48-turn activation chunks.
- Inference caches projected K/V within each fixed-weight episode, then clears
  them at every new game; training still recomputes full prefixes under current weights.
  Complete 719-turn BF16 cached sampling vs replay has mean prefix KL 1.0517e-5.
- Both BC and RL pad only loss-free final time/seat slots to fixed tensor shapes,
  avoiding redundant compiler variants. No real observation or supervised row is dropped.
- Eager actor compute profiling at 8/16/32 trajectories per GPU measured
  2,578 / 3,009 / 3,278 rows/s, with peak allocated 19.6 / 39.0 / 77.9 GB.
  These exclude compilation, IO and collectives; actual distributed timings follow.
- Parameters: actor 23,663,258; critic 10,869,122; total 34,532,380.
- Necessary causality, K/V, packing/padding and related regression tests: 32 passed.
- Dataset: 1,856 retained episodes; 1 excluded abnormal episode; 5,568 arrays
  authenticated. Nine full official games match 12,960 observations, all sampled
  12,223 encoded rows/labels match reconstructed complete trajectories.
- Full 719-turn BF16 sampling/replay consistency: mean unchanged-policy prefix KL
  1.0517e-5 with K/V caching; 384-turn eviction, new-episode reset and missing-frame
  rejection passed. FP32 component checks
  also passed (maximum active-field logprob difference 4.77e-7).
- Formal config: configs/learning_gtrxl_20260916.yaml. Random root 70001,
  output outputs/learning/gtrxl-m384-3d-20260916-s70001; formally launched at 09:00 UTC.
  Population contains 137 external models (86 existing + 51 from stopped s68001),
  capacity 177. Formal training/evaluation seed intervals have no overlap across
  83 existing runs or the BC source worlds; see seed-audit.json.

## Qualification and formal execution

First whole-sequence TorchInductor compilation in qualification-v1 crashed with
SIGSEGV while a diagnostic SIGUSR1 stack dump was requested. No BC or RL checkpoint
was produced. This is a failed engineering trial, not an architecture ablation.
Qualification-v2 compiles scene, temporal and decoder components separately.
Run outputs/learning/gtrxl-m384-qualification-20260916-v2. BC stopped normally at
cursor 2 with finite actor and optimizer tensors, then resumed from the authenticated
source archive through cursor 4 / two epochs and transitioned automatically to RL.
BC held-out NLL was 1.65825 then 1.56160 on the small integration fixture; these
are engineering checks, not formal training or model-quality claims.
The first RL update in v2 then hit Dynamo's default eight-variant compile limit:
scene.forward is shared by actor/critic, gradient/no-gradient passes and tail chunks.
No RL checkpoint was committed. Bounded compilation now permits 64 static variants;
Qualification-v3 stopped normally after U3 / 96 games: both optimizers advanced
16 steps, actor and critic memory changed, tensors remained finite, independent
rank RNGs advanced, terminal WDL and exact PFSP replay passed. U3 without new
compilation took about 24.8 seconds for 32 physical games. See v3 verification JSON.
The user's throughput request arrived during that run. Qualification-v4 now uses
the optimized pipeline, 64-trajectory BC and formal-size 128-game RL collection.
Its fixture contains 162 training episodes / 274 trajectories across all three days,
with 10 BC optimizer steps for two epochs. Run
outputs/learning/gtrxl-m384-qualification-20260916-v4 failed before the first BC
commit because the padded 720th compute slot indexed the 719-entry action-span
table. Padded slots now clamp only their action-credit clock, retain causal temporal
positions, and have zero loss. A boundary assertion was added to the padding test.
Qualification-v5 completed the optimized protocol: BC stopped at cursor 2 and
resumed through cursor 10, RL stopped after U3 and resumed through U4. Both
optimizers advanced 84 steps over 512 physical games. Actor/critic memory updated,
finite tensors, independent advancing rank RNGs, pure WDL and exact PFSP replay
passed. See optimized-qualification-verification.json. Warm U3 took 51.8 seconds
for 128 games while formal BC was also running; other qualification timings
include compilation or recovery and must not be treated as steady throughput.
All 137 formal historical checkpoint hashes match their frozen source ledgers.
Ruff, full mypy (808 source files, including the BC budget revision helper), and
32 related tests pass.
Do not signal SIGUSR1 during Inductor compilation. py-spy attachment is denied by
container ptrace permissions; this is optional debugging, not a task blocker.

Formal run ID d65ba778fd384a33a7715d823ab4fde0. The user changed BC to five epochs
after launch. The run stopped normally at BC cursor 73; its unchanged checkpoint
SHA is b1fa07cfe5afc82e30df7466387b0aad57eb4eca447232d538cc721409be31b5.
Budget revision bc-budget-revisions/0001 preserves the previous ledger and all
training state, changing only demonstrations.epochs from 2 to 5. Archived recovery
parent 861931 / child 862164 continues the same run from cursor 73, target 220.
Formal source hash remains 17641e57698e13bed7c9ce1ad3f91a5fe8e1f27fa341137b06473b73cfe97639.
Stable formal batches before the stop took roughly 4.2 seconds for 46k supervised
rows, including about 0.5 seconds loading; peak allocated memory was 65.85 GB/rank.

Formal BC completed all five epochs at 09:26 UTC: 220 optimizer steps and
9,897,105 supervised row exposures. Selection NLL by epoch was 1.0934621,
0.9406849, 0.8307085, 0.7671659, and 0.7252287; final training NLL was 0.7480389.
Endpoint pretraining/shard-000220.pt SHA is
cb1aa204b2b642d30da8700ddadc4488da8a1e8798b81243d0466580fc08e51f.
All checkpoint tensors are finite, every BC optimizer state reached step 220,
and both rank RNG states are present. See formal-bc-verification.json.
The 137 external historical opponents were imported and the initial post-BC/PFSP
ledger saved as formal-rl-initial.json before U1. Formal RL started at 09:28 UTC.

Formal RL stopped normally at U8 (1,024 physical games) at 09:35 UTC to investigate
KL protection: all eight actor candidate steps rolled back, while the critic
committed 168 steps. Consequently the initial formal verifier correctly rejected
the run for lacking actor updates. The BC endpoint is unchanged and authenticated.
An isolated diagnostic branch from U8 records attempted post-step KL; the initial
metrics recorded only accepted divergence. User also requested throughput
optimization and then explicitly requested **pure self-play**, with scripts and
PFSP history disabled for continuation. Preserve all old artifacts.

Outstanding: resolve actor KL rejections, profile and optimize dual-GPU execution,
qualify the pure self-play continuation with stop/recovery, then migrate and resume
the same formal run. Authenticate actual actor/critic memory updates, advancing
rank RNGs and terminal WDL rewards before declaring completion. Leave the formal
run active after successful verification.
Latest steering supersedes immediate LR calibration: analyze first and do not
reduce LR for now. The isolated 3e-6 benchmark was cancelled before its first
measurement completed; formal LR remains 7.5e-6 and the run remains stopped at U8.
See gtrxl_kl_analysis_20260916.md for measured KL, optimizer cold-start behavior,
pure-self-play power measurements and proposed (not applied) guard calibration.
Subsequent user authorization now supersedes the analysis pause: keep LR 7.5e-6,
raise KL and use early stopping only, with no parameter or optimizer rollback;
then start training. Selected KL is 0.05. The continuation is pure self-play,
128 games/update, 32 trajectories/rank and 48-turn chunks. No architecture or
action-space change: MemoryPolicy still inherits the existing TypedGroundedPolicy.
The bounded compiled objectives, cached action masks, BF16 projected K/V caches
and compiled temporal inference step are included in the new qualification.
32 tests, Ruff and full mypy (809 files) passed before qualification.
No subagents are authorized by current developer instructions.

## Pure self-play continuation

Qualification `gtrxl-m384-selfplay-qualification-20260916-v1` completed U9–U12,
512 physical games, including a normal stop at U10 and authenticated archive
recovery. Both optimizers added 16 steps, with zero actor rollbacks; actor entity,
temporal and fusion parameters and critic memory changed. All tensors are finite,
independent rank RNGs advanced, actual returns are pure terminal WDL, and disabled
history/PFSP state is preserved. See `selfplay-checkpoint-verification.json`.

Full 719-turn cached inference versus replay with the trained BC checkpoint and
new compiled BF16 K/V execution has mean prefix KL 0.000216276. Cache eviction
at 384 turns and fresh-game reset pass (`compiled-trained-consistency.json`).
Warm qualification rounds take 32.1–32.6 seconds for 128 games and four updates
of each optimizer. Mean training-phase GPU power is 667.6/670.4 W and utilization
100%/99.8%; GPU 1 also has an unrelated process, so these are device-wide readings.
The timing is an execution measurement, not evidence of policy-strength gain.

Formal `sampling-revisions/0001` preserves the U8 checkpoint, optimizer, RNG,
run ID and all old artifacts. Its source archive SHA is
`d9cbd9205b68b9d57b54d495d6d52d8507919cafa01006c1a7735b5029344073`.
Recovery was launched at 10:12 UTC under parent PID 1061110. Formal U12 is saved
and verified: 512 continuation games, 16 new actor and critic steps, totals 16/184,
zero rollbacks, updated actor encoder/temporal/fusion and critic memory parameters,
finite tensors, advancing independent rank RNGs, pure WDL, and preserved history.
Checkpoint SHA is `cffb5e497d3fbfc6c9d16d69bce9fb8984c330fda418eadc931f5d0e1e1d43ad`.
See `formal-selfplay-verification.json`. Warm formal U10/U11/U12 took
32.15/32.18/32.35 seconds per 128 games. Formal RL remains active.

The action-space audit against old s68001 confirms identical observation and
action interfaces: grounded-v2, 276 factors, vocabulary size 101, 32 unit slots,
10 market slots, identical cardinalities and decision clock. `MemoryPolicy`
inherits `TypedGroundedPolicy` and uses its existing `decode_encoded`; typed
operation/quantity conditioning, masks and market budget logic remain in place.
See `action-interface-verification.json`.
