const COLORS = ["#22b99a", "#7d9fff", "#e0a72e", "#9f76dc", "#ff705d"];
const MODE_NAMES = { greedy: "贪心评估", sampled: "采样评估", selection_sampled: "固定种子 selection · 采样", confirmation_sampled: "预留种子 confirmation · 采样" };
const FIELDS = ["wins", "ties", "losses", "mean_terminal_cash", "mean_cash_difference"];

export function evaluationSeries(points) {
  // Keep missing opponents absent. A missing match panel is never a zero win rate.
  const series = {};
  for (const point of points) {
    const groups = [["overall", point.overall], ...Object.entries(point.opponents || {})
      .map(([name, values]) => [`opponent/${encodeURIComponent(name)}`, values])];
    for (const [group, values] of groups) {
      if (!values) continue;
      const games = Number(values.games);
      const metrics = { ...values };
      if (games > 0 && Number.isFinite(values.wins)) metrics.win_rate = values.wins / games * 100;
      for (const field of [...FIELDS, "win_rate"]) {
        if (!Number.isFinite(metrics[field])) continue;
        const tag = `${group}/${field}`;
        (series[tag] ||= []).push({ step: point.step, value: metrics[field] });
      }
    }
  }
  for (const values of Object.values(series)) values.sort((a, b) => a.step - b.step);
  return series;
}

export function renderEvaluationHistory(target, history, runId, f) {
  const points = history?.points || [];
  if (!points.length) { target.innerHTML = ""; return; }
  const sameRun = target.dataset.runId === runId;
  const previousMode = sameRun ? target.querySelector('[data-evaluation="mode"]')?.value : null;
  const previousOpponent = sameRun ? target.querySelector('[data-evaluation="opponent"]')?.value : null;
  const previousStep = sameRun ? target.querySelector('[data-evaluation="step"]')?.value : null;
  const modes = [...new Set(points.map((point) => point.mode))];
  const mode = modes.includes(previousMode) ? previousMode : modes.includes("greedy") ? "greedy" : modes.includes("selection_sampled") ? "selection_sampled" : modes[0];
  const selected = points.filter((point) => point.mode === mode);
  const opponents = [...new Set(selected.flatMap((point) => Object.keys(point.opponents || {})))].sort();
  const choices = [
    ["all", "总体 + 所有对手"], ["overall", "仅总体"],
    ...opponents.map((name) => [`opponent/${encodeURIComponent(name)}`, name]),
  ];
  const opponent = choices.some(([key]) => key === previousOpponent) ? previousOpponent : "all";
  const step = selected.some((point) => String(point.step) === previousStep) ? previousStep : "latest";
  const steps = [["latest", "最新评估"], ...[...selected].reverse().map((point) => [String(point.step), `Update ${point.step}`])];
  const options = (values, chosen) => values.map(([value, label]) => `<option value="${f.escapeHtml(value)}"${value === chosen ? " selected" : ""}>${f.escapeHtml(label)}</option>`).join("");
  target.className = "evaluation-history";
  target.dataset.runId = runId;
  target.innerHTML = `
    <div class="evaluation-controls">
      <label>评估方式<select data-evaluation="mode">${options(modes.map((value) => [value, MODE_NAMES[value] || value]), mode)}</select></label>
      <label>对手<select data-evaluation="opponent">${options(choices, opponent)}</select></label>
      <label>胜平负明细<select data-evaluation="step">${options(steps, step)}</select></label>
    </div>
    <p class="evaluation-history-note">${f.integer(selected.length)} 个评估预算点 · Update ${f.integer(selected[0].step)}–${f.integer(selected.at(-1).step)}。悬停查看历史数值；胜率按胜局 / 总局数计算，现金仅作诊断。${mode.endsWith("_sampled") ? "同一模式复用固定种子，不计为额外独立样本；仅为自身初始化与随机锚点对照。" : ""}${selected.length === 1 ? "目前只有一次评估，后续评估完成后将自动连成折线。" : ""}</p>
    <div class="chart-grid evaluation-charts"></div>
    <div class="evaluation-history-detail"></div>`;
  const series = evaluationSeries(selected);
  const groups = [["overall", "总体", "#243640"], ...opponents.map((name, index) => [
    `opponent/${encodeURIComponent(name)}`, name, COLORS[index % COLORS.length],
  ])].filter(([key]) => opponent === "all" || opponent === key);
  const lines = (field) => groups.map(([key, label, color]) => [`${key}/${field}`, label, color]);
  const wdlGroup = opponent === "all" ? "overall" : opponent;
  const wdlLabel = choices.find(([key]) => key === wdlGroup)?.[1] || "总体";
  const configurations = [
    { title: "闭环胜率", unit: "%", note: "各 checkpoint 的完整比赛结果", lines: lines("win_rate") },
    { title: "闭环胜平负", unit: "局", note: `${wdlLabel} · 各次评估实际局数`, lines: [
      [`${wdlGroup}/wins`, "胜", COLORS[0]], [`${wdlGroup}/ties`, "平", COLORS[2]], [`${wdlGroup}/losses`, "负", COLORS[4]],
    ] },
    { title: "闭环终局现金", unit: "现金", note: "被评估模型的平均终局现金", lines: lines("mean_terminal_cash") },
    { title: "闭环终局现金差", unit: "现金差", zero: true, note: "被评估模型减对手的平均终局现金", lines: lines("mean_cash_difference") },
  ].map((config) => ({ ...config, stepLabel: "update" }));
  f.renderCharts(target.querySelector(".evaluation-charts"), "evaluation", { series }, configurations);
  const renderTable = () => {
    const value = target.querySelector('[data-evaluation="step"]').value;
    const point = selected.find((item) => String(item.step) === value) || selected.at(-1);
    const rows = [["overall", "总体", point.overall], ...Object.entries(point.opponents || {}).map(([name, values]) => [
      `opponent/${encodeURIComponent(name)}`, name, values,
    ])].filter(([key]) => opponent === "all" || opponent === key);
    target.querySelector(".evaluation-history-detail").innerHTML = `
      <p class="evaluation-history-note">Update ${f.integer(point.step)} · ${f.escapeHtml(MODE_NAMES[point.mode] || point.mode)}${point.temperature != null ? ` · T=${f.number(point.temperature, 4)}` : ""}</p>
      <div class="wdl-table-wrap"><table class="wdl-table"><thead><tr><th>对手</th><th>比赛</th><th>胜</th><th>平</th><th>负</th><th>胜率</th><th>终局现金</th><th>现金差</th></tr></thead><tbody>${rows.map(([, label, row]) => `<tr>
        <td>${f.escapeHtml(label)}</td><td>${f.integer(row.games)}</td><td class="w">${f.integer(row.wins)}</td><td>${f.integer(row.ties)}</td><td class="l">${f.integer(row.losses)}</td><td>${row.games > 0 ? f.percent(row.wins / row.games) : "—"}</td><td>${f.number(row.mean_terminal_cash)}</td><td>${f.number(row.mean_cash_difference)}</td>
      </tr>`).join("") || '<tr><td colspan="8">这次评估没有该对手的明细</td></tr>'}</tbody></table></div>
      <p class="evaluation-history-note">来源：${f.escapeHtml(point.source)}${!Object.keys(point.opponents || {}).length ? " · 此历史记录仅保存了总体结果" : ""}</p>`;
  };
  renderTable();
  target.querySelector('[data-evaluation="step"]').addEventListener("change", renderTable);
  for (const control of ["mode", "opponent"]) {
    target.querySelector(`[data-evaluation="${control}"]`).addEventListener("change", () => renderEvaluationHistory(target, history, runId, f));
  }
}
