const COLORS = ["#22b99a", "#ff705d", "#7d9fff", "#e0a72e", "#9f76dc"];
const MAX_OPPONENT_LINES = 8;

const PRODUCTION_KL_NAMES = {
  maximum_prefix_kl: ["前缀条件 KL", "本轮最大平均值；各计划内的有效前缀条件 KL 求和"],
  maximum_plan_kl: ["完整计划 KL", "本轮观测到的最大平均计划 KL"],
  maximum_field_kl: ["平均字段 KL", "本轮观测到的最大平均字段 KL"],
  approximate_kl: ["近似 KL", "日志中实际记录的近似 KL"],
};

export function productionKlMetrics(values) {
  // Cards and charts share scope discovery. A new maximum_*_kl field remains
  // visible under its recorded name until it receives a human-readable label.
  return Object.keys(values).filter((tag) => {
    const value = values[tag];
    const present = Array.isArray(value) ? value.length > 0 : value !== null
      && value !== undefined && Number.isFinite(Number(value));
    return present && tag.startsWith("rl/optimization/")
      && /^(maximum_.*_kl|approximate_kl)$/.test(tag.split("/").at(-1));
  }).map((tag) => {
    const name = tag.split("/").at(-1);
    const [label, note] = PRODUCTION_KL_NAMES[name] || [name.replaceAll("_", " "), "日志中实际记录的 KL"];
    const index = Object.keys(PRODUCTION_KL_NAMES).indexOf(name);
    return { tag, label, note, order: index < 0 ? 99 : index };
  }).sort((a, b) => a.order - b.order || a.tag.localeCompare(b.tag));
}

const VALUE_QUALITY_CHART = {
  title: "价值模型质量",
  variants: [
    {
      note: "从行动前现金到终局现金的剩余量预测误差；越低越好",
      unit: "剩余现金",
      lines: [
        ["rl/optimization/value_remaining_cash_rmse", "RMSE", COLORS[0]],
        ["rl/optimization/value_remaining_cash_mae", "MAE", COLORS[3]],
      ],
    },
    {
      note: "历史终局现金价值头的预测误差；越低越好",
      unit: "终局现金",
      lines: [
        ["rl/optimization/value_cash_rmse", "RMSE", COLORS[0]],
        ["rl/optimization/value_cash_mae", "MAE", COLORS[3]],
      ],
    },
    {
      note: "W/D/L 价值头：准确率越高越好，Brier 越低越好；仅作训练拟合诊断",
      unit: "比例",
      lines: [
        ["rl/optimization/value_accuracy", "准确率", COLORS[0]],
        ["rl/optimization/value_brier", "Brier", COLORS[3]],
      ],
    },
    {
      note: "W/D/L 价值头交叉熵；越低越好，仅作训练拟合诊断",
      unit: "NLL",
      lines: [
        ["rl/optimization/root_value_loss", "根状态 NLL", COLORS[0]],
        ["rl/optimization/candidate_value_loss", "候选 NLL", COLORS[3]],
      ],
    },
    {
      note: "价值预测负对数似然；越低越好，仅作训练拟合诊断",
      unit: "NLL",
      lines: [["rl/optimization/value_nll", "NLL", COLORS[0]]],
    },
    {
      note: "价值预测训练损失（W/D/L 价值头为交叉熵 NLL）；越低越好",
      unit: "损失",
      lines: [["rl/optimization/value_loss", "价值损失", COLORS[0]]],
    },
  ],
};

