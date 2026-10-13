const UI_VERSION = document.querySelector('meta[name="ui-version"]')?.content || "";
const chartsUrl = UI_VERSION
  ? `/assets/charts.js?v=${encodeURIComponent(UI_VERSION)}`
  : "/assets/charts.js";
const { renderCharts, productionKlMetrics } = await import(chartsUrl);
const { renderEvaluationHistory } = await import(`/assets/evaluation.js?v=${encodeURIComponent(UI_VERSION)}`);
const { searchCards, searchCharts, renderSearch, renderSearchEvaluation } = await import(`/assets/search.js?v=${encodeURIComponent(UI_VERSION)}`);
const { apprenticeCards, apprenticeCharts, renderApprentice } = await import(`/assets/apprentice.js?v=${encodeURIComponent(UI_VERSION)}`);
const { branchCards, branchCharts, renderBranch } = await import(`/assets/branching.js?v=${encodeURIComponent(UI_VERSION)}`);
const { learningCards, learningStage, opponentLabel, currentPopulationMetrics, pfspTable } = await import(`/assets/learning.js?v=${encodeURIComponent(UI_VERSION)}`);
const { activeMembers, leagueLabel, leaguePairTable, leaguePairs, renderLeagueEvaluation } = await import(`/assets/league.js?v=${encodeURIComponent(UI_VERSION)}`);
const { isLearningBC, bcCards, bcCharts, renderPretraining } = await import(`/assets/pretraining.js?v=${encodeURIComponent(UI_VERSION)}`);

const { createExplorer, readPreference, savePreference } = await import(`/assets/explorer.js?v=${encodeURIComponent(UI_VERSION)}`);
const { createOpponentExplorer } = await import(`/assets/opponents.js?v=${encodeURIComponent(UI_VERSION)}`);
const opponentExplorer = createOpponentExplorer({ fetchJson });
const explorer = createExplorer({ fetchJson, onContext: opponentExplorer.update });
const sidebarPreferences = readPreference("revue.monitor.sidebar.v1", {});
const MAX_OPPONENT_ROWS = 12;

const state = {
  overview: null,
  detail: null,
  selectedRun: null,
  filter: sidebarPreferences.filter || "all",
  query: sidebarPreferences.query || "",
  pinned: sidebarPreferences.pinned || [],
  historyOpen: sidebarPreferences.historyOpen || false,
  refreshSeconds: 5,
  timer: null,
  refreshing: false,
  requestVersion: 0,
};

const elements = {
  runList: document.querySelector("#run-list"),
  runCount: document.querySelector("#run-count"),
  runSearch: document.querySelector("#run-search"),
  filters: document.querySelector("#run-filters"),
  sidebarLive: document.querySelector("#sidebar-live"),
  sidebarSystem: document.querySelector("#sidebar-system"),
  crumbRun: document.querySelector("#crumb-run"),
  syncState: document.querySelector("#sync-state"),
  tensorboardLink: document.querySelector("#tensorboard-link"),
  refreshButton: document.querySelector("#refresh-button"),
  errorBanner: document.querySelector("#error-banner"),
  hero: document.querySelector("#hero-panel"),
  metricGrid: document.querySelector("#metric-grid"),
  opponentSection: document.querySelector("#opponent-section"),
  opponentPanel: document.querySelector("#opponent-panel"),
  chartGrid: document.querySelector("#chart-grid"),
  evidenceNote: document.querySelector("#evidence-note"),
  evaluationAsOf: document.querySelector("#evaluation-asof"),
  evaluation: document.querySelector("#evaluation-panel"),
  metricSource: document.querySelector("#metric-source"),
  latestMetrics: document.querySelector("#latest-metrics"),
  systemPanel: document.querySelector("#system-panel"),
  artifacts: document.querySelector("#artifact-list"),
  identity: document.querySelector("#identity-card"),
  footerUpdate: document.querySelector("#footer-update"),
  menuButton: document.querySelector("#menu-button"),
  sidebarClose: document.querySelector("#sidebar-close"),
  sidebarScrim: document.querySelector("#sidebar-scrim"),
};

const STATUS = {
  failed: ["训练失败", "失败"],
  running: ["训练中", "在线"],
  recent: ["持续更新", "活跃"],
  evaluated: ["已完成评估", "评估"],
  trained: ["训练已完成", "完成"],
  stopped: ["已停止 / 中断", "停止"],
};

const METRIC_NAMES = {
  accepted: "本代采纳",
  accepted_total: "累计采纳",
  candidates: "搜索候选",
  eligible: "搜索通过",
  finalists: "进入复核",
  generation_seconds: "整代耗时",
  selection_seconds: "新种子复核耗时",
  checkpoint_seconds: "保存检查点耗时",
  inference_seconds: "推理耗时",
  native_seconds: "Native 耗时",
  encoding_seconds: "编码耗时",
  collation_seconds: "整理耗时",
  proposal_seconds: "参数扰动耗时",
  physical_games: "物理比赛数",
  physical_games_per_second: "端到端比赛吞吐",
  peak_allocated_bytes: "Torch allocated 峰值",
  peak_reserved_bytes: "Torch reserved 峰值",
  cold_capture_seconds: "冷启动 CUDA Graph capture",
  wdl_gain: "配对 W−L 净改善",
  mean_cash: "平均终局现金",
  wins: "胜局",
  ties: "平局",
  losses: "负局",
  mean_cash_difference: "平均终局现金差",
  mean_terminal_cash: "平均终局现金",
  games_per_second: "对局吞吐",
  training_episodes_per_second: "训练视角吞吐",
  task_decisions_per_second: "Task AR 决策吞吐",
  turns_per_second: "Turn 吞吐",
  decisions_per_second: "决策吞吐",
  total_loss: "总损失",
  policy_loss: "策略损失",
  value_loss: "价值损失",
  state_value_loss: "局面价值损失",
  prefix_value_loss: "前缀价值损失",
  bc_retention_loss: "BC 保留损失",
  advantage_scale: "优势标准差",
  actor_steps: "Actor 更新步数",
  critic_steps: "Critic 更新步数",
  actor_early_stop: "Actor 因 KL 早停",
  critic_warmup: "Critic 预热",
  temperature: "实际采样温度",
  actor_learning_rate: "Actor 实际学习率",
  credit_seconds: "前缀信用计算耗时",
  value_remaining_cash_rmse: "剩余终局现金 RMSE",
  value_remaining_cash_mae: "剩余终局现金 MAE",
  value_cash_rmse: "终局现金 RMSE",
  value_cash_mae: "终局现金 MAE",
  value_nll: "价值 NLL",
  value_accuracy: "价值准确率",
  value_brier: "价值 Brier",
  root_value_loss: "根状态 W/D/L loss",
  candidate_value_loss: "候选 W/D/L loss",
  approximate_kl: "近似 KL",
  maximum_prefix_kl: "前缀条件最大 KL",
  maximum_plan_kl: "完整计划最大 KL",
  maximum_field_kl: "平均字段最大 KL",
  clip_fraction: "裁剪比例",
  entropy: "策略熵",
  gradient_norm: "梯度范数",
  maximum_gradient_norm: "最大梯度范数",
  task_policy_loss: "Task 策略损失",
  market_policy_loss: "Market 策略损失",
  task_value_loss: "Task 价值损失",
  market_value_loss: "Market 价值损失",
  task_entropy: "Task 熵",
  market_entropy: "Market 熵",
  maximum_task_kl: "Task 最大 KL",
  maximum_market_kl: "Market 最大 KL",
  task_factors: "Task PPO factors",
  market_factors: "Market PPO factors",
  task_decisions: "Task AR 决策数",
  training_episodes: "训练视角数",
  games: "物理比赛数",
  maximum_actor_seconds: "最大 Actor 耗时",
  remaining_overage_seconds: "剩余 Overage",
  optimization_seconds: "PPO 优化耗时",
  stopped_for_target_kl: "因目标 KL 早停",
  host_bytes: "Rollout 主存",
  maximum_minibatch_bytes: "最大 minibatch",
  peak_gpu_allocated_bytes: "GPU 峰值已分配",
  peak_gpu_reserved_bytes: "GPU 峰值已保留",
  selected_direct_fraction: "DIRECT 选择占比",
  selected_capability_fraction: "能力选择占比",
  behavior_exploration_epsilon: "行为探索混合",
  direct_turn_fraction: "DIRECT primitive turn 占比",
  action_accuracy: "动作准确率",
  quantity_accuracy: "数量准确率",
  unit_accuracy: "单位动作准确率",
  market_accuracy: "市场动作准确率",
  objective_nll: "目标 NLL",
  causal_objective_nll: "因果目标 NLL",
  action_nll: "动作 NLL",
  quantity_nll: "数量 NLL",
  elapsed_seconds: "耗时",
  update_elapsed_seconds: "Update 耗时",
  cuda_peak_allocated_bytes: "CUDA 峰值已分配",
  cuda_peak_reserved_bytes: "CUDA 峰值已保留",
};

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function finite(value) {
  return value !== null && value !== undefined && Number.isFinite(Number(value));
}

