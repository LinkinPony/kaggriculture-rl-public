# PFSP Has Mastered Opponent Frequency Reduction

**2026-09-28 Follow-up:** New learners will inherit the previous learner's discount evidence and mastered states,
see [PFSP Inheritance](pfsp_inheritance_20260928.md).

**September 28, 2026 Update:** According to user request, subsequent new PFSP training will default to enable this rule.
Normal training startup, historical pool bootstrap, and BC→RL workflows complete the missing `mastery` settings prior to protocol freezing; thresholds remain at 64 games, 95%, with a combined 5% review probability.
The deserialization of the original historical protocol remains unchanged; old runs restore values as saved; new bootstrap runs also restore previously saved valid values when resumed with the original Hydra configuration. Explicit configurations take precedence, and `mastery: null` is only set when explicitly requested by the user. Project conventions have been recorded in `AGENTS.md`.
The frozen protocol for new run `derived-v5b-m384-boey-watch4-ppo50-warmup300-20260928-s97001` explicitly enables the rule, inheriting the [existing thresholds](#section-629c646a7707) below.
The 11 targeted tests—missing configuration defaults on, explicit overrides, old protocol restoration, new bootstrap resumption, and unified pool sampling—have passed. Ruff and mypy have also passed.

Follow user's request to directly modify the current training without ablation. Run:
`derived-v5b-m384-watch6-ppo50-warmup300-20260927-s95001`.

<a id="section-629c646a7707"></a>

## Rules

The unified pool and all historical weights, PFSP evidence are retained. Add optional Hydra configuration:

```yaml
population:
  pfsp:
    mastery:
      min_games: 64
      score_threshold: 0.95
      review_fraction: 0.05
```

When the opponent's last recorded interaction is saved as `effective_games >= 64` and `effective_score / effective_games >= 0.95`, enter the low-frequency recheck set.
Win count: 1, Draw count: 0.5; here, the valid evidence from the most recent actual measurement is used, without considering time decay as a sign of declining strength, nor permanently eliminating the opponent based on accumulated historical win rate.

Recheck collection collectively obtains **5% of PFSP sampling probability**, evenly distributed among members; the remaining 95% continues within the normal collection using the original loss square, uniform exploration, and latest snapshot mixing. The latest snapshot remains within the normal collection. Thus, uniform exploration will not allow a large number of previously mastered opponents to regain budget. The recheck normally updates existing valid statistics and reverts to normal sampling when thresholds are no longer met. When no recheck members are present, the original algorithm is used; when no normal members exist and no latest snapshot is available for protection, uniform recheck applies to the entire pool. Sampling results and historical protocols not enabled by configuration remain unchanged.

Each turn still consists of **64 self-play games + 64 unified PFSP games**; 5% corresponds to the expected value of all physical matches.
2.5% is not a fixed quota for each short window. The script and neural strategy follow the same rules.
Rewards, learning rate, optimizer, RNG, and sampling batch methods remain unchanged.

## Actual Switch

Training completed fully at **U889 / 113,792 games**. Boundary checkpoints, original ledger, and qualification reports are saved at
[`outputs/analysis/pfsp-mastery-s95001-20260927/`](../outputs/analysis/pfsp-mastery-s95001-20260927/).

In this fixed state, among 412 opponents, 304 enter the review set, reducing their combined sampling probability in the next round from 54.83% to 5%. The remaining 108 opponents receive 95%. This is only a deterministic validation of sampling allocation, not a conclusion regarding training gain or strength improvement.

Use the existing `learning.recovery.population` record protocol and freeze source code revisions, then restore the same runtime via `learning.recovery.cli`. Enable new rules starting from **U890**.
Full configuration see [change.yaml](../outputs/analysis/pfsp-mastery-s95001-20260927/change.yaml),
boundary evidence see [qualification.json](../outputs/analysis/pfsp-mastery-s95001-20260927/qualification.json).

## Verification

28 targeted tests passed, covering evidence threshold, expired statistics, re-examination downgrade, budget cap, latest snapshot, empty set, old protocol compatibility, and dual rank deterministic recovery. Ruff and all 994 source code files passed mypy.

When running the old standalone script pool test additionally, `test_script_replacement_preserves_checkpoint_evidence_and_history_pool`
failed due to forged manifest hash; the same failure has been reproduced in this run with the original frozen source code, without modifying the old test.
Logs available at [baseline-test.log](../outputs/analysis/pfsp-mastery-s95001-20260927/baseline-test.log).

Formal continuation training **U890–U892 / 384 new games added** — verified: all PFSP selections and probabilities can be precisely replayed,
both Actor and Critic have been updated, each Adam optimizer continues for 12 steps, all tensors are finite, and dual rank RNG is fully intact.
64/64 ratio is maintained, the combined probability of the 304 reviewed members remains at 5%. See
[running-verification.json](../outputs/analysis/pfsp-mastery-s95001-20260927/running-verification.json).

Training continues. The original BC→RL workflow supervisor has ended normally; the current training status is based on the training directory's
`run-status.json`, `recovery-status.json`, and `learning-progress.json`.