const PRODUCTION_CHARTS = [
  {
    title: "终局现金", note: "双方终局现金分布；独立对手评估见评估面板", unit: "现金",
    lines: [
      ["rl/rollout/mean_terminal_cash", "平均", COLORS[3]],
      ["rl/rollout/p10_terminal_cash", "P10", COLORS[2]],
    ],
  },
  {
    title: "物理比赛吞吐", note: "每场比赛只计一次；端到端包含学习、同步和 checkpoint", unit: "games/s",
    lines: [
      ["rl/system/physical_games_per_second", "端到端", COLORS[0]],
      ["rl/rollout/games_per_second", "Rollout", COLORS[2]],
    ],
  },
  {
    title: "Update 阶段耗时", note: "并行设备最慢阶段与全局 wall time", unit: "秒",
    lines: [
      ["rl/system/update_elapsed_seconds", "Update", COLORS[1]],
      ["rl/rollout/elapsed_seconds", "Rollout", COLORS[2]],
      ["rl/system/optimization_seconds", "Learner", COLORS[0]],
      ["rl/system/checkpoint_seconds", "Checkpoint", COLORS[3]],
    ],
  },
  {
    title: "Rollout 耗时", note: "最忙 rank 的原生推进、编码与 GPU 推理", unit: "秒",
    lines: [
      ["rl/rollout/native_seconds", "原生执行", COLORS[1]],
      ["rl/rollout/inference_seconds", "推理", COLORS[2]],
      ["rl/rollout/encoding_seconds", "编码", COLORS[0]],
    ],
  },
  {
    title: "PPO 稳定性", unit: "KL",
    metricFamily: "production-kl",
  },
  {
    title: "采样温度", note: "每轮实际采样温度；T=0 为贪心预热", unit: "T",
    lines: [["rl/run/temperature", "实际温度", COLORS[3]]],
  },
  {
    title: "Actor 学习率", note: "优化器实际采用的学习率", unit: "学习率",
    lines: [["rl/optimization/actor_learning_rate", "Actor", COLORS[0]]],
  },
  {
    title: "优化器更新步数", note: "每轮实际完成的同步更新次数，不累加 GPU 副本", unit: "步",
    lines: [
      ["rl/optimization/actor_steps", "Actor", COLORS[0]],
      ["rl/optimization/critic_steps", "Critic", COLORS[2]],
    ],
  },
  {
    title: "PPO 更新状态", note: "1 表示发生；critic 预热与 KL 提前停止分别记录", unit: "状态",
    lines: [
      ["rl/optimization/actor_early_stop", "KL 提前停止", COLORS[1]],
      ["rl/optimization/critic_warmup", "Critic 预热", COLORS[3]],
    ],
  },
  {
    title: "训练损失", note: "独立 critic 与 BC 保留项；只作训练诊断", unit: "loss",
    lines: [
      ["rl/optimization/value_loss", "Critic", COLORS[2]],
      ["rl/optimization/state_value_loss", "局面价值", COLORS[0]],
      ["rl/optimization/prefix_value_loss", "前缀价值", COLORS[4]],
      ["rl/optimization/bc_retention_loss", "BC", COLORS[3]],
    ],
  },
  {
    title: "GPU 内存峰值", note: "各 rank 最大值", unit: "bytes", bytes: true,
    lines: [
      ["rl/system/cuda_peak_allocated_bytes", "Allocated", COLORS[0]],
      ["rl/system/cuda_peak_reserved_bytes", "Reserved", COLORS[3]],
    ],
  },
];

const RL_CHARTS = [
  {
    title: "训练对局结果",
    note: "每次 rollout 的 W / D / L；属于训练诊断",
    unit: "局",
    lines: [
      ["rl/rollout/wins", "胜", COLORS[0]],
      ["rl/rollout/ties", "平", "#99a5a6"],
      ["rl/rollout/losses", "负", COLORS[1]],
    ],
  },
  {
    title: "终局现金差",
    note: "seat-relative mean cash difference · 0 为基线",
    unit: "现金差",
    zero: true,
    lines: [["rl/rollout/mean_cash_difference", "平均现金差", COLORS[2]]],
  },
  {
    title: "终局现金",
    note: "每次 rollout 的平均 terminal cash",
    unit: "现金",
    lines: [["rl/rollout/mean_terminal_cash", "平均终局现金", COLORS[3]]],
  },
  VALUE_QUALITY_CHART,
  {
    title: "PPO 更新稳定性",
    note: "近似 KL 与裁剪比例",
    unit: "比例",
    lines: [
      ["rl/optimization/approximate_kl", "近似 KL", COLORS[2]],
      ["rl/optimization/clip_fraction", "裁剪比例", COLORS[1]],
    ],
  },
  {
    title: "Rollout 吞吐",
    note: "完整规则物理 game/s 与环境 turn/s",
    unit: "/s",
    lines: [
      ["rl/rollout/games_per_second", "物理比赛", COLORS[2]],
      ["rl/rollout/turns_per_second", "环境 turn", COLORS[0]],
    ],
  },
  {
    title: "损失与熵",
    note: "训练目标只用于优化诊断",
    unit: "值",
    lines: [
      ["rl/optimization/value_loss", "Value loss", COLORS[2]],
      ["rl/optimization/root_value_loss", "Root W/D/L", COLORS[2]],
      ["rl/optimization/candidate_value_loss", "Candidate W/D/L", COLORS[0]],
      ["rl/optimization/value_nll", "Value NLL", COLORS[2]],
      ["rl/optimization/entropy", "Entropy", COLORS[3]],
      ["rl/optimization/total_loss", "Total loss", COLORS[4]],
    ],
  },
];

