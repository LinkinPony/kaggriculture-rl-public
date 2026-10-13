export const isLearningBC = (run) => run.family === "learning" && run.kind === "bc";
export const domains = [
  ["unit_target", "单位目标"], ["unit_operation", "单位操作"], ["unit_quantity", "单位数量"],
  ["market_operation", "市场操作"], ["market_quantity", "市场数量"],
];
const colors = ["#22b99a", "#7d9fff", "#e0a72e", "#9f76dc", "#de7e96"];
const readingStates = new Map();

function updatePanel(panel, markup, runId) {
  const previousRun = panel.dataset.run;
  const focused = panel.contains(document.activeElement)
    ? document.activeElement.closest("details[id]")?.id : null;
  if (previousRun) {
    readingStates.set(previousRun, {
      disclosures: [...panel.querySelectorAll("details[id]")].map((node) => [node.id, node.open]),
      scroll: [...panel.querySelectorAll(".bc-table-wrap[id]")].map((node) => [node.id, node.scrollLeft, node.scrollTop]),
    });
  }
  panel.innerHTML = markup;
  panel.dataset.run = runId;
  const saved = readingStates.get(runId);
  for (const [id, open] of saved?.disclosures || []) {
    const node = panel.querySelector(`#${id}`);
    if (node) node.open = open;
  }
  if (previousRun === runId && focused) {
    panel.querySelector(`#${focused} > summary`)?.focus({ preventScroll: true });
  }
  for (const [id, left, top] of saved?.scroll || []) {
    const node = panel.querySelector(`#${id}`);
    if (node) { node.scrollLeft = left; node.scrollTop = top; }
  }
}

export function bcCards(detail, f) {
  const { metricCard, integer, number, duration } = f;
  const bc = detail.pretraining || {};
  const latest = detail.metrics?.latest || {};
  const batch = bc.batches?.at(-1);
  const epoch = Math.min(bc.epochs || 100, bc.completed_epochs + 1);
  const nll = bc.current_epoch_nll ?? latest["bc/training/action_nll"];
  const seconds = batch?.performance?.seconds;
  const speed = seconds > 0 ? batch.rows / seconds : latest["bc/training/turns_per_second"];
  return [
    metricCard("BC Epoch", `${integer(bc.completed_epochs)} / ${integer(bc.epochs)}`, `已完成完整 epoch · 当前第 ${integer(epoch)} 轮`, 1),
    metricCard("监督回合", integer(bc.rows), `总预算 ${integer(bc.total_training_rows)} · 每轮完整遍历训练集`, 2),
    metricCard("训练 NLL", number(nll, 5), "当前 epoch 按有效回合加权；每回合内按有效字段取均值", 3),
    metricCard("验证 NLL", number(latest["bc/validation/action_nll"], 5), "每个 epoch 遍历完整 selection 集", 4),
    metricCard("有效回合 / 秒", number(speed, 0), `双卡合计 · 最近批次 ${duration(seconds)}`, 5),
    metricCard("优化器更新", integer(bc.optimizer_steps), `学习率 ${number(bc.learning_rate, 6)} · 全局批次 ${integer(bc.batch_rows)} 上下文回合`, 6),
    metricCard("预计剩余", duration(detail.run.progress?.eta_seconds), "根据已完成 epoch 的训练与验证耗时估算", 7),
    metricCard("保存进度", `${integer(bc.checkpoint_cursor)} 批`, `实时已处理 ${integer(bc.cursor)} 批 · ${(bc.devices || []).join(" + ")} · ${bc.precision || "—"}`, 8),
  ];
}

export function bcCharts() {
  return [
    { title: "训练与验证 NLL", note: "完整分区；每个有效回合等权，越低越好", unit: "NLL", lines: [
      ["bc/training/action_nll", "训练", colors[0]], ["bc/validation/action_nll", "验证", colors[1]],
    ] },
    { title: "验证集：五类动作 NLL", note: "各动作域按其有效字段数归一化", unit: "NLL", lines:
      domains.map(([key, label], i) => [`bc/validation/${key}_nll`, label, colors[i]]) },
    { title: "验证集：五类动作准确率", note: "给定教师前缀的条件 argmax 命中率", unit: "比例", lines:
      domains.map(([key, label], i) => [`bc/validation/${key}_accuracy`, label, colors[i]]) },
    { title: "训练集：五类动作准确率", note: "完整 epoch 的有效字段统计", unit: "比例", lines:
      domains.map(([key, label], i) => [`bc/training/${key}_accuracy`, label, colors[i]]) },
    { title: "有效监督吞吐", note: "双卡合计，不计填充和不支持的教师动作", unit: "回合/秒", lines: [
      ["bc/training/turns_per_second", "训练", colors[0]], ["bc/validation/turns_per_second", "验证", colors[1]],
    ] },
    { title: "Epoch 阶段耗时", note: "首轮包含编译；每个 epoch 均完成验证", unit: "秒", lines: [
      ["bc/system/training_seconds", "训练", colors[0]], ["bc/system/validation_seconds", "验证", colors[1]],
    ] },
  ];
}

function table(headers, rows, id) {
  return `<div class="bc-table-wrap" id="${id}"><table class="opponent-table"><thead><tr>${headers.map((h) => `<th>${h}</th>`).join("")}</tr></thead><tbody>${rows.join("")}</tbody></table></div>`;
}

