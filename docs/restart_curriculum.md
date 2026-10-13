# Multi-source Replay State Course

## Purpose and Scope

The grounded single-turn interface resolves random credit issues for absent units, but both seeds initialized from the starting state have learned the strategy of "less procurement, less sowing, no harvest." In this turn, we use the existing farm state from the current daily replay to allow the random policy to encounter production actions within a shorter operation sequence, gradually returning to the full initial state. The original replay actions are not used as training labels.

Training entry remains `kagg_revue.learning.cli`, explicitly select `--config-name learning_curriculum`.
All models and anchors start from new random parameters; no prior models from the first two rounds or weights from previous instructions are used.
Input contains only hashed-bound original data indices; checkpoint, teacher, BC, and script opponent inputs remain closed.

## Environment Recovery

`datasets.restarts.RestartBank` Bind the manifest, original ZIP, index, and per-turn replay content SHA256.
Both seats are assigned to the same source partition using the same environment seed. Candidates are not filtered by future returns; only the cash difference, unit capacity, and pre-declared upper limit of source count are used.

`ParallelBatch.replay_prefixes` replays actions from the official seed to gradually reconstruct the public history. It only accepts a fresh self-play batch: first parses the input, then replays it on a fork, and only replaces the original batch after all steps succeed, avoiding partial updates in case of failure.
On entry, it performs field-by-field comparison of both sides' states, and bitwise compares the `ContractSession`-encoded native features with sequentially consumed raw official observations, including public history and unit support. Official frames missing a step are padded with their frame number; if explicit clock inconsistencies are detected, the process is rejected. The verified state bank remains unchanged, and each training run starts from a fork.

The actor still only receives private information from its own side and observable public state. The PPO tape starts from the entry point; actions, probabilities, and observations in the original prefix do not enter the optimizer. Breakpoint recovery reconstructs the source state based on the original configuration and deterministic sampling seeds for each update.

## Experiment Protocol

The reserved budgets for `scratch-curriculum-s43001` and `scratch-curriculum-s43002` are both 64 × 128 games.
The training source code archive fingerprint is `87fd06468b04fd4285f2927f99505f4c5b58d91f3fde87f2fe4493654c6667e5`.
Each phase has 8 updates, with entry points sequentially at 576, 384, 192, and 48; every fourth update starts at turn 0.
Updates 33–64 all start at turn 0. Each group consists of 5,120 full initial-state games and 3,072 suffix games;
the report also records the actual number of strategy transitions, not counting replay prefixes as online training effort.

Opponent remains at 50% current self-play and 50% historical neural strategy running internally. Training data sources are limited to at most 128 matches from the training arena, sliced in fixed hash order by episode; the number of displayed names does not represent the number of distinct strategy versions.
Source conditions require that the cash difference between both sides does not exceed `0.2 * max(3000, cash0, cash1)`, and the number of units does not exceed model capacity.

The reward for this training turn is:

`sign(own terminal cash - opponent terminal cash) + (own terminal cash - own cash at entry) / 1000`

Subtracting the injection cash is a state-dependent constant, and the wealth existing prior to takeover should not be considered as earnings from the new strategy.
The cash component is a clearly defined auxiliary objective, and its gains should not be equated with an improvement in match win rate; this round does not claim that the auxiliary objective guarantees optimal final match performance. The fixed evaluation always starts from turn 0, reporting only direct WDL and terminal cash.
Selection occurs every 8 updates, and independent confirmation seeds are only read after the full budget is exhausted.

`learning.probes` Additionally provides suffix evaluation from the leftover suffixes: for each source state, run both seats, three random anchors from the same experiment, compare WDL and cash difference, and provide paired intervals based on the source environment seed.
Suffix evaluation does not replace capability validation starting from turn 0, nor does it prove the competitive strength against external mature strategies.

## Evidence Already Obtained

