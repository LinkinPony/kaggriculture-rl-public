# compact289: Script adds unified PFSP pool

2026-09-21 User requests to add a script opponent to the current training. The target run is
`compact289-v4-selected8-ppo-restart-20260921-s74001`, not a halted large model or the first PPO round.
This uses the existing native C++ opponent, without adding Python turn callbacks or re-implementing strategies.

Configuration see [this pool revision](../configs/learning_compact_scripts_change_20260921.yaml).
Add the following five verified scripts:

- `ahmed_v45`
- `metacounter_r1`
- `shop_router_0913`
- `rayk_v38_low_pressure`
- `farming_v4_0914`

Before the switch, this branch only had uniformly sampled historical models from itself, with no PFSP states or script opponents.

This update enables unified PFSP: each turn remains **1024 games = 820 self-play games + 204 pool-vs-play games**,
where each game is drawn from the joint distribution between scripts and the historical models of this branch, with 204 games evenly distributed between two GPUs and both player positions.
Scripts have no dedicated allocation or minimum game quota; `script_population.fraction: 0` indicates no additional script budget is allocated,
and does not imply that scripts are disabled. The pool ratio is precisely `0.19921875`.

PFSP reuses existing implementation and parameters: loss square weight, 20% uniform exploration, 10% coverage of latest history, 8 neutral prior games, 128 update half-life, and an effective evidence upper limit of 256 games.
The script starts from the neutral prior; this branch previously had no PFSP statistics and does not borrow opponent win rates from other learners.
Existing training records are fully preserved, and the BC/PPO models from this branch are retained in the historical pool.
The historical capacity remains at 177, and the subsequent snapshot interval remains at 64 updates.

Only modify `population` and `script_population`. Keep two GPUs, γ=λ=1, three updates of Actor/Critic per turn (Actor still under KL early stopping constraint), full-sample training, original learning rate with 500 update warmup, and pure terminal WDL; warmup continues based on absolute updates. The only change in source code identity is the addition of Hydra configuration; the training implementation and rule engine remain unchanged.

Operated normally on U78 / 79,872 full games, then stopped normally with exit code 0.
Boundary checkpoints and old ledger are separately saved at
[`outputs/analysis/compact-scripts-pfsp-20260921/`](../outputs/analysis/compact-scripts-pfsp-20260921/).
The user explicitly requested to first resume training, then optimize script throughput; the remaining independent validation was therefore terminated early.
All five scripts completed full games with two seats each: 14,400 official observations and 7,190 script actions matching.
Independent replicas completed training, full save stop, and recovery from U82 archive; actual covered rounds, optimizer progress, and PFSP exact replay results are detailed in the validation report, and completion of the originally planned eight rounds is not claimed.

Registration revised to `population-revisions/0001`, effective from **U79**.
**05:33:09 UTC** official dual-GPU recovery initiated, parent process **3066404**, training process **3066477**.
The initial unified pool includes five scripts and four preserved models from this branch: BC, U64, U76, and U78.
The old complete checkpoint bytes, all saved training records, and member hashes are consistent; optimizers and dual-GPU RNG are continued from the original U78. Updates from independent replicas are not written into the official runtime.

Evidence: [Stop Recording](../outputs/analysis/compact-scripts-pfsp-20260921/stopped.json),
[Source Code Differences](../outputs/analysis/compact-scripts-pfsp-20260921/source-comparison.json),
[Access Verification](../outputs/analysis/compact-scripts-pfsp-20260921/qualification.json),
[Migration Validation](../outputs/analysis/compact-scripts-pfsp-20260921/transition-verification.json),
[Formal Launch](../outputs/analysis/compact-scripts-pfsp-20260921/launch.json).
