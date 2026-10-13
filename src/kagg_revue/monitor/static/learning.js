const version = new URL(import.meta.url).search;
const { activeMembers, leagueCards, leagueChartConfigurations, leagueLabel } = await import(`./league.js${version}`);
const { quadrantCards, quadrantCharts } = await import(`./quadrants.js${version}`);

export function learningStage(run) {
  if (run.learning?.league && run.learning.phase === "reinforcement_learning") return `${activeMembers(run).length} 模型联赛 PPO`;
  return {
    initializing: "初始化与数据校验",
    demonstrations: "多来源示范预训练",
    reinforcement_learning: "在线 PPO",
    complete: "完整训练已结束",
    stopped: "训练已停止",
    failed: "训练异常退出",
  }[run.learning?.phase] || "随机根 PPO";
}

export function opponentLabel(name) {
  if (name.includes("_vs_")) return leagueLabel(name);
  return {
    router_95: "Thomas Router 95.5%",
    farming_v4: "Farming V4",
    kaito_v58: "Kaito v58",
    boatlee_v29: "Boatlee v29",
    shop_router_0908: "Shop Router 0908",
    shop_router_0909: "Shop Router 0909",
  }[name] || name;
}

function snapshotLabel(entry, integer) {
  if (entry.kind === "script") return opponentLabel(entry.name);
  const update = entry.update === 0 ? "BC 终点" : `U${integer(entry.update)}`;
  const source = entry.source_run?.split("/").pop();
  const escaped = source?.replace(/[&<>"']/g, (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[char]);
  return escaped ? `${escaped} · ${update}` : update;
}

export function currentPopulationMetrics(latest, live = {}, savedUpdate = null) {
  const counts = live.population_games;
  if (!counts) return latest || {};
  if (live.pfsp?.enabled) {
    if (latest?.["rl/pfsp/enabled"] !== 1) return {};
    if (Number.isFinite(savedUpdate) && savedUpdate < live.pfsp.started_update) return {};
    if (Boolean(live.pfsp.separate_scripts) !== (latest?.["rl/pfsp/separate_scripts"] === 1)) return {};
    // A sampled update can have different opponents and rounded counts from the saved one.
    if (live.pfsp.unified || live.pfsp.separate_scripts) return latest;
    const fixed = ["self_play", "historical_self_play"].every((name) => (
      Number(latest?.[`rl/rollout/opponents/${name === "historical_self_play" ? "history" : name}/games`]) === counts[name]
    ));
    return fixed ? latest : {};
  }
  const matches = Object.entries(counts).every(([name, count]) => (
    Number(latest?.[`rl/rollout/opponents/${name === "historical_self_play" ? "history" : name}/games`]) === count
  ));
  return matches ? latest : {};
}

function compositionCard(live, f) {
  const { metricCard, integer, percent } = f;
  if (live.pfsp?.unified) {
    return metricCard("训练对局", `${percent(live.target_selfplay_fraction)} Self-play · ${percent(live.unified_pool_fraction)} 统一 PFSP`, `每轮 ${integer(live.games_per_update)} 场；本轮 Self-play ${integer(live.population_games?.self_play || 0)} 场；历史与脚本共享抽样概率`, 4);
  }
  if (live.pfsp?.separate_scripts) {
    const counts = live.population_games || {};
    const script = Object.entries(counts).find(([name]) => !["self_play", "historical_self_play"].includes(name));
    return metricCard("训练对局", `${percent(live.target_selfplay_fraction)} Self-play · ${percent(live.target_script_fraction)} 脚本 · ${percent(live.target_history_fraction)} 历史 PFSP`, `每轮 ${integer(live.games_per_update)} 场；${script ? `${opponentLabel(script[0])} ${integer(script[1])} 场` : "等待新配比首轮"}；脚本池内按近期比分自适应抽样`, 4);
  }
  if (live.population_games) {
    const scripts = Object.entries(live.population_games).filter(([name]) => !["self_play", "historical_self_play"].includes(name));
    const parts = [`${percent(live.selfplay_fraction)} Self-play`];
    if (live.script_fraction > 0) parts.push(`${percent(live.script_fraction)} 脚本`);
    if (live.history_fraction > 0) parts.push(`${percent(live.history_fraction)} 历史`);
    const detail = scripts.map(([name, count]) => `${opponentLabel(name)} ${integer(count)} 场`).join("；");
    if (live.pfsp?.enabled) parts.push("PFSP");
    return metricCard("训练对局", parts.join(" · "), `每轮 ${integer(live.games_per_update)} 场${detail ? `；${detail}` : "；当前模型控制双方"}`, 4);
  }
  return null;
}

export function learningCards(run, latest, f) {
  if (run.learning?.league) return leagueCards(run, latest, f);
  const { metricCard, integer, number, duration, bytes, percent } = f;
  const live = run.learning || {};
  const progress = run.progress || {};
  if (live.phase === "demonstrations" || live.phase === "initializing") {
    return [
      metricCard("当前阶段", learningStage(run), "固定多来源初始化，之后进入在线 PPO", 1),
      metricCard("示范 epoch", `${integer(live.epoch)} / ${integer(live.epochs || 4)}`, "固定监督预算", 2),
      metricCard("示范分片", `${integer(live.cursor)} / ${integer(live.total_shards)}`, "随训练自动刷新", 3),
      metricCard("已学习动作行", integer(live.rows), `优化器更新 ${integer(live.optimizer_steps)}`, 4),
      metricCard("当前分片 NLL", number(live.shard_nll, 4), "仅训练标签的负对数似然", 5),
      metricCard("留出 NLL", number(live.selection_nll, 4), "每个 epoch 结束后计算", 6),
      metricCard("在线 PPO 预算", integer(progress.target), "预训练不计入 PPO updates", 7),
      metricCard("预训练耗时", duration(live.elapsed_seconds), "包含训练与已完成的留出评估", 8),
    ];
  }
  return [
    metricCard("PPO Update", `${integer(live.update ?? progress.current)} / ${integer(progress.target)}`, `预计剩余 ${duration(progress.eta_seconds)}`, 1),
    metricCard("恢复点", integer(live.checkpoint_update ?? progress.current), `每 ${integer(live.checkpoint_interval || 1)} updates 保存`, 2),
    metricCard("终局现金", number(latest["rl/rollout/mean_terminal_cash"]), "训练采样中的双方现金均值", 3),
    compositionCard(live, f) || (live.pure_selfplay
      ? metricCard("训练对局", "100% Self-play", `当前模型控制双方；每轮 ${integer(live.games_per_update)} 场`, 4)
      : metricCard("历史对手比分", percent(latest["rl/run/history_score"]), "训练诊断；不等于固定对手评估", 4)),
    metricCard("累计在线比赛", integer(latest["rl/rollout/cumulative_physical_games"]), `本轮 ${integer(latest["rl/rollout/physical_games"])} 场`, 5),
    metricCard("Update 耗时", duration(latest["rl/system/update_elapsed_seconds"]), "采样与优化，不含保存和评估", 6),
    metricCard("Actor 学习率", number(latest["rl/optimization/actor_learning_rate"], 7), `KL ${number(latest["rl/optimization/maximum_accepted_post_step_kl"], 6)}`, 7),
    metricCard("价值损失", number(latest["rl/optimization/value_loss"], 4), "Critic 训练目标", 8),
    metricCard("GPU 内存峰值", bytes(latest["rl/system/cuda_peak_allocated_bytes"]), "本轮已分配显存", 9),
    ...quadrantCards(latest, f),
    ...(live.pfsp?.enabled ? [
      metricCard(live.pfsp.unified ? "PFSP 统一对手池" : "PFSP 历史池", `${integer(live.pfsp.pool_size)} 个对手`, `每 ${integer(live.pfsp.snapshot_interval)} 轮入池；保留 BC 终点、近期与较早策略`, 10),
      metricCard(live.pfsp.unified ? "当前池中对手" : "当前历史对手", !live.pfsp.selected ? "等待首轮采样" : snapshotLabel(live.pfsp.selected, integer), `U${integer(live.pfsp.update)} 采样；学习方预估比分 ${percent(live.pfsp.selected?.score)}`, 11),
      metricCard("PFSP 均匀探索", percent(live.pfsp.uniform_fraction), "其余概率优先较难对手，并保留最新历史模型覆盖", 12),
    ] : []),
  ];
}

export function pfspTable(live, f) {
  if (!live.pfsp?.history?.length) return "";
  const { integer, percent } = f;
  const rows = live.pfsp.history.map((entry) => `<tr><td>${snapshotLabel(entry, integer)}</td><td>${integer(entry.games)}</td><td>${percent(entry.score)}</td><td>${percent(entry.probability)}</td></tr>`).join("");
  const scripts = live.pfsp.separate_scripts ? `<div class="opponent-footnote">独立脚本池 · 占总对局 ${percent(live.target_script_fraction)}，不参与历史 PFSP 权重归一化。</div><div class="opponent-table-wrap"><table class="opponent-table"><thead><tr><th>脚本</th><th>学习方预估比分</th><th>池内抽样概率</th><th>总对局抽样概率</th></tr></thead><tbody>${Object.entries(live.pfsp.scripts || {}).map(([name, entry]) => `<tr><td>${opponentLabel(name)}</td><td>${percent(entry.score)}</td><td>${percent(entry.probability)}</td><td>${percent(entry.overall_probability)}</td></tr>`).join("")}</tbody></table></div>` : "";
  return `<div class="opponent-footnote">PFSP ${live.pfsp.unified ? "统一对手池" : "历史池"} · U${integer(live.pfsp.update)} 后的下一轮抽样概率。比分为衰减后的学习方胜 + 0.5 × 平；未交手快照从 50% 先验开始。</div><div class="opponent-table-wrap"><table class="opponent-table"><thead><tr><th>冻结对手</th><th>累计交手</th><th>预估比分</th><th>抽样概率</th></tr></thead><tbody>${rows}</tbody></table></div>${scripts}`;
}

export function renderLearningCharts(target, run, metrics, renderCharts) {
  if (!metrics?.series?.["rl/rollout/mean_terminal_cash"]?.length) {
    const pretraining = ["initializing", "demonstrations"].includes(run.learning?.phase);
    target.innerHTML = `<div class="panel-card empty-panel"><div><h3>${pretraining ? "示范预训练进行中" : "等待首个 PPO 指标提交"}</h3><p>${pretraining ? "分片进度与 NLL 见上方；固定预训练结束后自动进入在线 PPO。" : "完整更新保存后，训练曲线会自动显示。"}</p></div></div>`;
    return;
  }
  renderCharts(target, "rl", metrics, learningChartConfigurations(run, metrics));
}

export function learningChartConfigurations(run, metrics) {
  if (run.learning?.league) return leagueChartConfigurations(run, metrics);
  const colors = ["#22b99a", "#7d9fff", "#e0a72e", "#9f76dc"];
  const chart = (title, note, unit, lines) => ({
    title, note, unit,
    lines: lines.map(([tag, label], index) => [tag, label, colors[index % colors.length]]),
  });
  const charts = [
    ...quadrantCharts(metrics, chart),
    ...(run.learning?.pfsp?.enabled ? [
      chart(run.learning.pfsp.separate_scripts ? "脚本池抽样概率" : "PFSP 脚本分配概率", run.learning.pfsp.separate_scripts ? "独立脚本配额；池内按近期比分自适应抽样，与历史 PFSP 分开" : run.learning.pfsp.unified ? "与历史模型共享概率分布；每轮抽取一个完整对手批次" : "含最低席位覆盖；每轮按双方席位成对采样", "比例",
        (run.learning.pfsp.separate_scripts ? Object.keys(run.learning.pfsp.scripts || {}) : run.learning.pfsp.unified ? run.learning.pfsp.history.filter((entry) => entry.kind === "script").map((entry) => entry.name) : Object.keys(run.learning.population_games || {}).filter((name) => !["self_play", "historical_self_play"].includes(name)))
          .map((name) => [`rl/pfsp/scripts/${name}/probability`, opponentLabel(name)])),
    ] : []),
    ...scriptCharts(metrics, chart, run.learning?.pfsp?.unified || run.learning?.pfsp?.separate_scripts ? null : run.learning?.population_games),
    chart("终局现金", "训练采样中的双方现金均值", "现金", [
      ["rl/rollout/mean_terminal_cash", "平均现金"],
    ]),
    ...((run.learning?.history_fraction === 0 && !run.learning?.pfsp?.unified) || run.learning?.pure_selfplay ? [] : [chart("历史对手比分", "训练诊断；历史池变化，不等于固定对手评估", "比例", [
      ["rl/run/history_score", "比分"],
    ])]),
    chart("PPO 稳定性", "前缀条件 KL；更新后的 KL 仅计入已接受的优化步", "KL", [
      ["rl/optimization/maximum_prefix_kl", "更新前最大 KL"],
      ["rl/optimization/maximum_accepted_post_step_kl", "已接受更新后最大 KL"],
    ]),
    chart("价值损失", "Critic 训练目标", "损失", [
      ["rl/optimization/value_loss", "总价值损失"],
      ["rl/optimization/state_value_loss", "局面价值"],
      ["rl/optimization/prefix_value_loss", "前缀价值"],
    ]),
    chart("Actor 学习率", "优化器实际采用的学习率", "学习率", [
      ["rl/optimization/actor_learning_rate", "Actor"],
    ]),
    chart("Update 阶段耗时", "采样与优化；不含保存和评估", "秒", [
      ["rl/system/update_elapsed_seconds", "Update"],
      ["rl/rollout/elapsed_seconds", "采样"],
      ["rl/system/optimization_seconds", "优化"],
    ]),
    chart("物理比赛吞吐", "每场只计一次；Update 吞吐不含保存和评估", "games/s", [
      ["rl/system/physical_games_per_second", "Update"],
      ["rl/rollout/games_per_second", "采样"],
    ]),
    { ...chart("GPU 内存峰值", "本轮已分配显存", "bytes", [
      ["rl/system/cuda_peak_allocated_bytes", "已分配"],
    ]), bytes: true },
  ];
  return charts.map((config) => ({ ...config,
    overview: config.overview || config.title === "历史对手比分",
    group: config.group || (config.title.includes("脚本") ? "opponents"
      : ["Update 阶段耗时", "物理比赛吞吐", "GPU 内存峰值"].includes(config.title) ? "resources"
      : ["终局现金", "历史对手比分"].includes(config.title) ? "overview" : "diagnostics"),
    percent: config.unit === "比例",
  }));
}

export function scriptCharts(metrics, chart, populations = null) {
  const prefix = "rl/rollout/opponents/";
  const scripts = Object.keys(metrics?.series || {})
    .filter((tag) => tag.startsWith(prefix) && tag.endsWith("/games"))
    .map((tag) => tag.slice(prefix.length, -"/games".length))
    .filter((name) => !["self_play", "history"].includes(name))
    .filter((name) => populations === null || populations[name] > 0).sort();
  if (!scripts.length) return [];
  return [
    ["脚本对手胜率", "胜局 / 本轮对局；平局单列在上方表格", "比例", "win_rate"],
    ["对脚本终局现金", "学习方的本轮平均终局现金", "现金", "mean_terminal_cash"],
    ["对脚本现金差", "学习方减脚本对手；正值表示领先", "现金", "mean_cash_difference"],
  ].map(([title, note, unit, field]) => ({ ...chart(
    title, `${note}；属于训练采样统计`, unit,
    scripts.map((name) => [`${prefix}${name}/${field}`, opponentLabel(name)]),
  ), zero: field === "mean_cash_difference" }));
}