const TASK_RL_CHARTS = [
  {
    title: "Self-play 物理局结果",
    note: "seat-0 记账面；seat-1 结果严格镜像，不重复计为物理比赛",
    unit: "局",
    lines: [
      ["rl/rollout/wins", "胜", COLORS[0]],
      ["rl/rollout/ties", "平", "#99a5a6"],
      ["rl/rollout/losses", "负", COLORS[1]],
    ],
  },
  {
    title: "终局现金诊断",
    note: "seat-0 terminal cash 与 cash difference；仅作训练诊断",
    unit: "现金",
    zero: true,
    lines: [
      ["rl/rollout/mean_terminal_cash", "终局现金", COLORS[3]],
      ["rl/rollout/mean_cash_difference", "现金差", COLORS[2]],
    ],
  },
  {
    title: "Self-play 吞吐",
    note: "物理 match/s 与保留双座位训练 trajectory/s 分开统计",
    unit: "/s",
    lines: [
      ["rl/rollout/games_per_second", "物理比赛", COLORS[2]],
      ["rl/rollout/training_episodes_per_second", "训练视角", COLORS[0]],
    ],
  },
  {
    title: "Task AR 决策吞吐",
    note: "GPU task autoregressive decoder 每秒完成的条件决策数",
    unit: "decision/s",
    lines: [
      ["rl/rollout/task_decisions_per_second", "Task AR", COLORS[4]],
    ],
  },
  {
    title: "Update 阶段耗时",
    note: "完整 update、rollout 与 PPO wall time",
    unit: "秒",
    lines: [
      ["rl/system/update_elapsed_seconds", "Update", COLORS[1]],
      ["rl/rollout/elapsed_seconds", "Rollout", COLORS[2]],
      ["rl/system/optimization_seconds", "PPO", COLORS[0]],
    ],
  },
  {
    title: "Task / Market 策略损失",
    note: "两个 AR factor surface 的 PPO policy loss",
    unit: "loss",
    zero: true,
    lines: [
      ["rl/optimization/task_policy_loss", "Task", COLORS[4]],
      ["rl/optimization/market_policy_loss", "Market", COLORS[0]],
    ],
  },
  {
    title: "Task / Market 价值损失",
    note: "terminal W/D/L critic loss；不替代独立闭环评估",
    unit: "loss",
    lines: [
      ["rl/optimization/task_value_loss", "Task", COLORS[4]],
      ["rl/optimization/market_value_loss", "Market", COLORS[2]],
      ["rl/optimization/total_loss", "Total", COLORS[1]],
    ],
  },
  {
    title: "PPO 最大 KL",
    note: "每个 update 观测到的 task / market 最大 KL；用于 target-KL 早停",
    unit: "KL",
    lines: [
      ["rl/optimization/maximum_task_kl", "Task", COLORS[4]],
      ["rl/optimization/maximum_market_kl", "Market", COLORS[0]],
    ],
  },
  {
    title: "Task / Market 策略熵",
    note: "两个动作面的行为策略熵",
    unit: "entropy",
    lines: [
      ["rl/optimization/task_entropy", "Task", COLORS[4]],
      ["rl/optimization/market_entropy", "Market", COLORS[3]],
    ],
  },
  {
    title: "PPO Factor 数",
    note: "实际参与本轮优化的 task 与 market 行为 factors",
    unit: "factor",
    lines: [
      ["rl/optimization/task_factors", "Task", COLORS[4]],
      ["rl/optimization/market_factors", "Market", COLORS[0]],
    ],
  },
  {
    title: "优势归一化",
    note: "Task / market episode advantage 的原始均值与归一化尺度",
    unit: "值",
    zero: true,
    lines: [
      ["rl/optimization/task_advantage/mean", "Task mean", COLORS[4]],
      ["rl/optimization/market_advantage/mean", "Market mean", COLORS[0]],
      ["rl/optimization/task_advantage/scale", "Task scale", COLORS[2]],
      ["rl/optimization/market_advantage/scale", "Market scale", COLORS[3]],
    ],
  },
  {
    title: "Rollout 热路径耗时",
    note: "并发 actor lane 的累计工作时间；用于比较阶段占比，不是 wall time",
    unit: "秒",
    lines: [
      ["rl/rollout/phase_work_seconds/task_decode", "Task decode", COLORS[4]],
      ["rl/rollout/phase_work_seconds/market_decode", "Market decode", COLORS[0]],
      ["rl/rollout/phase_work_seconds/record", "Record", COLORS[3]],
      ["rl/rollout/phase_work_seconds/environment", "Environment", COLORS[1]],
      ["rl/rollout/phase_work_seconds/policy_inputs", "Inputs", COLORS[2]],
      ["rl/rollout/phase_work_seconds/start_turn", "Start turn", "#63747a"],
      ["rl/rollout/phase_work_seconds/cuda_graph_capture", "Graph capture", "#99a5a6"],
    ],
  },
  {
    title: "内存峰值",
    note: "两卡聚合 CUDA 峰值、rollout host tape 与最大 episode minibatch",
    unit: "bytes",
    bytes: true,
    lines: [
      ["rl/system/cuda_peak_allocated_bytes", "GPU allocated", COLORS[0]],
      ["rl/system/cuda_peak_reserved_bytes", "GPU reserved", COLORS[3]],
      ["rl/rollout/host_bytes", "Host tape", COLORS[2]],
      ["rl/rollout/maximum_minibatch_bytes", "Max minibatch", COLORS[4]],
    ],
  },
  {
    title: "官方 Actor 时间预算",
    note: "最慢 batched actor call 与该 episode panel 剩余 overage",
    unit: "秒",
    lines: [
      ["rl/rollout/maximum_actor_seconds", "最大 actor", COLORS[1]],
      ["rl/rollout/remaining_overage_seconds", "剩余 overage", COLORS[0]],
    ],
  },
];