export function renderPretraining(detail, f) {
  const section = document.querySelector("#bc-section");
  const active = isLearningBC(detail.run);
  section.classList.toggle("hidden", !active);
  const evaluation = document.querySelector("#evaluation-panel");
  evaluation.closest("section").querySelector("h2").textContent = active ? "独立确认集" : "模型表现";
  if (!active) return;
  const { integer, number, duration, percent, escapeHtml } = f;
  const bc = detail.pretraining || {};
  const latest = bc.records?.at(-1);
  const batch = bc.batches?.at(-1);
  const perEpoch = bc.batches_per_epoch || 0;
  const within = perEpoch ? bc.cursor % perEpoch : 0;
  const completed = bc.completed_epochs >= bc.epochs;
  const fraction = completed ? 100 : perEpoch ? 100 * within / perEpoch : 0;
  const fieldRows = domains.map(([key, label]) => `<tr><td>${label}</td><td>${number(latest?.training?.[`${key}_nll`], 5)}</td><td>${number(latest?.validation?.[`${key}_nll`], 5)}</td><td>${percent(latest?.training?.[`${key}_accuracy`])}</td><td>${percent(latest?.validation?.[`${key}_accuracy`])}</td><td>${integer(latest?.validation?.[`${key}_fields`])}</td></tr>`);
  const splitRows = [["train", "训练"], ["selection", "验证"], ["confirmation", "确认"]].map(([key, label]) => {
    const row = bc.coverage?.[key] || {};
    return `<tr><td>${label}</td><td>${integer(row.episodes)}</td><td>${integer(row.trajectories)}</td><td>${integer(row.usable_rows)}</td></tr>`;
  });
  const epochRows = [...(bc.records || [])].reverse().map((row) => `<tr><td>${integer(row.epoch)}</td><td>${number(row.train_nll, 5)}</td><td>${number(row.selection_nll, 5)}</td><td>${number(row.selection_nll - row.train_nll, 5)}</td><td>${integer(row.train_rows)}</td><td>${duration(row.training_seconds)}</td><td>${duration(row.validation_seconds)}</td></tr>`);
  const batchRows = [...(bc.batches || [])].reverse().map((row) => `<tr><td>${integer(row.batch)}</td><td>${integer(row.epoch)}</td><td>${number(row.nll, 5)}</td><td>${integer(row.rows)}</td><td>${number(row.gradient_norm, 4)}</td><td>${duration(row.performance?.seconds)}</td><td>${duration(row.performance?.load_seconds)}</td></tr>`);
  const teachers = Object.entries(bc.teachers || {}).map(([name, count]) => `<tr><td>${escapeHtml(name)}</td><td>${integer(count)}</td></tr>`);
  const origin = bc.initial_weights;
  const originNote = origin ? `<p class="bc-note">起始权重：${escapeHtml(origin.run.split("/").at(-1))} / ${escapeHtml(origin.checkpoint)} · BC 优化器重新初始化</p>` : "";
  updatePanel(document.querySelector("#bc-panel"), `
    <div class="panel-card bc-live"><div class="panel-heading"><h3>${completed ? "100 epoch 预算已完成" : `当前 epoch · ${integer(within)} / ${integer(perEpoch)} 批`}</h3><span class="source-badge">${bc.all_array_hashes_verified ? "数据哈希已核验" : "数据核验 / 首轮编译中"}</span></div>
      <div class="hero-progress-track"><i style="width:${fraction}%"></i></div>
      <p>最近批次 NLL ${number(batch?.nll, 5)} · 梯度范数 ${number(batch?.gradient_norm, 4)} · ${bc.early_stopping ? "按已配置规则早停" : "固定 epoch 预算，无早停"}</p>${originNote}</div>
    <div class="bc-grid"><article class="panel-card"><h3>最近完整 epoch · 动作域诊断</h3>${table(["动作域", "训练 NLL", "验证 NLL", "训练准确率", "验证准确率", "验证字段数"], fieldRows, "bc-fields-table")}<p class="bc-note">条件动作拟合指标；不代表完整比赛胜率。</p></article>
    <article class="panel-card"><h3>数据分区与覆盖</h3>${table(["分区", "比赛", "轨迹", "监督回合"], splitRows, "bc-splits-table")}
      <details id="bc-teachers"><summary>八队轨迹数与数据来源</summary>${table(["队伍", "轨迹数"], teachers, "bc-teachers-table")}<p class="bc-note">${escapeHtml(bc.manifest || "")}</p><code class="bc-hash">${escapeHtml(bc.dataset_sha256 || "")}</code></details></article></div>
    <details class="panel-card" id="bc-epochs" open><summary>逐 epoch 明细 · 已完成 ${integer(bc.completed_epochs)} 轮</summary>${epochRows.length ? table(["Epoch", "训练 NLL", "验证 NLL", "验证 − 训练", "训练回合", "训练耗时", "验证耗时"], epochRows, "bc-epochs-table") : '<p class="bc-note">首个完整 epoch 结束后出现验证曲线与明细。</p>'}</details>
    <details class="panel-card" id="bc-batches"><summary>最近 ${integer(batchRows.length)} 个训练批次</summary>${table(["批次", "Epoch", "NLL", "有效回合", "梯度范数", "总耗时", "数据加载"], batchRows, "bc-batches-table")}</details>`, detail.run.id);
  const confirmation = bc.confirmation || {};
  evaluation.classList.toggle("empty-panel", !confirmation.rows);
  evaluation.innerHTML = confirmation.rows
    ? `<div class="panel-card"><h3>最终确认 NLL ${number(confirmation.nll, 5)}</h3><p>第 ${integer(confirmation.epoch)} 个 epoch 后，完整评估 ${integer(confirmation.rows)} 个独立确认回合。</p></div>`
    : `<div><h3>确认集保留至训练结束</h3><p>${integer(bc.coverage?.confirmation?.usable_rows)} 个监督回合；完成固定 ${integer(bc.epochs)} epoch 后评估，不参与参数更新或逐轮选择。</p></div>`;
}
