# Local Training Observation Desk

**September 24, 2026 Update:** As requested by users, the current `learning.train` no longer performs automatic "closed-loop" evaluations at startup, during cycles, and at termination regarding the starting point and random anchor points. The demonstrations for `evaluation/selection-*.json` and `confirmation-*.json` below pertain to historical versions and do not imply that these evaluations will continue to run automatically. Daily training continues to record PFSP performance against individual opponents. See [Deactivation Notice](s82001_resume_no_evaluation_20260924.md).

The monitoring page aggregates existing and actively written experiment artifacts under `outputs/` in read-only mode. It shows training status, resource usage, and closed-loop model performance. It does not modify checkpoints or automatically promote models based on training metrics.

Data sources are categorized by purpose:

- `metrics.jsonl` and TensorBoard scalar are used for training progress, loss, throughput, memory usage, and rollout diagnostics; long files are read incrementally and downsampled before being returned to the browser.
- `training-report.json`, `resolved-settings.json`, and artifact metadata are used to display target steps, reproducibility identity, and checkpoint status.
- `evaluation-report.json` is used for model performance, directly showing win/draw/loss results, final cash, and cash difference from official rule-based paired matches. Self-play win rate does not substitute for such evidence.
- Local process, CPU, memory, and NVIDIA GPU information are used to determine whether the task is still running and to assess resource pressure.

`learning/` runs grouped by "Overview / Opponent Performance / Training Diagnostics / Resources and Records".
The overview displays the latest fixed evaluation round and range, key progress cards, as well as recent script win rates, cash balance, and execution time.
Scripts default to one chart each, and can be switched to overlaid comparison; opponent filtering applies simultaneously to win rate, cash, and cash difference.
The run list separates active, in-progress, and historical runs, with historical runs defaulting to collapsed state, supporting pinning the current run and saving filters.

The training curve defaults to showing the most recent **500 updates**, with a backward rolling trend of **32 updates**. "Display raw data" is disabled by default. When checked, a light-colored raw line is overlaid; when unchecked, only the trend line is displayed; hidden raw points are not included in y-axis scaling. The KL plot still explicitly lists the original peak values within the selected interval. The trend window supports 1 / 8 / 32 / 128; win rate is calculated as total wins divided by total games in the window, cash is weighted by actual game count, and other scalar metrics are averaged over the record. The legend displays the window mean and relative change compared to the previous window; hovering over the legend shows the number of rounds covered, number of records, and the number of games applicable to each metric. These rolling training statistics do not constitute independent evaluation evidence.

Top range supports the last 100 / 500 / 2000 points, full duration, and custom ranges. Selecting any training chart will zoom in synchronously on all charts and pause the follow mode; "Return to Latest" restores the recent window. "Pause Follow" only fixes the chart interval, while real-time updates continue. All charts share the x-axis and hover position, supporting independent zooming. View settings, trend windows, original lines, layout, and opponent selection are saved in the browser, with fixed viewing intervals saved per run; automatic refresh retains these settings, and reloading the page restores them.

A new `/api/curves/<family>/<run>` interface builds a compact numerical column from the incremental construction of the full `metrics.jsonl`,
caching only a small number of recently viewed runs without maintaining a complete historical run list. It first computes trends on the full record, then down-samples according to the display interval; by default, it retains all points for intervals up to 2000 turns, and for longer intervals, it retains only the first and last points, extrema, and segment boundaries, returning the mean, extrema, count, and sample weights within each bucket. Early intervals can be zoomed back to retrieve original details; the interface does not rely on the previous overview's 400-point cache. Parameters are `window` (0 indicates full range), `start`, `end`, `smoothing`, and a comma-separated list of `tags`.

Configuration events are generated from actual recorded opponent compositions and execution device changes per turn, without hardcoding specific turn values.
Opponent changes reset the trend window; device changes only reset metrics such as duration, throughput, and GPU memory;
missing metrics are not filled with zeros, and no interpolation or accumulation of trends across missing intervals is performed. Expanding a configuration event allows viewing the changes before and after, and jumping to nearby turns.
PFSP explicitly records opponents not assigned in the current turn, continuing along the same trend segment based on actual match records, and trends are only calculated for real matches within the window; changes in script pool members still reset the window.

`learning/` Mainline displays the current stage via small atomic files `learning-progress.json`: data verification, demonstration pre-training, online PPO, and termination status. The pre-training section shows fixed epochs, completed shards, action lines, and training/validation NLL; this portion does not count toward the PPO update budget. The online phase displays cash, historical opponent scores, learning rate, KL divergence, and GPU memory, distinguishing between completed updates and saved checkpoint recovery points. The curves are read incrementally from submitted `metrics.jsonl` files, with a submission every 4 updates for every 100k runs, at most lagging behind real-time cards by 3 update steps. Monitoring does not repeatedly read the growing full `state.json` file to display progress.