function number(value, digits = 2) {
  if (!finite(value)) return "—";
  const numeric = Number(value);
  const absolute = Math.abs(numeric);
  if (absolute >= 1e9) return `${(numeric / 1e9).toFixed(1)}B`;
  if (absolute >= 1e6) return `${(numeric / 1e6).toFixed(1)}M`;
  if (absolute >= 1e3) return `${(numeric / 1e3).toFixed(1)}k`;
  if (absolute > 0 && absolute < 0.001) return numeric.toExponential(2);
  return numeric.toLocaleString("zh-CN", { maximumFractionDigits: digits });
}

function integer(value) {
  return finite(value) ? Math.round(Number(value)).toLocaleString("zh-CN") : "—";
}

function percent(value, inputIsRatio = true) {
  if (!finite(value)) return "—";
  const numeric = Number(value) * (inputIsRatio ? 100 : 1);
  const digits = Math.abs(numeric) < 0.1 && numeric !== 0 ? 3 : Math.abs(numeric) < 10 ? 2 : 1;
  return `${numeric.toFixed(digits)}%`;
}

function bytes(value) {
  if (!finite(value)) return "—";
  const units = ["B", "KiB", "MiB", "GiB", "TiB"];
  let numeric = Math.abs(Number(value));
  let index = 0;
  while (numeric >= 1024 && index < units.length - 1) { numeric /= 1024; index += 1; }
  return `${Number(value) < 0 ? "−" : ""}${numeric.toFixed(numeric >= 100 ? 0 : numeric >= 10 ? 1 : 2)} ${units[index]}`;
}

function duration(value) {
  if (!finite(value)) return "—";
  let seconds = Math.max(0, Number(value));
  if (seconds < 60) return `${seconds.toFixed(seconds < 10 ? 1 : 0)} 秒`;
  if (seconds < 3600) return `${Math.floor(seconds / 60)} 分 ${Math.round(seconds % 60)} 秒`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)} 小时 ${Math.round(seconds % 3600 / 60)} 分`;
  const days = Math.floor(seconds / 86400);
  const hours = Math.round(seconds % 86400 / 3600);
  return `${days.toLocaleString("zh-CN")} 天 ${hours} 小时`;
}

function dateTime(value) {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.valueOf())) return "—";
  return new Intl.DateTimeFormat("zh-CN", {
    month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit", second: "2-digit", hour12: false,
  }).format(date);
}

function relativeTime(value) {
  if (!value) return "尚无数据";
  const seconds = Math.max(0, (Date.now() - new Date(value).valueOf()) / 1000);
  if (seconds < 10) return "刚刚";
  if (seconds < 60) return `${Math.floor(seconds)} 秒前`;
  if (seconds < 3600) return `${Math.floor(seconds / 60)} 分钟前`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)} 小时前`;
  return `${Math.floor(seconds / 86400)} 天前`;
}

function setLoading(loading) {
  elements.syncState.classList.toggle("loading", loading);
  elements.refreshButton.classList.toggle("loading", loading);
  if (loading) elements.syncState.innerHTML = "<i></i>正在同步";
}

function showError(message) {
  elements.errorBanner.textContent = message;
  elements.errorBanner.classList.remove("hidden");
  elements.syncState.className = "sync-state error";
  elements.syncState.innerHTML = "<i></i>同步异常";
}

function clearError() {
  elements.errorBanner.classList.add("hidden");
  elements.syncState.className = "sync-state";
}

async function fetchJson(path) {
  const response = await fetch(path, { cache: "no-store" });
  if (!response.ok) throw new Error(`${response.status} ${response.statusText}`);
  return response.json();
}

function saveSidebar() {
  savePreference("revue.monitor.sidebar.v1", { filter: state.filter, query: state.query, pinned: state.pinned, historyOpen: state.historyOpen });
}

function runMatches(run) {
  const query = state.query.trim().toLocaleLowerCase();
  if (query && !`${run.name} ${run.family}`.toLocaleLowerCase().includes(query)) return false;
  if (state.filter === "all") return true;
  if (state.filter === "live") return run.status === "running" || run.status === "recent";
  if (state.filter === "evaluated") return run.has_evaluation;
  return run.kind === state.filter;
}

function renderRunList() {
  const runs = (state.overview?.runs || []).filter(runMatches);
  elements.runCount.textContent = `${runs.length} / ${state.overview?.runs?.length || 0}`;
  elements.runList.innerHTML = "";
  if (!runs.length) {
    elements.runList.innerHTML = '<div class="run-empty">没有匹配的实验</div>';
    return;
  }
  const groups = [
    ["已置顶", runs.filter((run) => state.pinned.includes(run.id))],
    ["进行中", runs.filter((run) => !state.pinned.includes(run.id) && ["running", "recent"].includes(run.status))],
    ["历史运行", runs.filter((run) => !state.pinned.includes(run.id) && !["running", "recent"].includes(run.status))],
  ];
  groups.forEach(([label, grouped]) => {
    if (!grouped.length) return;
    const container = document.createElement(label === "历史运行" ? "details" : "div");
    if (label === "历史运行") {
      container.className = "run-history";
      container.open = state.historyOpen || Boolean(state.query) || state.filter !== "all" || grouped.some((run) => run.id === state.selectedRun);
      container.innerHTML = `<summary>${label} · ${grouped.length}</summary>`;
      container.addEventListener("toggle", () => { state.historyOpen = container.open; saveSidebar(); });
    } else container.innerHTML = `<div class="run-group-title">${label} · ${grouped.length}</div>`;
    elements.runList.appendChild(container);
    grouped.forEach((run) => {
      const button = document.createElement("button");
      const progress = run.progress || {};
      const step = finite(progress.current)
        ? `${run.kind === "search" ? "G" : run.kind === "bc" ? "E" : "U"}${integer(progress.current)}${finite(progress.target) ? ` / ${integer(progress.target)}` : ""}` : "—";
      button.className = `run-item${run.id === state.selectedRun ? " active" : ""}`;
      button.innerHTML = `
        <i class="run-state ${escapeHtml(run.status)}"></i>
        <span class="run-name"><strong title="${escapeHtml(run.name)}">${escapeHtml(run.name)}</strong><span>${escapeHtml(run.family)} · ${relativeTime(run.modified_at)}</span></span>
        <span class="run-step">${step}</span>`;
      button.addEventListener("click", () => selectRun(run.id));
      container.appendChild(button);
    });
  });
  document.querySelector("#pin-run").textContent = state.pinned.includes(state.selectedRun) ? "取消置顶" : "置顶运行";
}

function renderSidebarSystem() {
  const system = state.overview?.system || {};
  const gpus = system.gpus || [];
  const active = (system.training_processes || []).length;
  const updating = (state.overview?.runs || []).filter((run) => (
    run.status === "running" || run.status === "recent"
  )).length;
  const liveText = active
    ? `${active} 个 Revue 训练进程在线`
    : updating
      ? `${updating} 个 run 的指标持续更新`
      : "当前没有活跃训练指标";
  elements.sidebarLive.innerHTML = `<span class="live-pulse"></span><span>${liveText}</span>`;
  const gpuUtil = gpus.length ? Math.max(...gpus.map((gpu) => Number(gpu.utilization_percent || 0))) : 0;
  const memory = system.memory || {};
  const memoryUtil = Number(memory.utilization_percent || 0);
  elements.sidebarSystem.innerHTML = `
    <div class="sidebar-system-head"><span>本机资源</span><span class="muted-light">${gpus.length} GPU</span></div>
    <div class="resource-line"><span>GPU</span><div class="mini-track"><i style="width:${Math.min(100, gpuUtil)}%"></i></div><b>${Math.round(gpuUtil)}%</b></div>
    <div class="resource-line"><span>RAM</span><div class="mini-track"><i style="width:${Math.min(100, memoryUtil)}%"></i></div><b>${Math.round(memoryUtil)}%</b></div>`;
}