const INTENT_RL_CHARTS = [
  VALUE_QUALITY_CHART,
  {
    title: "Self-play 物理局结果",
    note: "每个 update 的 seat-0 记账 W / D / L",
    unit: "局",
    lines: [
      ["rl/rollout/wins", "胜", COLORS[0]],
      ["rl/rollout/ties", "平", "#99a5a6"],
      ["rl/rollout/losses", "负", COLORS[1]],
    ],
  },
  {
    title: "终局现金诊断",
    note: "seat-0 terminal cash 与 cash difference；仅作训练诊断",
    unit: "现金",
    zero: true,
    lines: [
      ["rl/rollout/mean_terminal_cash", "终局现金", COLORS[3]],
      ["rl/rollout/mean_cash_difference", "现金差", COLORS[2]],
    ],
  },
  {
    title: "Rollout 吞吐",
    note: "物理 game/s、pseudo-step/s 与 official turn/s",
    unit: "/s",
    lines: [
      ["rl/rollout/games_per_second", "物理比赛", COLORS[2]],
      ["rl/rollout/pseudo_steps_per_second", "Pseudo-step", COLORS[4]],
      ["rl/rollout/turns_per_second", "Official turn", COLORS[0]],
    ],
  },
  {
    title: "Update 阶段耗时",
    note: "完整 update、rollout 与 PPO wall time",
    unit: "秒",
    lines: [
      ["rl/system/update_elapsed_seconds", "Update", COLORS[1]],
      ["rl/rollout/elapsed_seconds", "Rollout", COLORS[2]],
      ["rl/system/optimization_seconds", "PPO", COLORS[0]],
    ],
  },
  {
    title: "Rollout 热路径耗时",
    note: "device transaction 各阶段 wall time",
    unit: "秒",
    lines: [
      ["rl/rollout/policy_seconds", "Policy", COLORS[4]],
      ["rl/rollout/decision_seconds", "Decision", COLORS[2]],
      ["rl/rollout/encode_seconds", "Encode", COLORS[0]],
      ["rl/rollout/graph_capture_seconds", "Graph capture", "#99a5a6"],
      ["rl/rollout/native_observation_seconds", "Native obs", COLORS[3]],
      ["rl/rollout/action_compilation_seconds", "Compile", COLORS[1]],
    ],
  },
  {
    title: "PPO 更新稳定性",
    note: "近似 KL、裁剪比例与优势归一化",
    unit: "值",
    zero: true,
    lines: [
      ["rl/optimization/approximate_kl", "近似 KL", COLORS[2]],
      ["rl/optimization/clip_fraction", "裁剪比例", COLORS[1]],
      ["rl/optimization/advantage_mean", "Adv mean", COLORS[0]],
      ["rl/optimization/advantage_scale", "Adv scale", COLORS[3]],
    ],
  },
  {
    title: "损失与熵",
    note: "pseudo-step PPO 诊断",
    unit: "值",
    lines: [
      ["rl/optimization/value_loss", "Value loss", COLORS[2]],
      ["rl/optimization/policy_loss", "Policy loss", COLORS[0]],
      ["rl/optimization/entropy", "Entropy", COLORS[3]],
      ["rl/optimization/total_loss", "Total loss", COLORS[4]],
    ],
  },
  {
    title: "行为重放误差",
    note: "首轮 update 的 causal behavior replay 审计",
    unit: "误差",
    lines: [
      ["rl/behavior_replay/log_probability_error", "Logprob", COLORS[2]],
      ["rl/behavior_replay/value_error", "Value", COLORS[3]],
    ],
  },
  {
    title: "内存峰值",
    note: "双卡聚合 CUDA allocated / reserved 峰值",
    unit: "bytes",
    bytes: true,
    lines: [
      ["rl/system/cuda_peak_allocated_bytes", "GPU allocated", COLORS[0]],
      ["rl/system/cuda_peak_reserved_bytes", "GPU reserved", COLORS[3]],
    ],
  },
];