The real-time progress snapshot includes the complete PFSP opponent pool, with a read limit and monitoring report consistent at 20 MiB.
On 2026-09-16, a bug was fixed where the old 64 KiB limit caused real-time information for large opponent pools to be discarded, and historical opponent details and script pool statistics to disappear; ordinary training and leagues now share the same bounded read logic.

The per-opponent training table reads `populations` for each round. It shows the game share, retained trajectories, complete games, wins/draws/losses, win rate, learner terminal cash, and cash margin for self-play, historical snapshots, and each script. The header identifies the latest saved round. Script win rate is wins divided by games; draws do not count as wins. Three script charts show win rate, terminal cash, and cash margin. Missing statistics from before script integration are not filled with zeros. These are training samples; fixed evaluation remains in its separate panel. Script game counts reflect the actual batch size for each round; the 128→512 transition does not recalculate earlier rounds.

"Opponent Record and Match History" aggregates all saved matches currently running, grouped by frozen opponent identity, covering historical models, scripts, members in the current pool who have not yet played, and opponents who have exited the pool. Checkpoints with the same name across different runs are not mixed by round; performance records are separately tracked for each learner. The table supports search by name/source/identity, filtering by type and pool status, column sorting, and 50 rows per page. Clicking on an opponent displays round-by-round results, identity information, and two trend charts.

Cumulative record covers the entire duration of current operation; interval performance and details follow the most recent 500 turns, the full duration, or a custom range above. Actual win rate is defined as wins divided by total games, while measured score is (wins + 0.5 × draws) divided by total games. Cash average is weighted by number of games. Missing matchups within an interval are displayed as null values; trends still use the backward rolling window set above, so trend data at the interval start can reference evidence from the window prior to the start. Estimated scores and probabilities recorded turn-by-turn are derived from logs prior to the current turn; the table's current PFSP value comes from a real-time snapshot; both are separately annotated with their update times.

The detail log only reads the global `metrics.jsonl` and `populations`, without duplicating or accumulating worker results, and does not read `state.json`. It shares incremental reading and limited run cache with the training curve. When appending, it processes only the newly added complete rows. On rollback, truncation, or replacement, it rebuilds the data. Missing game records with fixed identities in old logs show unassigned game counts; incomplete batches display missing entry warnings. When the current pool identity cannot be clearly determined, the original PFSP table is retained. Each detail entry is a summary of a training epoch's game session. Current outputs do not provide per-game action replay.

`evaluation/selection-*.json` and `confirmation-*.json` are displayed, supporting switching between opponents and budget points.
The same mode reuses the predefined seed; performance from self-initialization and random anchor points does not represent the strength of public opponents.
`?run=learning/<run-name>` can directly open a specific run. The current shared service runs in a named tmux session
`kagg_revue_monitor`, on port 8765, with TensorBoard redirection disabled.

Start:

```bash
python -m kagg_revue.monitor.cli
```

Ports and refresh strategies are managed by [monitor.yaml](../configs/monitor.yaml), and can be temporarily adjusted using Hydra override, for example:

```bash
python -m kagg_revue.monitor.cli port=8877 refresh_seconds=10
```

The service address is fixedly bound to IPv4 loopback; there is no host switch in the configuration. When running long-term, a named tmux session should be established according to repository conventions. If TensorBoard is started separately, `tensorboard_port` can be set to point to its local port; setting it to `null` will hide the redirect entry.

The backend provides read-only pages: `/` (Overview), `/api/overview` (Runtime Summary), `/api/runs/<family>/<run>` (Individual Run Details), `/api/curves/<family>/<run>` (Interval Curve), and `/api/health` (Health Status). The run identifier must be exactly a two-level relative path under `outputs/` and cannot be used to access other files in the repository.

The opponent history interface is `/api/opponents/<family>/<run>`, accepting the same `window/start/end/smoothing` parameters; `opponent` is the opponent identity key, `before` is the forward pagination cursor excluding the current round, and `limit` defaults to 50 with a maximum of 200. The interface returns full and interval summaries along with data coverage ranges, and includes the opponent's records and trends when a specific opponent is specified. The frontend only requests this data when viewing "Opponent Performance," and refreshes preserve the applied filters and expanded states.

The default interval, trend window, raw line toggle, full-point budget, and historical cache size are managed by `monitor.yaml`; display preferences saved in the browser take precedence over server-side defaults.