function renderOverview() {
  renderRunList();
  renderSidebarSystem();
}

function formatProgress(value) {
  if (!finite(value)) return "—";
  const numeric = Number(value);
  return `${numeric.toFixed(numeric < 0.01 && numeric > 0 ? 4 : numeric < 1 ? 2 : 1)}%`;
}

function runObjective(run, configuration) {
  if (configuration.training_family === "state_branch") return "Expert Iteration · 状态分支搜索 + 整网偏好学习 · argmax 执行";
  if (configuration.training_family === "expert_iteration") return "Expert Iteration · 搜索专家 + 整网梯度学习 · argmax 执行";
  if (run.kind === "search") return "参数空间策略搜索 · WDL 选择 · argmax 执行";
  if (run.kind === "bc") return "Behavior cloning";
  if (run.kind !== "rl") return "Experiment artifact";
  if (configuration.training_family === "unit_task_rl") {
    return "Unit-task tape terminal W/D/L PPO · current-policy self-play";
  }
  if (configuration.direct_capability) {
    return "Capability-space terminal W/D/L PPO";
  }
  if (configuration.optimization_target !== "terminal_cash") {
    return "Terminal W/D/L actor-critic";
  }
  if (configuration.value_target === "remaining_cash_from_pre_turn_balance") {
    return "终局现金 actor-critic · 价值头预测剩余终局现金";
  }
  return "终局现金 actor-critic";
}

function renderHero(run, configuration) {
  const progress = run.progress || {};
  const status = STATUS[run.status] || [run.status, run.status];
  const source = state.detail?.metrics?.sources?.join(" + ") || "artifact";
  const population = configuration.population === "script_mix"
    ? `${percent(configuration.script_fraction)} 脚本对手 + self-play`
    : "纯 self-play";
  const kind = isLearningBC(run) ? "Behavior Cloning · 固定监督预算" : run.family === "learning" ? learningStage(run) : configuration.training_family === "spatial-contract"
    ? `空间经营计划 PPO · ${population} · 终局现金与胜负目标`
    : runObjective(run, configuration);
  elements.crumbRun.textContent = run.name;
  elements.hero.innerHTML = `
    <div class="hero-grid"></div>
    <div class="hero-copy">
      <div class="hero-kicker"><span class="status-dot ${escapeHtml(run.status)}"></span><span>${escapeHtml(status[0])} · ${escapeHtml(run.family)}</span></div>
      <h1>${escapeHtml(run.name)}</h1>
      <p>${kind} · ${escapeHtml(source)} · 最后活动 ${relativeTime(run.modified_at)}</p>
    </div>
    <div class="hero-progress">
      <div class="hero-progress-top"><span>训练进度</span><strong>${formatProgress(progress.percent)}</strong></div>
      <div class="hero-progress-track"><i style="width:${Math.min(100, Number(progress.percent || 0))}%"></i></div>
      <div class="hero-progress-meta"><span>当前 ${integer(progress.current)}</span><span>目标 ${integer(progress.target)}</span></div>
    </div>`;
}

function evidenceNote(run, configuration) {
  if (isLearningBC(run)) return "每个 epoch 完整遍历训练集；逐轮验证使用 selection 集，confirmation 集保留至训练结束。条件动作准确率和 NLL 衡量教师动作拟合程度。";
  if (run.learning?.league) {
    const members = activeMembers(run).map(leagueLabel).join("、");
    const scripts = run.learning.script_opponents?.length || 0;
    return `${members} 各自完成 BC 后，进行互战与各模型自博弈${scripts ? `，并对战 ${scripts} 个固定脚本对手` : ""}。互战与脚本对战从名称左侧模型视角统计，自博弈胜平负按席位 0 统计。每场只计一次；训练采样与固定种子评估分别展示。`;
  }
  if (run.family === "learning") return `${configuration.initial_weights ? "从指定检查点权重开始" : "从随机参数开始，可先执行固定多来源示范初始化"}，按当前对手组成运行 PPO。对局占比按完整比赛计算；脚本胜平负与现金差从学习方视角统计。训练统计与下方固定种子评估分别展示。`;
  if (configuration.training_family === "state_branch") return "从学生访问的状态分叉，比较完整方案的终局 WDL，学习有证据的方案偏好。分支赢家仅作训练标签；模型面板为学生独立执行的比赛。";
  if (configuration.training_family === "expert_iteration") return "学生在自己访问的状态上学习搜索专家；KL 和动作一致率仅作拟合诊断。闭环面板分别报告学生、专家和原始 PPO，只有学生独立执行的结果能证明改进已被吸收。";
  if (run.kind === "search") return "图中胜负属于最终保留策略的新种子复核；复核参与选择，每代种子变化。配对净改善使用同代父模型作基线，现金仅作诊断。";
  if (configuration.training_family === "spatial-contract") {
    if (configuration.population === "script_mix") {
      return "按物理对局混合当前策略自对弈与原生脚本。仅学习当前策略的席位，每局等权；现金排除脚本席位，自对弈先平均双方。胜负中自对弈按 seat-0、脚本对局按学习方记账。下方独立评估使用分离种子。";
    }
    return "PPO 对局全部来自当前策略 self-play；现金统计双方，胜负按 seat-0 记账。独立 notebook 配对评估见下方。";
  }
  if (configuration.training_family === "unit_task_rl") {
    return "纯 self-play rollout 是训练诊断；双方视角严格成对，晋级仍需独立完整规则比赛";
  }
  if (run.kind === "rl" && configuration.optimization_target === "terminal_cash") {
    return "Actor 优化终局现金；remaining-cash 只作为 critic 基线。晋级仍只看完整官方规则配对比赛";
  }
  if (run.kind === "rl") {
    return "Rollout 为训练诊断；晋级只看下方完整官方规则配对比赛";
  }
  return "BC 拟合指标不具有晋级权限；下方闭环比赛是表现证据";
}

function metricCard(label, value, sub, index, className = "", extra = "") {
  const cardIndex = String(index).padStart(2, "0");
  return `<article class="metric-card"><div class="metric-label"><span>${escapeHtml(label)}</span><span class="metric-index">${cardIndex}</span></div><div class="metric-value ${className}">${value}</div><div class="metric-sub">${sub}</div>${extra}</article>`;
}

function wdlStrip(wins, ties, losses) {
  const total = Number(wins || 0) + Number(ties || 0) + Number(losses || 0);
  if (!total) return '<div class="wdl-strip"></div>';
  return `<div class="wdl-strip"><i class="win" style="width:${Number(wins || 0) / total * 100}%"></i><i class="tie" style="width:${Number(ties || 0) / total * 100}%"></i><i class="loss" style="width:${Number(losses || 0) / total * 100}%"></i></div>`;
}

function valueQualityCard(latest, totalLoss, index = 6) {
  const cashVariants = [
    {
      rmse: "rl/optimization/value_remaining_cash_rmse",
      mae: "rl/optimization/value_remaining_cash_mae",
      label: "剩余现金价值 RMSE",
    },
    {
      rmse: "rl/optimization/value_cash_rmse",
      mae: "rl/optimization/value_cash_mae",
      label: "终局现金价值 RMSE",
    },
  ];
  const cash = cashVariants.find((variant) => finite(latest[variant.rmse]));
  if (cash) {
    return metricCard(
      cash.label,
      number(latest[cash.rmse]),
      `MAE ${number(latest[cash.mae])} · loss ${number(totalLoss, 4)}`,
      index,
    );
  }
  const rootLoss = latest["rl/optimization/root_value_loss"];
  const candidateLoss = latest["rl/optimization/candidate_value_loss"];
  if (finite(rootLoss)) {
    return metricCard(
      "W/D/L 价值损失",
      number(rootLoss, 4),
      `候选 ${number(candidateLoss, 4)} · total ${number(totalLoss, 4)}`,
      index,
    );
  }
  const accuracy = latest["rl/optimization/value_accuracy"];
  const brier = latest["rl/optimization/value_brier"];
  if (finite(accuracy)) {
    return metricCard(
      "W/D/L 价值准确率",
      percent(accuracy),
      `Brier ${number(brier, 4)} · loss ${number(totalLoss, 4)}`,
      index,
    );
  }
  const nll = latest["rl/optimization/value_nll"];
  const valueLoss = latest["rl/optimization/value_loss"];
  if (finite(nll) || finite(valueLoss)) {
    return metricCard(
      "价值模型质量",
      number(finite(nll) ? nll : valueLoss, 4),
      `${finite(nll) ? "NLL" : "价值损失（W/D/L 为 NLL）"} · 越低越好 · 训练拟合诊断`,
      index,
    );
  }
  return metricCard(
    "价值模型质量",
    "—",
    "当前 run 尚无可识别的质量诊断",
    index,
  );
}

