This repo is for a Kaggle contest. Please see CONTEST.md for details (If you need).

Current training mainline, research incumbent, and deployment decisions live in
`docs/CURRENT_MAINLINE.md`. Treat that document and its linked resolved artifacts
as the authority rather than old design documents or runnable legacy commands.

Training and future policy optimization default to pure terminal WDL rewards:
win +1, draw 0, loss -1. Do not add absolute-cash, cash-margin, or intermediate
money rewards unless the user explicitly changes this instruction. Cash may
remain an observation and diagnostic metric. Preserve historical run artifacts.

Explicit exception requested on 2026-09-19: the current
`agronomy-v4-m384-bc100-3d-20260917-s73001` run uses terminal
`WDL + delta / (abs(delta) + 10000)`, where delta is own minus opponent
terminal cash. See `docs/CURRENT_MAINLINE.md` for the effective update and
authenticated reward revision.
The same run now samples scripts and historical policies from one unified PFSP
pool (70% of games), with 30% self-play. Scripts have no separate game quota or
minimum allocation; preserve their existing PFSP evidence.

Future new PFSP training defaults to mastered-opponent review sampling:
`mastery.min_games=64`, `mastery.score_threshold=0.95`, and
`mastery.review_fraction=0.05`. Keep this enabled unless the user explicitly
requests otherwise. Apply the same rule to scripts and historical policies;
preserve archived protocols and their evidence when restoring old runs.

Current and future PFSP training also inherits discounted predecessor evidence
(`inheritance.discount=0.5`): opponents the learner has not met start from the
nearest predecessor ledger's decayed evidence times `0.5 ** generation`, and an
inherited mastery status holds until the learner meets that opponent. History-pool
bootstrap applies it automatically; keep it enabled unless the user explicitly
requests otherwise.

DO NOT MODIFY ANYTHING IN third_party.

- Prefer existing native C++ script opponents; do not use per-turn Python
  opponent callbacks in training or reimplement available strategies unless necessary.
  Active ports live under `src/kagg_revue/native/csrc/opponents/compiled/`:
  `ahmed_v45`, `metacounter_r1`, `shop_router_0913`, `rayk_v38_low_pressure`,
  `farming_v4_0914`, `ahmed_v53`, and `thomas_metav4`.
  Their frozen public source is compiled ahead of time
  by `opponents/compilation/`; regenerate generated C++ instead of editing it.
  Ahmed `ahmed_v41`/`ahmed_v42`, Farming `farming_v4_0912`, Thomas `router_95`, `farming_v4`, Kaito v39/v48/v58, Shop Router 0908/0909,
  Mugundh v21 and Boatlee v21/v29 are retired compatibility assets.
  Reuse `opponents/native_batch.py::create_native_opponent_session` and
  `opponents/batches.py::create_batch` under `src/kagg_revue/`; these feed
  `_revue_native.ParallelBatch` (`csrc/parallel/legacy.cpp`), whose
  `advance_programs` executes opponents directly in C++ with the GIL released.
- All code should be implemented in src/.
- Organize Python code by domain subpackages under `src/kagg_revue/`; do not
  simulate package boundaries with filename prefixes such as `teacher_`, `rl_`,
  `bc_`, `cuda_`, or `rollout_`.
- Do NOT create too large files. Follow good software engineering practice.
- Follow google coding style.
- Check your code with mypy and ruff.
- Use Pydantic when it's necessary.
- Write test if and only if nesssery. DO NOT write tons of test.
- Use hydra to manage configs
- Store disposable temporary files under the repository-root `tmp/` directory.
  Do not use the system `/tmp` directory for project work, and clean
  task-specific temporary assets when they are no longer needed. Reusable
  downloaded datasets and external raw artifacts, including Kaggle episodes,
  replays, and logs, are not temporary: store them permanently under an
  appropriate gitignored `data/external/` directory instead of `tmp/`, and do
  not delete them during routine task cleanup. Preserve their provenance in a
  manifest when practical.
- Store all generated training run results under the repository-root,
  gitignored `outputs/` directory. This includes checkpoints, optimizer state,
  resolved training configuration, metrics, evaluation reports, and BC/PPO run
  artifacts. Do not write new training results under `data/`; reserve
  `data/external/` for reusable source datasets and external raw artifacts.
- Use git normally, DO NOT need approval from user.