const BC_CHARTS = [
  {
    title: "训练 / 验证目标",
    note: "优先显示 causal objective，兼容历史 action NLL",
    unit: "NLL",
    alternatives: [
      [
        ["bc/training/causal_objective_nll", "训练", COLORS[2]],
        ["bc/validation/causal_objective_nll", "验证", COLORS[1]],
      ],
      [
        ["bc/training/objective_nll", "训练", COLORS[2]],
        ["bc/validation/objective_nll", "验证", COLORS[1]],
      ],
      [
        ["bc/training/action_nll", "训练", COLORS[2]],
        ["bc/validation/action_nll", "验证", COLORS[1]],
      ],
    ],
  },
  {
    title: "动作准确率",
    note: "训练集与验证集逐 epoch 走势",
    unit: "比例",
    lines: [
      ["bc/training/action_accuracy", "训练", COLORS[2]],
      ["bc/validation/action_accuracy", "验证", COLORS[0]],
    ],
  },
  {
    title: "验证集分域准确率",
    note: "单位、市场与数量动作",
    unit: "比例",
    lines: [
      ["bc/validation/unit_accuracy", "单位", COLORS[0]],
      ["bc/validation/market_accuracy", "市场", COLORS[3]],
      ["bc/validation/quantity_accuracy", "数量", COLORS[4]],
    ],
  },
  {
    title: "训练吞吐",
    note: "每个 epoch 的有效 turn/s",
    unit: "turn/s",
    lines: [
      ["bc/training/turns_per_second", "训练", COLORS[2]],
      ["bc/validation/turns_per_second", "验证", COLORS[0]],
    ],
  },
  {
    title: "GPU 峰值显存",
    note: "allocated / reserved bytes",
    unit: "bytes",
    bytes: true,
    lines: [
      ["bc/system/cuda_peak_allocated_bytes", "已分配", COLORS[0]],
      ["bc/system/cuda_peak_reserved_bytes", "已保留", COLORS[3]],
    ],
  },
  {
    title: "Epoch 耗时",
    note: "训练与验证合计 wall time",
    unit: "秒",
    lines: [["bc/system/elapsed_seconds", "耗时", COLORS[1]]],
  },
];

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function compact(value, bytes = false) {
  if (value === null || value === undefined || !Number.isFinite(Number(value))) return "—";
  const number = Number(value);
  if (bytes) {
    const units = ["B", "KiB", "MiB", "GiB", "TiB"];
    let scaled = Math.abs(number);
    let unit = 0;
    while (scaled >= 1024 && unit < units.length - 1) { scaled /= 1024; unit += 1; }
    return `${number < 0 ? "−" : ""}${scaled.toFixed(scaled >= 100 ? 0 : scaled >= 10 ? 1 : 2)} ${units[unit]}`;
  }
  const absolute = Math.abs(number);
  if (absolute >= 1e9) return `${(number / 1e9).toFixed(1)}B`;
  if (absolute >= 1e6) return `${(number / 1e6).toFixed(1)}M`;
  if (absolute >= 1e3) return `${(number / 1e3).toFixed(1)}k`;
  if (absolute !== 0 && absolute < 0.001) return number.toExponential(2);
  if (absolute < 1) return number.toFixed(4).replace(/0+$/, "").replace(/\.$/, "");
  return number.toLocaleString("zh-CN", { maximumFractionDigits: 2 });
}