function isTaskTapeMetrics(latest) {
  return finite(latest["rl/optimization/task_value_loss"])
    || finite(latest["rl/rollout/task_decisions_per_second"]);
}

function isIntentLedgerMetrics(latest) {
  return finite(latest["rl/rollout/pseudo_steps_per_second"])
    || finite(latest["rl/rollout/pseudo_steps"]);
}

function intentLedgerMetricCards(run, latest, headline, progress) {
  const cash = headline.mean_cash_difference;
  const cashClass = finite(cash) ? Number(cash) > 0 ? "positive" : Number(cash) < 0 ? "negative" : "" : "";
  const updateSeconds = latest["rl/system/update_elapsed_seconds"];
  const rolloutSeconds = latest["rl/rollout/elapsed_seconds"];
  const optimizationSeconds = latest["rl/system/optimization_seconds"];
  return [
    metricCard("训练 Update", `${integer(progress.current)} <small>/ ${integer(progress.target)}</small>`, `预计剩余 ${duration(progress.eta_seconds)}`, 1),
    metricCard("Self-play 胜 · 平 · 负", `${integer(headline.wins)} · ${integer(headline.ties)} · ${integer(headline.losses)}`, `${integer(latest["rl/rollout/physical_games"] || latest["rl/rollout/games"])} 物理局 · ${integer(latest["rl/rollout/episodes"])} seat`, 2, "", wdlStrip(headline.wins, headline.ties, headline.losses)),
    metricCard("终局现金差", number(cash), `seat-0 终局现金 ${number(headline.mean_terminal_cash)}`, 3, cashClass),
    metricCard("Rollout 吞吐", `${number(latest["rl/rollout/games_per_second"])} <small>game/s</small>`, `${number(latest["rl/rollout/pseudo_steps_per_second"], 0)} pseudo-step/s · ${number(latest["rl/rollout/episodes_per_second"])} seat/s`, 4),
    metricCard("Update 耗时", duration(updateSeconds), `rollout ${duration(rolloutSeconds)} · PPO ${duration(optimizationSeconds)}`, 5),
    metricCard("PPO 稳定性", `${number(latest["rl/optimization/approximate_kl"], 5)} KL`, `clip ${percent(latest["rl/optimization/clip_fraction"])} · entropy ${number(latest["rl/optimization/entropy"], 4)}`, 6),
    metricCard("价值 / 策略损失", `${number(latest["rl/optimization/value_loss"], 4)} · ${number(latest["rl/optimization/policy_loss"], 4)}`, `总损失 ${number(headline.total_loss, 4)} · steps ${integer(latest["rl/optimization/optimizer_steps"])}`, 7),
    metricCard("行为重放误差", `${number(latest["rl/behavior_replay/log_probability_error"], 5)} logprob`, `value ${number(latest["rl/behavior_replay/value_error"], 5)} · 首轮 update 审计`, 8),
    metricCard("训练内存峰值", bytes(latest["rl/system/cuda_peak_reserved_bytes"]), `allocated ${bytes(latest["rl/system/cuda_peak_allocated_bytes"])} · 双卡聚合`, 9),
    valueQualityCard(latest, headline.total_loss, 10),
  ];
}

function taskTapeMetricCards(run, latest, headline, progress) {
  const cash = headline.mean_cash_difference;
  const cashClass = finite(cash) ? Number(cash) > 0 ? "positive" : Number(cash) < 0 ? "negative" : "" : "";
  const updateSeconds = latest["rl/system/update_elapsed_seconds"];
  const rolloutSeconds = latest["rl/rollout/elapsed_seconds"];
  const optimizationSeconds = latest["rl/system/optimization_seconds"];
  const taskKl = latest["rl/optimization/maximum_task_kl"];
  const marketKl = latest["rl/optimization/maximum_market_kl"];
  const stopped = Number(latest["rl/optimization/stopped_for_target_kl"] || 0) > 0;
  return [
    metricCard("训练 Update", `${integer(progress.current)} <small>/ ${integer(progress.target)}</small>`, `预计剩余 ${duration(progress.eta_seconds)}`, 1),
    metricCard("物理局 胜 · 平 · 负", `${integer(headline.wins)} · ${integer(headline.ties)} · ${integer(headline.losses)}`, `${integer(latest["rl/rollout/games"])} 场 · seat-0 记账面`, 2, "", wdlStrip(headline.wins, headline.ties, headline.losses)),
    metricCard("终局现金差", number(cash), `seat-0 终局现金 ${number(headline.mean_terminal_cash)}`, 3, cashClass),
    metricCard("训练视角吞吐", `${number(latest["rl/rollout/training_episodes_per_second"])} <small>trajectory/s</small>`, `物理比赛 ${number(latest["rl/rollout/games_per_second"])} match/s · ${integer(latest["rl/rollout/training_episodes"])} 视角`, 4),
    metricCard("Task AR 吞吐", `${number(latest["rl/rollout/task_decisions_per_second"], 0)} <small>decision/s</small>`, `${number(latest["rl/rollout/task_decisions"])} task decisions · ${number(latest["rl/rollout/market_factors"])} market factors`, 5),
    metricCard("Update 耗时", duration(updateSeconds), `rollout ${duration(rolloutSeconds)} · PPO ${duration(optimizationSeconds)}`, 6),
    metricCard("Task / Market KL", `${number(taskKl, 5)} · ${number(marketKl, 5)}`, stopped ? "本轮达到 target KL，已提前停止 PPO epoch" : "本轮未触发 target KL 早停", 7),
    metricCard("Task / Market 策略损失", `${number(latest["rl/optimization/task_policy_loss"], 4)} · ${number(latest["rl/optimization/market_policy_loss"], 4)}`, `总损失 ${number(headline.total_loss, 4)} · optimizer steps ${integer(latest["rl/optimization/optimizer_steps"])}`, 8),
    metricCard("Task / Market 价值损失", `${number(latest["rl/optimization/task_value_loss"], 4)} · ${number(latest["rl/optimization/market_value_loss"], 4)}`, `factor 数 ${integer(latest["rl/optimization/task_factors"])} · ${integer(latest["rl/optimization/market_factors"])}`, 9),
    metricCard("Task / Market 熵", `${number(latest["rl/optimization/task_entropy"], 4)} · ${number(latest["rl/optimization/market_entropy"], 4)}`, `梯度范数 ${number(latest["rl/optimization/maximum_gradient_norm"], 4)}`, 10),
    metricCard("官方时限余量", `${number(latest["rl/rollout/remaining_overage_seconds"])} <small>s</small>`, `最慢 actor batch ${number(latest["rl/rollout/maximum_actor_seconds"])} s · 预算 1s + 60s`, 11),
    metricCard("训练内存峰值", bytes(latest["rl/system/cuda_peak_reserved_bytes"]), `GPU allocated ${bytes(latest["rl/system/cuda_peak_allocated_bytes"])} · host ${bytes(latest["rl/rollout/host_bytes"])}`, 12),
  ];
}