- Added prefix replay, native dual-seat support and public history consistency, failure atomicity, fork isolation, PPO suffix boundary, cash baseline, source hash, and partition validation. All 40 relevant tests passed, as did Ruff and mypy over 528 source files.
- `scratch-curriculum-qualification-v1` failed during pre-training due to missing step field in real replay, resulting in no updates being performed and retaining a failed state; subsequent fix started from a new random root and did not bypass source or recovery checks.
- `scratch-curriculum-qualification-v2` completed three turns starting from 576, performing updates and one full season update totaling 32 games. Results of 24 full-initial-state games were confirmed to match those of a randomly initialized model.
- Deterministic FP32 interruption recovery verification passed: after sending SIGTERM at update 1, the system reloaded the source bank and resumed training to update 3, with actor, critic, two optimizers, CPU/CUDA RNG, source sampling, and cash outcomes matching bit-for-bit with continuous training. Reported as `outputs/learning/scratch-curriculum-resume-challenge-v1/resume-verification.json`.
  This validation requires deterministic algorithms and `CUBLAS_WORKSPACE_CONFIG=:4096:8`, and does not extend to default BF16.
- In 4 independent mirror suffix audits with separate sources, both initial and final policies executed 8 harvests and 6 irrigations, including fertilization and fertilizer collection; sales revenue was 630 in each case, purchases were 6,172, and net cash mean was -692.75.
  This demonstrates that the curriculum exposes effective production actions, but does not prove that better business strategies have been learned.

The technical qualification, suffix behavior, and source pairing reports are located at:
`outputs/learning/scratch-curriculum-qualification-v2/`,
`outputs/analysis/scratch-curriculum-qualification-behavior/`,
`outputs/analysis/scratch-curriculum-qualification-probe/`.
Two complete budget experiments of 64 rounds each have concluded, with no zero-start operational capability observed: at both endpoints, in 8 full-image matches with identical seeds, there were no sowing, no harvesting, and no sales—only expenditures of 1 and 0, respectively. The source suffix cash retained at turn 576 increased by approximately 828.26/781.95 compared to the initial model, but the net cash mean remained only 73.45/57.36, making it unextrapolable to initial investment.
Complete results are available in `outputs/analysis/scratch-curriculum-baseline/` and the behavior/source curves in the current mainline.

## Turn-by-turn correspondence between the opening phase and sales volume

v2 adds turn indices 1, 3, 6, 12, totaling 21,846 candidate states; the source partition remains unchanged.
`learning_reverse.yaml` refines the entry point to 576, 384, 192, 96, 48, 24, 12, 6, 3, 1;
each phase consists of 8 rounds, with a full initial state maintained every fourth round; a total of 128 rounds, with the last 48 rounds starting entirely from the initial state.
As planned, each branch includes 8,704 full initial state games and 7,680 suffix games.

Add a semantic switch for the `operation_quantity_bias` model. When enabled, market quantity logits are augmented with learnable biases indexed by order operations; during initialization, the original sales quantity inherits only the procurement quantity penalty previously assigned. The initial procurement distribution, market operation distribution, and other shared parameters remain unchanged; no modifications are made to the quantity vocabulary, official inventory caps, or cash rules. Original large-scale sales requests are executed by official settlement based on the actual inventory held. This switch is saved along with the model layout, and the default state for new mainline checkpoints is disabled. Current neural gameplay now evaluates compatibility based on observations, actions, and time interfaces, allowing different network capacities or quantity bias models to use the same native game interface.

`scratch-reverse-volume-qualification-v1`'s 8 source upper limit had no eligible candidates in turn 1 that met the cash difference condition; exited training prior to training. Cash difference rules were not relaxed.
`...qualification-v2` increased to 32 sources, actually verified the 25 roots in turn 3 and the 13 roots in turn 1, completed 2 × 8 suffixes with newly randomized weights and performed full confirmation. It proved that non-day boundaries, quantity bias, and save/load paths are operational; it does not prove operational improvement.