function resolveLines(config, series) {
  if (config.lines) return config.lines;
  const alternatives = config.alternatives || [];
  return alternatives.find((candidate) => candidate.some(([tag]) => series[tag]?.length)) || alternatives[0] || [];
}

function resolveConfig(config, series) {
  if (config.metricFamily === "production-kl") {
    const metrics = productionKlMetrics(series);
    return {
      ...config,
      note: metrics.map((metric) => metric.note).join("；") || "等待 PPO KL 标量",
      lines: metrics.map((metric, index) => [metric.tag, metric.label, COLORS[(index + 2) % COLORS.length]]),
    };
  }
  if (!config.variants?.length) return config;
  const variant = config.variants.find((candidate) => (
    resolveLines(candidate, series).some(([tag]) => series[tag]?.length)
  )) || config.variants[0];
  return { ...config, ...variant };
}

function pathFor(points, x, y) {
  return points.map((point, index) => `${index ? "L" : "M"}${x(point.step).toFixed(2)},${y(point.value).toFixed(2)}`).join(" ");
}

function nearest(points, targetStep) {
  let low = 0;
  let high = points.length - 1;
  while (low < high) {
    const middle = Math.floor((low + high) / 2);
    if (points[middle].step < targetStep) low = middle + 1;
    else high = middle;
  }
  if (low > 0 && Math.abs(points[low - 1].step - targetStep) < Math.abs(points[low].step - targetStep)) return points[low - 1];
  return points[low];
}