function renderMetricCards(run, metrics) {
  elements.metricGrid.dataset.family = run.family;
  const latest = metrics?.latest || {};
  const headline = run.headline || {};
  const progress = run.progress || {};
  let cards;
  if (isLearningBC(run)) {
    cards = bcCards(state.detail, { metricCard, integer, number, duration });
  } else if (run.family === "learning") {
    cards = learningCards(run, latest, { metricCard, integer, number, duration, bytes, percent });
  } else if (run.kind === "search") {
    cards = searchCards(run, metrics, { metricCard, integer, duration, number, wdlStrip });
  } else if (run.kind === "rl") {
    if (latest["rl/run/state_branch"]) {
      cards = branchCards(run, metrics, { metricCard, integer, duration, number, percent, wdlStrip });
    } else if (latest["rl/run/expert_iteration"]) {
      cards = apprenticeCards(run, metrics, { metricCard, integer, duration, number, percent, wdlStrip });
    } else if (finite(latest["rl/system/physical_games_per_second"])) {
      const klMetric = productionKlMetrics(latest)[0];
      const stopped = latest["rl/optimization/actor_early_stop"];
      const warmup = latest["rl/optimization/critic_warmup"];
      const updateState = warmup > 0 ? "Critic 预热" : stopped > 0 ? "已触发 KL 早停"
        : finite(stopped) ? "未触发 KL 早停" : "未记录早停状态";
      cards = [
        metricCard("训练 Update", `${integer(progress.current)} <small>/ ${integer(progress.target)}</small>`, `预计剩余 ${duration(progress.eta_seconds)}`, 1),
        metricCard("端到端吞吐", `${number(latest["rl/system/physical_games_per_second"])} <small>games/s</small>`, "包含 rollout、学习、同步和 checkpoint", 2),
        metricCard("终局现金", number(headline.mean_terminal_cash), `学习方统计 · P10 ${number(latest["rl/rollout/p10_terminal_cash"])}`, 3),
        metricCard("物理对局", integer(latest["rl/rollout/physical_games"]), `${integer(latest["rl/rollout/training_trajectories"])} 条策略轨迹 · 脚本 ${integer(latest["rl/rollout/script_games"] || 0)} 场`, 4),
        metricCard("Update 耗时", duration(latest["rl/system/update_elapsed_seconds"]), `rollout ${duration(latest["rl/rollout/elapsed_seconds"])} · PPO ${duration(latest["rl/system/optimization_seconds"])}`, 5),
        metricCard("PPO 稳定性", `${number(latest[klMetric?.tag], 6)} KL`, `${klMetric?.label || "等待 KL 标量"} · ${updateState}`, 6),
        metricCard("实际采样温度", `${number(latest["rl/run/temperature"], 6)} <small>T</small>`, `Actor 学习率 ${number(latest["rl/optimization/actor_learning_rate"], 6)}`, 7),
        metricCard("Actor / Critic 步数", `${integer(latest["rl/optimization/actor_steps"])} · ${integer(latest["rl/optimization/critic_steps"])}`, `本轮实际更新 · ${updateState}`, 8),
        metricCard("局面 / 前缀价值损失", `${number(latest["rl/optimization/state_value_loss"], 4)} · ${number(latest["rl/optimization/prefix_value_loss"], 4)}`, `Critic 总损失 ${number(latest["rl/optimization/value_loss"], 4)} · 优势标准差 ${number(latest["rl/optimization/advantage_scale"], 4)}`, 9),
        metricCard("GPU 内存峰值", bytes(latest["rl/system/cuda_peak_reserved_bytes"]), `最忙设备 · allocated ${bytes(latest["rl/system/cuda_peak_allocated_bytes"])}`, 10),
      ];
    } else if (isTaskTapeMetrics(latest)) {
      cards = taskTapeMetricCards(run, latest, headline, progress);
    } else if (isIntentLedgerMetrics(latest)) {
      cards = intentLedgerMetricCards(run, latest, headline, progress);
    } else {
      const cash = headline.mean_cash_difference;
      const cashClass = finite(cash) ? Number(cash) > 0 ? "positive" : Number(cash) < 0 ? "negative" : "" : "";
      cards = [
        metricCard("训练步", `${integer(progress.current)} <small>/ ${integer(progress.target)}</small>`, `预计剩余 ${duration(progress.eta_seconds)}`, 1),
        metricCard("Rollout 胜 · 平 · 负", `${integer(headline.wins)} · ${integer(headline.ties)} · ${integer(headline.losses)}`, `训练面板胜率 ${percent(headline.win_rate)}`, 2, "", wdlStrip(headline.wins, headline.ties, headline.losses)),
        metricCard("平均终局现金差", number(cash), "相对对手的终局差额", 3, cashClass),
        metricCard("平均终局现金", number(headline.mean_terminal_cash), "候选模型的 terminal cash", 4),
        metricCard("Rollout 吞吐", `${number(headline.games_per_second)} <small>games/s</small>`, `${number(headline.turns_per_second, 0)} turn/s`, 5),
        valueQualityCard(latest, headline.total_loss),
      ];
    }
  } else if (run.kind === "bc") {
    cards = [
      metricCard("训练轮次", `${integer(progress.current)} <small>/ ${integer(progress.target)}</small>`, `预计剩余 ${duration(progress.eta_seconds)}`, 1),
      metricCard("验证目标 NLL", number(headline.validation_objective_nll, 4), `训练 ${number(headline.training_objective_nll, 4)}`, 2),
      metricCard("验证动作准确率", percent(headline.validation_action_accuracy), `数量准确率 ${percent(headline.validation_quantity_accuracy)}`, 3),
      metricCard("训练吞吐", `${number(headline.turns_per_second, 0)} <small>turn/s</small>`, `最近 epoch ${duration(progress.mean_step_seconds)}`, 4),
      metricCard("验证 Unit / Market", `${percent(latest["bc/validation/unit_accuracy"])} · ${percent(latest["bc/validation/market_accuracy"])}`, "按动作域拆分", 5),
    ];
  } else {
    cards = [
      metricCard("记录步数", integer(progress.current), "可用的最新标量 step", 1),
      metricCard("标量数量", integer(metrics?.scalar_count), "TensorBoard 与 JSONL 合并", 2),
      metricCard("最后活动", relativeTime(run.modified_at), dateTime(run.modified_at), 3),
      metricCard("评估报告", run.has_evaluation ? "已就绪" : "暂无", "完整比赛证据", 4),
    ];
  }
  elements.metricGrid.innerHTML = cards.join("");
}

function pathLabel(path) {
  const translations = {
    selection: "选择集", confirmation: "确认集", population: "对手群体", head_to_head: "正面对局",
    challenger: "挑战者", incumbent: "现任", turn_policy: "候选策略", deterministic_incumbent: "确定性基线",
    paired_outcome_comparison: "配对结果比较", matchups: "逐对手",
  };
  return (path || []).map((part) => translations[part] || part).join(" · ") || "总体";
}

function evidencePills(evaluation) {
  const pills = [];
  const completion = evaluation.completion || {};
  const execution = evaluation.execution || {};
  if ("timeout_enforced" in execution) pills.push([execution.timeout_enforced, "时限已执行", "时限未执行"]);
  if ("all_matches_valid" in execution) pills.push([execution.all_matches_valid, "比赛均有效", "存在无效比赛"]);
  if ("all_done" in completion) pills.push([completion.all_done, "比赛均完成", "存在未完成比赛"]);
  if ("all_transition_counts_match" in completion) pills.push([completion.all_transition_counts_match, "步数完整", "步数不完整"]);
  return pills.map(([good, yes, no]) => `<span class="evidence-pill ${good ? "good" : "bad"}">${good ? yes : no}</span>`).join("");
}

function decisionView(evaluation) {
  const decision = evaluation.decision || {};
  const status = String(decision.status || "review");
  const eligible = decision.promotion_eligible === true;
  let title = "需要人工审阅";
  if (status === "retain_incumbent") title = "保留现任模型";
  if (status === "reject_promotion") title = "不晋级候选模型";
  if (status === "eligible_for_manual_promotion") title = "可进入人工晋级审阅";
  const reasons = Array.isArray(decision.reasons) && decision.reasons.length
    ? decision.reasons.join(" · ") : "评估报告已生成，未自动修改 incumbent";
  return { title, reasons, eligible };
}