The first two branches are `scratch-reverse-volume-s45001` (enabled) and `scratch-reverse-shared-s45001` (disabled). They share the initialization seed 45001, source sampling seed, and budget; each branch independently generates a random root; all shared initial tensors are bit-identical, with the only newly introduced parameter being the count bias table. This is a paired switch configuration for the initialization seed, not two independent RNG reproductions. Initialization evidence is located in `outputs/analysis/scratch-reverse-ablation/initialization-control.json`.
The training source code archive fingerprint is `06c092c55d1e794657ed3bfd555e2eb5843f2ba46a30c31258aa601a3b05d752`.
Both branches terminated after 48 turns due to a failure in the source feature verification at turn 12, without collecting turn 49 or fully reading the budget confirmation. The full initial state mirror audit for turn 48 shows only 3/2 seedings, zero harvests; thus, this interruption cannot be used as evidence of the complete budget algorithm outcome. Failure reasons and fixes are detailed in the next section.

## Turn Order of Inventory Items in Daily JSON

The original JSON sorts dictionary keys by name, which does not preserve the insertion order of the backpack in the official Python environment. The backpack order affects DROP and cross-day warehouse overflow settlements, and there is a separate field in actor inputs. Previous field-by-field audits of dictionary values could not detect this order discrepancy; the day boundary entry happens to clear the backpack. Among the 128 training roots in turn 12, 6 triggered feature verification as a result, and both training branches failed as expected before consuming the erroneous source.

`datasets.observations.ReplayObservations` starts tracking the key sets of each unit from turn 0 with an empty backpack.
According to the official rules, a unit can add at most one item key per turn, so the existing order of old keys can be preserved and new keys appended sequentially; deletions, re-adding, and cross-day clearing are reflected in the next frame's key set. Reads are rejected when the source is not a complete prefix or when multiple new keys cannot be uniquely reconstructed. It does not correct reference values based on native outputs, does not use future observations, and does not pass source actions to PPO.

The updated daily audit runs the hash-fixed official 1.32.7 interpreter, comparing against the native engine and the original replay with restored sequence. All 64 complete trajectories and 92,160 mutual observations passed, including backpack key sequences. See `outputs/analysis/daily-20260906-inventory-order-audit/report.json`.
Training invokes `RestartBank.prepare()` to verify all declared entry points prior to the first PPO, and saves `source-qualification.json`. The v2 branch has been launched from two independently initialized random roots, with output paths at `scratch-reverse-volume-v2-s45001` and `scratch-reverse-shared-v2-s45001`; both share identical initial parameters, with no continuation from round 48 of the first round. Both branches have completed pre-launch verification for 10 entry points and 1,040 training roots. The launch source code fingerprint is `c69da90c279d2b8ad90f9a6e8a03917c88795753a1dc47a4c9281c84c3169e82`, with each branch still set to 128 turns.

Both have completed 128 rounds and exited. Each branch conducted 16,384 games and 10,749,440 strategy transitions, with actor updates occurring 2,826/2,586 times—none of which involved rollback. The terminal mirror match has not yet produced seeding or harvesting; in the active branch, there are minor wheat buy-sell activities, while the inactive branch retains the initial cash balance. Against the same group of internal neural opponents trained in this session, the active branch's score increased from 7.81%/46.09%/60.55% at Round 32/64/96 to 69.53%, whereas the inactive branch ended at 50.39%. The active branch's terminal average cash balance was 2,992, still below the initial capital; thus, this trajectory cannot be directly labeled as sustainable profitability or competitive scalability. Detailed identities, per-game results for dual positions, seed-clustered intervals, and full behavioral patterns are available in the v2 report linked in the current main thread.

## Building and Restoring Archives

The new runtime will now include CMake, CUDA, and C++ `.inc` files in the source code fingerprint, and will store the actual native binaries used at `native/` for verification upon restoration. The above four primary runtimes have been supplemented with `build-provenance/`, preserving native binaries, build files, and CUDA inputs that match the SHA256 in the ledger; prior to this, each archived native source code and these build inputs were individually verified to belong to the same current version. Separate records have been maintained for the supplement's inventory, timestamp, and scope.