function renderChart(container, config, metricSeries) {
  config = resolveConfig(config, metricSeries);
  const lines = resolveLines(config, metricSeries)
    .map(([tag, label, color]) => ({ tag, label, color, points: metricSeries[tag] || [] }))
    .filter((line) => line.points.length);
  const latestLegend = lines.map((line) => {
    const value = line.points.at(-1)?.value;
    return `<span class="legend-item"><i style="background:${line.color}"></i><span class="legend-label" title="${escapeHtml(line.label)}">${escapeHtml(line.label)}</span><b>${compact(value, config.bytes)}</b></span>`;
  }).join("");
  container.innerHTML = `
    <div class="chart-head">
      <div class="chart-title"><h3>${escapeHtml(config.title)}</h3><p>${escapeHtml(config.note)}</p></div>
      <div class="chart-legend">${latestLegend}</div>
    </div>
    <div class="chart-canvas"></div>`;
  const canvas = container.querySelector(".chart-canvas");
  if (!lines.length) {
    canvas.innerHTML = '<div class="chart-empty">此 run 暂无该组标量</div>';
    return;
  }

  const width = Math.max(360, Math.round(canvas.getBoundingClientRect().width || 700));
  const height = 246;
  const margin = { top: 12, right: 14, bottom: 30, left: 54 };
  const plotWidth = width - margin.left - margin.right;
  const plotHeight = height - margin.top - margin.bottom;
  const allPoints = lines.flatMap((line) => line.points);
  let xMin = Math.min(...allPoints.map((point) => point.step));
  let xMax = Math.max(...allPoints.map((point) => point.step));
  let yMin = Math.min(...allPoints.map((point) => point.value));
  let yMax = Math.max(...allPoints.map((point) => point.value));
  if (xMin === xMax) { xMin -= 1; xMax += 1; }
  if (yMin === yMax) {
    const padding = Math.abs(yMin) * 0.08 || 1;
    yMin -= padding; yMax += padding;
  } else {
    const padding = (yMax - yMin) * 0.09;
    yMin -= padding; yMax += padding;
  }
  const x = (value) => margin.left + (value - xMin) / (xMax - xMin) * plotWidth;
  const y = (value) => margin.top + (yMax - value) / (yMax - yMin) * plotHeight;

  const yTicks = Array.from({ length: 5 }, (_, index) => yMin + (yMax - yMin) * index / 4);
  const xTicks = Array.from({ length: 3 }, (_, index) => xMin + (xMax - xMin) * index / 2);
  const grid = yTicks.map((tick) => `
    <line class="chart-grid-line" x1="${margin.left}" x2="${width - margin.right}" y1="${y(tick)}" y2="${y(tick)}"></line>
    <text class="chart-axis-label" x="${margin.left - 9}" y="${y(tick) + 3}" text-anchor="end">${escapeHtml(compact(tick, config.bytes))}</text>`).join("");
  const xLabels = xTicks.map((tick) => `<text class="chart-axis-label" x="${x(tick)}" y="${height - 7}" text-anchor="middle">${Math.round(tick).toLocaleString("zh-CN")}</text>`).join("");
  const paths = lines.map((line) => {
    const last = line.points.at(-1);
    return `<path class="chart-path" stroke="${line.color}" d="${pathFor(line.points, x, y)}"></path>
      <circle class="chart-endpoint" fill="${line.color}" cx="${x(last.step)}" cy="${y(last.value)}" r="3.6"></circle>`;
  }).join("");
  const zero = config.zero && yMin < 0 && yMax > 0
    ? `<line class="zero-line" x1="${margin.left}" x2="${width - margin.right}" y1="${y(0)}" y2="${y(0)}"></line>` : "";
  canvas.innerHTML = `
    <svg class="chart-svg" viewBox="0 0 ${width} ${height}" preserveAspectRatio="none" role="img" aria-label="${escapeHtml(config.title)}">
      ${grid}${zero}${paths}${xLabels}
      <line class="hover-line" x1="0" x2="0" y1="${margin.top}" y2="${height - margin.bottom}"></line>
      <rect class="chart-hit" x="${margin.left}" y="${margin.top}" width="${plotWidth}" height="${plotHeight}"></rect>
    </svg>
    <div class="chart-tooltip"></div>`;

  const svg = canvas.querySelector("svg");
  const hit = canvas.querySelector(".chart-hit");
  const hover = canvas.querySelector(".hover-line");
  const tooltip = canvas.querySelector(".chart-tooltip");
  hit.addEventListener("pointermove", (event) => {
    const bounds = svg.getBoundingClientRect();
    const svgX = (event.clientX - bounds.left) / bounds.width * width;
    const clampedX = Math.max(margin.left, Math.min(width - margin.right, svgX));
    const step = xMin + (clampedX - margin.left) / plotWidth * (xMax - xMin);
    const values = lines.map((line) => ({ line, point: nearest(line.points, step) }));
    const anchor = values.reduce((best, item) => Math.abs(item.point.step - step) < Math.abs(best.point.step - step) ? item : best);
    const anchorX = x(anchor.point.step);
    hover.setAttribute("x1", anchorX); hover.setAttribute("x2", anchorX); hover.style.opacity = "1";
    tooltip.innerHTML = `<div class="tooltip-step">${escapeHtml(config.unit)} · ${escapeHtml(config.stepLabel || "step")} ${anchor.point.step.toLocaleString("zh-CN")}</div>${values.map(({ line, point }) => `<div class="tooltip-row"><span><i style="background:${line.color}"></i>${escapeHtml(line.label)}</span><b>${compact(point.value, config.bytes)}</b></div>`).join("")}`;
    tooltip.style.left = `${anchorX / width * 100}%`;
    tooltip.style.top = `${Math.max(22, Math.min(88, event.offsetY / bounds.height * 100))}%`;
    tooltip.classList.add("visible");
  });
  hit.addEventListener("pointerleave", () => { hover.style.opacity = "0"; tooltip.classList.remove("visible"); });
}