function renderEvaluation(evaluation, history, runId) {
  const leaguePoints = history?.points?.filter((point) => point.pairs) || [];
  if (leaguePoints.length) {
    elements.evaluationAsOf.textContent = `最新评估 U${integer(leaguePoints.at(-1).step)}`;
    renderLeagueEvaluation(elements.evaluation, leaguePoints, { escapeHtml, integer, number, percent });
    return;
  }
  const hasHistory = Boolean(history?.points?.length);
  if (!evaluation && !hasHistory) {
    elements.evaluationAsOf.textContent = "尚无完整比赛评估";
    elements.evaluation.className = "evaluation-panel empty-panel";
    elements.evaluation.innerHTML = '<div class="empty-orbit" aria-hidden="true"><i></i></div><div><h3>等待完整比赛评估</h3><p>训练曲线会先显示；正式表现以官方规则下的配对比赛结果为准。</p></div>';
    return;
  }
  evaluation ||= {};
  const reportTime = evaluation.generated_at || (history?.modified_timestamp ? history.modified_timestamp * 1000 : null);
  elements.evaluationAsOf.textContent = `报告时间 ${dateTime(reportTime)}`;
  const decision = decisionView(evaluation);
  const rows = evaluation.wdl_rows || [];
  const tableRows = rows.map((row) => `<tr>
    <td title="${escapeHtml(pathLabel(row.path))}">${escapeHtml(pathLabel(row.path))}</td>
    <td class="w">${integer(row.wins)}</td><td>${integer(row.ties)}</td><td class="l">${integer(row.losses)}</td>
    <td>${number(row.mean_terminal_cash)}</td><td>${number(row.mean_cash_difference)}</td>
  </tr>`).join("");
  elements.evaluation.className = "evaluation-panel";
  const historyPanel = elements.evaluation.querySelector(".evaluation-history") || document.createElement("div");
  const reportOpen = historyPanel.dataset.runId === runId && elements.evaluation.querySelector(".evaluation-report")?.open;
  const reportTable = `<div class="wdl-table-wrap"><table class="wdl-table"><thead><tr><th>完整比赛面板</th><th>胜</th><th>平</th><th>负</th><th>终局现金</th><th>现金差</th></tr></thead><tbody>${tableRows || '<tr><td colspan="6">报告中没有 W/D/L 汇总</td></tr>'}</tbody></table></div>`;
  elements.evaluation.innerHTML = `
    <div class="evaluation-head">
      <div class="decision"><div class="decision-icon ${decision.eligible ? "" : "retain"}">${decision.eligible ? "✓" : "↺"}</div><div><strong>${escapeHtml(decision.title)}</strong><span>${escapeHtml(decision.reasons)}</span></div></div>
      <div class="evidence-pills">${evidencePills(evaluation)}</div>
    </div>
    ${hasHistory ? "" : reportTable}`;
  if (hasHistory) {
    elements.evaluation.appendChild(historyPanel);
    renderEvaluationHistory(historyPanel, history, runId, { escapeHtml, integer, number, percent, renderCharts });
    if (rows.length) elements.evaluation.insertAdjacentHTML("beforeend", `<details class="evaluation-report"${reportOpen ? " open" : ""}><summary>最新完整评估报告</summary>${reportTable}</details>`);
  }
}

function renderOpponentStats(metrics, kind, live = {}) {
  if (live.league) {
    const pairs = leaguePairs(metrics?.latest, live.members ? Object.keys(live.members) : null);
    elements.opponentSection.classList.toggle("hidden", !Object.keys(pairs).length);
    elements.opponentSection.querySelector(".evidence-note").textContent = `最近提交 U${integer(metrics?.last_step)}；互战按左侧模型，自博弈按席位 0 统计；每场只计一次`;
    elements.opponentPanel.innerHTML = leaguePairTable(pairs, { escapeHtml, integer, number, percent });
    return;
  }
  const pureSelfplay = live.pure_selfplay === true;
  const latest = currentPopulationMetrics(metrics?.latest, live, metrics?.last_step);
  const prefix = "rl/rollout/opponents/";
  const opponents = {};
  if (kind === "rl") {
    Object.entries(latest).forEach(([tag, value]) => {
      if (!tag.startsWith(prefix)) return;
      const path = tag.slice(prefix.length).split("/");
      if (path.length !== 2) return;
      const [opponent, field] = path;
      if (pureSelfplay && opponent !== "self_play") return;
      if (!live.pfsp?.enabled && live.population_games && !(live.population_games[opponent === "history" ? "historical_self_play" : opponent] > 0)) return;
      opponents[opponent] ||= {};
      opponents[opponent][field] = value;
    });
  }
  const rows = Object.entries(opponents).sort(([left, leftValues], [right, rightValues]) => {
    if (left === "self_play") return -1;
    if (right === "self_play") return 1;
    if (left === "history") return -1;
    if (right === "history") return 1;
    const fractionDifference = Number(rightValues.training_fraction || 0) - Number(leftValues.training_fraction || 0);
    return fractionDifference || left.localeCompare(right);
  });
  const poolHtml = pfspTable(live, { integer, percent });
  const poolTable = poolHtml ? `<div class="legacy-pfsp">${poolHtml}</div>` : "";
  elements.opponentSection.classList.toggle("hidden", !rows.length && !poolTable);
  if (!rows.length) {
    elements.opponentPanel.innerHTML = poolTable;
    if (poolTable) {
      elements.opponentSection.querySelector(".evidence-note").textContent = "当前阶段的胜平负将在完整保存后刷新；以下为对手池的实时统计和抽样概率";
    }
    return;
  }
  const visibleRows = rows.slice(0, MAX_OPPONENT_ROWS);
  const body = visibleRows.map(([opponent, values]) => {
    const cash = Number(values.mean_cash_difference);
    const cashClass = Number.isFinite(cash) ? cash > 0 ? "w" : cash < 0 ? "l" : "" : "";
    const label = opponent === "self_play"
      ? "self_play · 双视角"
      : opponent === "history"
        ? finite(values.opponent_update) ? `history · u${integer(values.opponent_update)}` : "history · 本轮历史快照"
        : opponentLabel(opponent);
    return `<tr>
      <td title="${escapeHtml(opponent)}">${escapeHtml(label)}</td>
      <td>${percent(values.training_fraction)}</td>
      <td>${integer(values.training_trajectories)}</td>
      <td>${integer(values.games)}</td>
      <td><span class="w">${integer(values.wins)}</span> · ${integer(values.ties)} · <span class="l">${integer(values.losses)}</span></td>
      <td>${percent(values.win_rate)}</td>
      <td>${number(values.mean_terminal_cash)}</td>
      <td class="${cashClass}">${number(values.mean_cash_difference)}</td>
    </tr>`;
  }).join("");
  const omitted = rows.length - visibleRows.length;
  const mixture = metrics?.latest?.["rl/run/script_mix"] === 1;
  elements.opponentSection.querySelector(".evidence-note").textContent =
    `最近已保存轮次 u${integer(metrics?.last_step)}；${pureSelfplay ? "当前仅训练模型双方自博弈；此前对手曲线保留在历史记录中" : mixture ? "占比按物理对局计算" : "训练占比按保留轨迹计算"}`;
  elements.opponentPanel.innerHTML = `<div class="opponent-table-wrap"><table class="opponent-table">
    <thead><tr><th>对手</th><th>${mixture ? "对局占比" : "训练占比"}</th><th>Trajectory</th><th>比赛</th><th>胜 · 平 · 负</th><th>胜率</th><th>终局现金</th><th>现金差</th></tr></thead>
    <tbody>${body}</tbody></table></div>
    <div class="opponent-footnote">${mixture ? "脚本与历史对局的胜平负、现金及现金差均从学习方视角统计，胜率为胜局 / 对局数。self-play 保留双方轨迹，胜平负按席位 0 统计，现金取双方均值。训练按每局等权归一化；这些是训练采样统计。" : "history 是本轮选中历史快照的稳定统计维度，并非一个固定对手；self-play 一局保留两个训练视角。"}${omitted ? ` 当前仅展示前 ${MAX_OPPONENT_ROWS} 个对手，另有 ${omitted} 个。` : ""}</div>${poolTable}`;
}

function metricPriority(kind, latest) {
  if (kind === "search") return Object.keys(latest).filter((tag) => (
    tag.startsWith("search/timing/") || tag.startsWith("search/ranks/") || tag.startsWith("search/rank_")
  ));
  if (kind === "rl" && finite(latest["rl/system/physical_games_per_second"])) return [
    ...productionKlMetrics(latest).map((metric) => metric.tag),
    "rl/run/temperature", "rl/optimization/actor_learning_rate",
    "rl/optimization/actor_early_stop", "rl/optimization/critic_warmup",
    "rl/optimization/actor_steps", "rl/optimization/critic_steps",
    "rl/optimization/state_value_loss", "rl/optimization/prefix_value_loss",
    "rl/optimization/value_loss", "rl/optimization/bc_retention_loss",
    "rl/optimization/advantage_scale", "rl/system/physical_games_per_second",
    "rl/system/update_elapsed_seconds", "rl/rollout/elapsed_seconds",
    "rl/system/optimization_seconds", "rl/rollout/mean_terminal_cash",
  ];
  if (kind === "rl" && isTaskTapeMetrics(latest)) return [
    "rl/rollout/games", "rl/rollout/training_episodes", "rl/rollout/wins", "rl/rollout/ties",
    "rl/rollout/losses", "rl/rollout/win_rate", "rl/rollout/mean_cash_difference",
    "rl/rollout/mean_terminal_cash", "rl/rollout/games_per_second",
    "rl/rollout/training_episodes_per_second", "rl/rollout/task_decisions_per_second",
    "rl/rollout/task_decisions", "rl/rollout/market_factors", "rl/rollout/maximum_actor_seconds",
    "rl/rollout/remaining_overage_seconds", "rl/system/update_elapsed_seconds",
    "rl/rollout/elapsed_seconds", "rl/system/optimization_seconds",
    "rl/optimization/task_policy_loss", "rl/optimization/market_policy_loss",
    "rl/optimization/task_value_loss", "rl/optimization/market_value_loss",
    "rl/optimization/maximum_task_kl", "rl/optimization/maximum_market_kl",
    "rl/optimization/task_entropy", "rl/optimization/market_entropy",
    "rl/optimization/maximum_gradient_norm", "rl/optimization/stopped_for_target_kl",
    "rl/optimization/task_factors", "rl/optimization/market_factors",
    "rl/optimization/optimizer_steps", "rl/optimization/total_loss",
    "rl/system/cuda_peak_allocated_bytes", "rl/system/cuda_peak_reserved_bytes",
    "rl/rollout/host_bytes", "rl/rollout/maximum_minibatch_bytes",
  ];
  if (kind === "rl") return [
    "rl/rollout/wins", "rl/rollout/ties", "rl/rollout/losses", "rl/rollout/mean_cash_difference",
    "rl/rollout/mean_terminal_cash", "rl/rollout/games_per_second", "rl/rollout/turns_per_second", "rl/optimization/value_remaining_cash_rmse",
    "rl/optimization/value_remaining_cash_mae", "rl/optimization/value_cash_rmse",
    "rl/optimization/value_cash_mae", "rl/optimization/value_accuracy", "rl/optimization/value_brier",
    "rl/optimization/root_value_loss", "rl/optimization/candidate_value_loss",
    "rl/optimization/value_loss", "rl/optimization/value_nll", "rl/optimization/policy_loss",
    "rl/optimization/approximate_kl", "rl/optimization/clip_fraction", "rl/optimization/entropy",
    "rl/optimization/maximum_gradient_norm", "rl/system/update_elapsed_seconds",
    "rl/search/selected_direct_fraction", "rl/search/selected_capability_fraction",
    "rl/search/behavior_exploration_epsilon", "rl/rollout/direct_turn_fraction",
    "rl/system/cuda_peak_allocated_bytes", "rl/system/cuda_peak_reserved_bytes",
  ];
  return [
    "bc/training/causal_objective_nll", "bc/validation/causal_objective_nll", "bc/training/objective_nll",
    "bc/validation/objective_nll", "bc/training/action_nll", "bc/validation/action_nll",
    "bc/training/action_accuracy", "bc/validation/action_accuracy", "bc/validation/quantity_accuracy",
    "bc/validation/unit_accuracy", "bc/validation/market_accuracy", "bc/training/turns_per_second",
    "bc/validation/turns_per_second", "bc/system/elapsed_seconds", "bc/system/cuda_peak_allocated_bytes",
    "bc/system/cuda_peak_reserved_bytes",
  ];
}

function metricValue(tag, value) {
  if (tag.endsWith("_bytes")) return bytes(value);
  if (tag.endsWith("learning_rate")) return number(value, 6);
  if (/(accuracy|fraction|rate|win_probability)$/.test(tag)) return percent(value);
  if (tag.endsWith("_seconds")) return `${number(value)} s`;
  if (tag.endsWith("_per_second")) return `${number(value)} /s`;
  return number(value, 5);
}

function renderLatest(metrics, kind) {
  const latest = metrics?.latest || {};
  const priority = metricPriority(kind, latest);
  const tags = [
    ...priority.filter((tag) => tag in latest),
    ...Object.keys(latest)
      .filter((tag) => !priority.includes(tag) && !tag.startsWith("rl/rollout/opponents/"))
      .sort(),
  ];
  elements.metricSource.textContent = metrics?.sources?.join(" + ") || "—";
  if (!tags.length) {
    elements.latestMetrics.innerHTML = '<div class="run-empty">暂无标量</div>';
    return;
  }
  elements.latestMetrics.innerHTML = `<table class="latest-table"><thead><tr><th>指标</th><th>最新值</th></tr></thead><tbody>${tags.map((tag) => {
    const leaf = tag.split("/").at(-1);
    const group = tag.split("/").slice(0, -1).join(" / ");
    return `<tr><td title="${escapeHtml(tag)}">${escapeHtml(METRIC_NAMES[leaf] || leaf.replaceAll("_", " "))}<small> · ${escapeHtml(group)}</small></td><td>${metricValue(tag, latest[tag])}</td></tr>`;
  }).join("")}</tbody></table>`;
}

function gauge(label, value, text, color = "") {
  const amount = finite(value) ? Math.max(0, Math.min(100, Number(value))) : 0;
  return `<div class="gauge-row"><span>${escapeHtml(label)}</span><div class="gauge-track"><i style="width:${amount}%;${color ? `background:${color}` : ""}"></i></div><strong>${escapeHtml(text)}</strong></div>`;
}

function renderSystem(system, processes) {
  const cpu = system?.cpu || {};
  const memory = system?.memory || {};
  const disk = system?.disk || {};
  const gpus = system?.gpus || [];
  const gpuCards = gpus.map((gpu) => {
    const memoryPercent = finite(gpu.memory_used_bytes) && finite(gpu.memory_total_bytes) && Number(gpu.memory_total_bytes) > 0
      ? Number(gpu.memory_used_bytes) / Number(gpu.memory_total_bytes) * 100 : 0;
    return `<div class="gpu-card"><div class="gpu-head"><strong>GPU ${integer(gpu.index)} · ${escapeHtml(gpu.name)}</strong><span>${number(gpu.temperature_celsius, 0)}°C</span></div>
      ${gauge("利用率", gpu.utilization_percent, percent(gpu.utilization_percent, false))}
      ${gauge("显存", memoryPercent, `${bytes(gpu.memory_used_bytes)} / ${bytes(gpu.memory_total_bytes)}`, "#7d9fff")}
      ${gauge("功耗", finite(gpu.power_watts) && finite(gpu.power_limit_watts) ? Number(gpu.power_watts) / Number(gpu.power_limit_watts) * 100 : 0, `${number(gpu.power_watts, 0)} W`, "#e0a72e")}</div>`;
  }).join("");
  const process = processes?.[0];
  const processCard = process ? `<div class="process-card"><div class="process-title"><span>绑定训练进程树 · ${integer(process.process_count)} processes</span><b>PID ${integer(process.pid)}</b></div><div class="process-grid">
    <div><span>状态</span><strong>${escapeHtml(process.status)}</strong></div><div><span>CPU</span><strong>${percent(process.cpu_percent, false)}</strong></div>
    <div><span>RAM</span><strong>${bytes(process.memory_bytes)}</strong></div><div><span>GPU 显存</span><strong>${bytes(process.gpu_memory_bytes)}</strong></div>
    <div><span>已运行</span><strong>${duration(process.elapsed_seconds)}</strong></div></div></div>` : '<div class="process-card"><div class="process-title"><span>绑定训练进程</span><b>未检测到</b></div></div>';
  elements.systemPanel.innerHTML = `<div class="system-summary">
      <div class="system-stat"><span>CPU</span><strong>${percent(cpu.utilization_percent, false)}</strong></div>
      <div class="system-stat"><span>RAM</span><strong>${percent(memory.utilization_percent, false)}</strong></div>
      <div class="system-stat"><span>Output disk</span><strong>${percent(disk.utilization_percent, false)}</strong></div>
    </div>${gpuCards || '<div class="run-empty">未发现 NVIDIA GPU</div>'}${processCard}`;
}