function opponentMetricLines(series, latest, metric) {
  const prefix = "rl/rollout/opponents/";
  const activeOpponents = new Set(Object.keys(latest || {})
    .filter((tag) => tag.startsWith(prefix))
    .map((tag) => tag.slice(prefix.length).split("/")[0]));
  return Object.keys(series)
    .filter((tag) => {
      if (!tag.startsWith(prefix)) return false;
      const path = tag.slice(prefix.length).split("/");
      return path.length === 2 && path[1] === metric
        && (!activeOpponents.size || activeOpponents.has(path[0]));
    })
    .sort((left, right) => {
      const leftOpponent = left.slice(prefix.length).split("/")[0];
      const rightOpponent = right.slice(prefix.length).split("/")[0];
      if (leftOpponent === "self_play") return -1;
      if (rightOpponent === "self_play") return 1;
      if (leftOpponent === "history") return -1;
      if (rightOpponent === "history") return 1;
      return leftOpponent.localeCompare(rightOpponent);
    })
    .slice(0, MAX_OPPONENT_LINES)
    .map((tag, index) => [
      tag,
      tag.slice(prefix.length).split("/")[0],
      COLORS[index % COLORS.length],
    ]);
}

export function renderCharts(target, kind, metrics, customConfigurations = null) {
  const series = metrics?.series || {};
  const latest = metrics?.latest || {};
  const production = Boolean(series["rl/system/physical_games_per_second"]?.length);
  const taskTape = Boolean(
    series["rl/optimization/task_value_loss"]?.length
    || series["rl/rollout/task_decisions_per_second"]?.length,
  );
  const intentLedger = Boolean(
    series["rl/rollout/pseudo_steps_per_second"]?.length
    || series["rl/rollout/pseudo_steps"]?.length,
  );
  let configurations = customConfigurations || (kind === "rl"
    ? [...(production ? PRODUCTION_CHARTS : taskTape ? TASK_RL_CHARTS : intentLedger ? INTENT_RL_CHARTS : RL_CHARTS)]
    : kind === "bc" ? BC_CHARTS : []);
  if (kind === "rl") {
    const capabilityModeLines = [
      ["rl/search/selected_mode_fraction/0", "DIRECT", COLORS[2]],
      ["rl/search/selected_mode_fraction/1", "CONTINUE", COLORS[0]],
      ["rl/search/selected_mode_fraction/2", "CANCEL", COLORS[3]],
      ["rl/search/selected_mode_fraction/3", "PATCH", COLORS[1]],
    ];
    if (capabilityModeLines.some(([tag]) => series[tag]?.length)) {
      configurations.splice(1, 0, {
        title: "能力模式选择",
        note: "最终 on-policy behavior distribution 的实际采样占比",
        unit: "比例",
        lines: capabilityModeLines,
      });
    }
    const winRateLines = opponentMetricLines(series, latest, "win_rate");
    const cashDifferenceLines = opponentMetricLines(series, latest, "mean_cash_difference");
    const customOpponents = customConfigurations?.some((configuration) =>
      configuration.lines.some(([tag]) => tag.startsWith("rl/rollout/opponents/")));
    if (winRateLines.length && !customOpponents) {
      configurations.push({
        title: "逐对手胜率",
        note: "每个 rollout update 的完整比赛结果；history 表示当轮选中的轮换快照",
        unit: "比例",
        lines: winRateLines,
      });
    }
    if (cashDifferenceLines.length && !customOpponents) {
      configurations.push({
        title: "逐对手终局现金差",
        note: "候选视角相对当前对手类别的 mean terminal cash difference",
        unit: "现金差",
        zero: true,
        lines: cashDifferenceLines,
      });
    }
  }
  if (!configurations.length) {
    configurations = Object.keys(series).slice(0, 4).map((tag, index) => ({
      title: tag.split("/").at(-1), note: tag, unit: "值", lines: [[tag, "值", COLORS[index % COLORS.length]]],
    }));
  }
  target.innerHTML = "";
  if (!configurations.length) {
    target.innerHTML = '<div class="chart-card wide"><div class="chart-empty">这个 run 暂无训练标量</div></div>';
    return;
  }
  configurations.forEach((config) => {
    const card = document.createElement("article");
    card.className = "chart-card";
    target.appendChild(card);
    renderChart(card, config, series);
  });
}