function artifactIcon(kind, path) {
  if (kind === "model") return "PT";
  if (kind === "checkpoint") return "CK";
  if (path.endsWith(".jsonl")) return "JL";
  return "JS";
}

function renderArtifacts(detail) {
  const artifacts = detail.artifacts || {};
  const files = artifacts.files || [];
  elements.artifacts.innerHTML = files.length ? files.map((file) => `<div class="artifact-row">
    <div class="artifact-icon ${escapeHtml(file.kind)}">${artifactIcon(file.kind, file.path)}</div>
    <div class="artifact-name"><strong title="${escapeHtml(file.path)}">${escapeHtml(file.path)}</strong><span>${escapeHtml(file.kind)} · ${dateTime(file.modified_at)}</span></div>
    <div class="artifact-size">${bytes(file.size_bytes)}</div></div>`).join("") : '<div class="run-empty">暂无可展示产物</div>';

  const source = detail.source || {};
  const config = detail.configuration || {};
  const configRows = Object.entries(config).slice(0, 12).map(([key, value]) => `<div class="identity-row"><span>${escapeHtml(key)}</span><strong>${escapeHtml(Array.isArray(value) ? value.join(", ") : value)}</strong></div>`).join("");
  const dirty = source.worktree_dirty;
  elements.identity.innerHTML = `<div class="identity-title">Source revision</div><div class="commit-hash">${escapeHtml(source.commit ? String(source.commit).slice(0, 12) : "unavailable")}</div>
    <div class="identity-row"><span>工作树</span><strong class="${dirty === false ? "clean" : dirty === true ? "dirty" : ""}">${dirty === false ? "clean" : dirty === true ? "dirty" : "unknown"}</strong></div>
    <div class="identity-row"><span>Checkpoint 数</span><strong>${integer(artifacts.checkpoint_count)}</strong></div>${configRows}`;
}

function renderDetail(refreshMetrics = true) {
  const detail = state.detail;
  if (!detail) return;
  const run = detail.run;
  renderPretraining(detail, { integer, number, duration, percent, escapeHtml });
  renderHero(run, detail.configuration || {});
  const searchFormat = { escapeHtml, integer, number, duration };
  renderSearch(detail, searchFormat);
  const apprentice = detail.configuration?.training_family === "expert_iteration";
  const branching = detail.configuration?.training_family === "state_branch";
  if (branching) renderBranch(detail, searchFormat);
  else if (apprentice) renderApprentice(detail, searchFormat);
  else document.querySelector("#search-section h2").textContent = "搜索进度与策略采纳";
  if (refreshMetrics) {
    renderMetricCards(run, detail.metrics);
    renderOpponentStats(detail.metrics, run.kind, run.learning);
    if (isLearningBC(run)) renderCharts(elements.chartGrid, "bc", detail.metrics, bcCharts());
    else if (run.family !== "learning") renderCharts(elements.chartGrid, run.kind, detail.metrics, branching ? branchCharts() : apprentice ? apprenticeCharts() : run.kind === "search" ? searchCharts(detail.metrics) : null);
    if (run.kind === "search") renderSearchEvaluation(detail, searchFormat);
    else if (!isLearningBC(run)) renderEvaluation(detail.evaluation, detail.evaluation_history, run.id);
    renderLatest(detail.metrics, run.kind);
    renderArtifacts(detail);
  }
  elements.evidenceNote.textContent = evidenceNote(run, detail.configuration || {});
  renderSystem(state.overview?.system || {}, detail.processes || []);
  const tensorboard = detail.tensorboard || {};
  const showTensorboard = tensorboard.available && tensorboard.url
    && (run.status === "running" || run.status === "recent");
  elements.tensorboardLink.classList.toggle("hidden", !showTensorboard);
  if (showTensorboard) elements.tensorboardLink.href = tensorboard.url;
  elements.footerUpdate.textContent = `同步于 ${dateTime(state.overview?.generated_at)}`;
  explorer.update(detail, state.overview?.display_defaults);
}

async function loadDetail(runId, version) {
  const encoded = runId.split("/").map(encodeURIComponent).join("/");
  const previous = state.detail?.run?.id === runId ? state.detail : null;
  const modified = previous?.run?.modified_timestamp;
  const query = finite(modified) ? `?after_modified=${encodeURIComponent(modified)}` : "";
  const detail = await fetchJson(`/api/runs/${encoded}${query}`);
  if (version !== state.requestVersion || runId !== state.selectedRun) return;
  if (detail.unchanged === true && previous) {
    state.detail = {
      ...previous,
      run: detail.run || previous.run,
      processes: detail.processes || [],
    };
    renderDetail(false);
  } else {
    state.detail = detail;
    renderDetail();
  }
}

async function selectRun(runId) {
  if (!runId) return;
  const url = new URL(window.location.href);
  url.searchParams.set("run", runId);
  window.history.replaceState(null, "", url);
  state.selectedRun = runId;
  state.detail = null;
  state.requestVersion += 1;
  const version = state.requestVersion;
  renderRunList();
  document.body.classList.remove("sidebar-open");
  setLoading(true);
  try {
    await loadDetail(runId, version);
    clearError();
  } catch (error) {
    if (version === state.requestVersion) showError(`无法读取 run：${error.message}`);
  } finally {
    setLoading(false);
  }
}

function chooseRun(runs) {
  if (state.selectedRun && runs.some((run) => run.id === state.selectedRun)) return state.selectedRun;
  const requested = new URLSearchParams(window.location.search).get("run");
  if (requested && runs.some((run) => run.id === requested)) return requested;
  return runs.find((run) => run.status === "running")?.id || runs.find((run) => run.kind === "rl")?.id || runs[0]?.id || null;
}

function scheduleRefresh() {
  clearTimeout(state.timer);
  state.timer = setTimeout(() => refresh(), state.refreshSeconds * 1000);
}

async function refresh() {
  if (state.refreshing || document.hidden) { scheduleRefresh(); return; }
  state.refreshing = true;
  setLoading(true);
  const version = ++state.requestVersion;
  try {
    const overview = await fetchJson("/api/overview");
    if (version !== state.requestVersion) return;
    if (UI_VERSION && overview.ui_version && overview.ui_version !== UI_VERSION) {
      window.location.reload();
      return;
    }
    state.overview = overview;
    state.refreshSeconds = Number(overview.refresh_seconds || 5);
    state.selectedRun = chooseRun(overview.runs || []);
    renderOverview();
    if (state.selectedRun) await loadDetail(state.selectedRun, version);
    clearError();
    const liveRuns = (overview.runs || []).filter((run) => (
      run.status === "running" || run.status === "recent"
    )).length;
    elements.syncState.innerHTML = `<i></i>${liveRuns ? "指标持续更新" : "已同步"}`;
  } catch (error) {
    showError(`监控数据同步失败：${error.message}`);
  } finally {
    state.refreshing = false;
    setLoading(false);
    scheduleRefresh();
  }
}

elements.runSearch.addEventListener("input", (event) => { state.query = event.target.value; saveSidebar(); renderRunList(); });
elements.filters.addEventListener("click", (event) => {
  const button = event.target.closest("[data-filter]");
  if (!button) return;
  state.filter = button.dataset.filter;
  saveSidebar();
  elements.filters.querySelectorAll(".filter").forEach((item) => item.classList.toggle("active", item === button));
  renderRunList();
});
elements.refreshButton.addEventListener("click", () => refresh());
elements.menuButton.addEventListener("click", () => document.body.classList.add("sidebar-open"));
elements.sidebarClose.addEventListener("click", () => document.body.classList.remove("sidebar-open"));
elements.sidebarScrim.addEventListener("click", () => document.body.classList.remove("sidebar-open"));
document.addEventListener("visibilitychange", () => { if (!document.hidden) refresh(); });

elements.runSearch.value = state.query;
elements.filters.querySelectorAll(".filter").forEach((button) => button.classList.toggle("active", button.dataset.filter === state.filter));
document.querySelector("#pin-run").addEventListener("click", () => {
  if (!state.selectedRun) return;
  state.pinned = state.pinned.includes(state.selectedRun) ? state.pinned.filter((id) => id !== state.selectedRun) : [...state.pinned, state.selectedRun];
  saveSidebar(); renderRunList();
});
refresh();
