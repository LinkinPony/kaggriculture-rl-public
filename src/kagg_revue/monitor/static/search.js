// Policy-space search has generations and direct match outcomes, without learner losses.
const C = ["#22b99a", "#ff705d", "#7d9fff", "#e0a72e"];
const line = (tag, label, color = C[0]) => [`search/${tag}`, label, color];
export const SEARCH_CHARTS = [
  ...[["scripts", "脚本对手"], ["neural", "固定参考模型"]].map(([key, label]) => ({
    title: `${label} · 保留策略胜平负`, unit: "局", stepLabel: "代",
    note: "新种子复核集（参与策略选择）；各代种子不同，需结合配对净改善看",
    lines: [line(`selection/${key}/wins`, "胜"), line(`selection/${key}/ties`, "平", C[3]), line(`selection/${key}/losses`, "负", C[1])],
  })),
  {
    title: "配对胜负净改善", unit: "W−L 差", zero: true, stepLabel: "代",
    note: "保留策略减父模型；同代、同种子、同对手和席位。0 表示净胜负未变",
    lines: [line("selection/paired_scripts/wdl_gain", "脚本"), line("selection/paired_neural/wdl_gain", "固定参考", C[2])],
  },
  {
    title: "候选通过与采纳", unit: "个", stepLabel: "代",
    note: "通过搜索筛选的候选、进入新种子复核的候选、本代实际采纳（0/1）",
    lines: [line("counts/eligible", "搜索通过", C[2]), line("counts/finalists", "进入复核", C[3]), line("counts/accepted", "本代采纳")],
  },
  {
    title: "累计策略采纳", unit: "次", stepLabel: "代",
    note: "实际替换父模型的次数；保留原策略时不增加",
    lines: [line("counts/accepted_total", "累计采纳")],
  },
  {
    title: "终局现金诊断", unit: "现金", stepLabel: "代",
    note: "保留策略在复核集的平均现金；不参与候选选择",
    lines: [line("selection/scripts/mean_cash", "脚本面板", C[3]), line("selection/neural/mean_cash", "固定参考面板", C[2])],
  },
  {
    title: "端到端比赛吞吐", unit: "games/s", stepLabel: "代",
    note: "每场物理比赛计一次；含双卡搜索、复核与检查点写入",
    lines: [line("timing/physical_games_per_second", "完整代")],
  },
  {
    title: "每代阶段耗时", unit: "秒", stepLabel: "代",
    note: "搜索取并行 rank 的最长耗时；复核在主 rank 执行",
    lines: [line("timing/generation_seconds", "整代", C[1]), line("ranks/elapsed_seconds", "搜索", C[2]), line("timing/selection_seconds", "复核"), line("timing/checkpoint_seconds", "存盘", C[3])],
  },
  {
    title: "搜索热路径", unit: "秒", stepLabel: "代",
    note: "各阶段取 rank 最大值；冷启动 capture 单列在最新诊断中",
    lines: [line("ranks/inference_seconds", "推理", C[2]), line("ranks/native_seconds", "Native", C[1]), line("ranks/encoding_seconds", "编码")],
  },
];

export function searchCharts(metrics) {
  const tags = Object.keys(metrics?.series || {});
  return [...SEARCH_CHARTS, ...[
    ["逐脚本胜率", "search/opponents/", "/win_rate", "比例", false],
    ["各设备显存峰值", "search/rank_", "/peak_reserved_bytes", "bytes", true],
  ].map(([title, prefix, suffix, unit, bytes]) => ({
    title, unit, bytes, stepLabel: "代",
    note: bytes ? "Torch reserved（包含 CUDA Graph 内存池）；当前进程总显存见计算资源" : "保留策略的新种子复核结果；未混入搜索候选成绩",
    lines: tags.filter((tag) => tag.startsWith(prefix) && tag.endsWith(suffix))
      .map((tag, index) => [tag, tag.split("/").at(-2), C[index % C.length]]),
  }))];
}

export function searchCards(run, metrics, f) {
  const m = metrics?.latest || {};
  const v = (tag) => m[`search/${tag}`];
  const accepted = v("counts/accepted");
  return [
    f.metricCard("已完成代数", `${f.integer(run.progress.current)} <small>/ ${f.integer(run.progress.target)}</small>`, `平均每代 ${f.duration(run.progress.mean_step_seconds)}`, 1),
    f.metricCard("本代策略决策", accepted === 1 ? "采纳新策略" : accepted === 0 ? "保留父模型" : "—", `累计采纳 ${f.integer(v("counts/accepted_total"))} 次`, 2),
    ...[["scripts", "脚本"], ["neural", "固定参考"]].map(([key, label], index) => {
      const w = v(`selection/${key}/wins`), d = v(`selection/${key}/ties`), l = v(`selection/${key}/losses`);
      return f.metricCard(`${label}复核 · 胜 / 平 / 负`, `${f.integer(w)} / ${f.integer(d)} / ${f.integer(l)}`, `保留策略 · 配对 W−L 净改善 ${f.number(v(`selection/paired_${key}/wdl_gain`), 0)}`, index + 3, "", f.wdlStrip(w, d, l));
    }),
    f.metricCard("通过搜索筛选", `${f.integer(v("counts/eligible"))} <small>/ ${f.integer(v("counts/candidates"))}</small>`, `${f.integer(v("counts/finalists"))} 个候选进入新种子复核`, 5),
    f.metricCard("端到端吞吐", `${f.number(v("timing/physical_games_per_second"))} <small>games/s</small>`, `本代 ${f.integer(v("timing/physical_games"))} 场完整比赛`, 6),
  ];
}

export function renderSearch(detail, f) {
  const isSearch = detail.run.kind === "search";
  document.querySelector("#search-section").classList.toggle("hidden", !isSearch);
  if (!isSearch) return;
  const ctx = detail.metrics?.context || {};
  const selected = ctx.selection?.selected;
  const completedGeneration = ctx.generation || 0;
  const live = detail.search_progress || [];
  const phaseNames = { control: "父模型基线", search: "候选搜索", selection: "新种子复核", checkpoint: "保存检查点", complete: "本代已完成" };
  const progress = live.length ? live.map((row) => {
    const age = Math.max(0, Date.now() / 1000 - row.updated_at);
    const previous = row.generation < Math.max(...live.map((item) => item.generation));
    const waiting = row.phase === "search" && row.completed === row.total;
    const label = waiting ? "搜索完成，等待主 rank 复核" : phaseNames[row.phase] || row.phase;
    return `<div class="search-live-row"><strong>Rank ${f.integer(row.rank)} · 第 ${f.integer(row.generation)} 代</strong><span>${f.escapeHtml(label)} · ${f.integer(row.completed)} / ${f.integer(row.total)}${previous ? "（上一代记录）" : ""}</span><span>${f.duration(age)} 前${detail.run.status !== "running" ? " · 训练未运行" : age > 180 ? " · 进度记录较旧" : ""}</span></div>`;
  }).join("") : '<p class="search-note">这段历史没有逐候选进度；下方展示完整代结果。</p>';
  const target = document.querySelector("#search-panel");
  const sameRun = target.dataset.runId === detail.run.id;
  if (sameRun && target.dataset.generation === String(completedGeneration)) {
    target.querySelector(".search-live").innerHTML = progress;
    return;
  }
  const keepOpen = sameRun && target.querySelector("details")?.open;
  const scrollOffsets = sameRun
    ? [...target.querySelectorAll(".wdl-table-wrap")].map((table) => table.scrollLeft) : [];
  const rows = (ctx.search?.candidates || []).map((candidate) => `<tr>
    <td>${f.integer(candidate.candidate)}</td><td>${f.number(candidate.scale, 3)}</td>
    <td>${f.number(candidate.scripts_wdl_gain, 0)}</td><td>${f.number(candidate.neural_wdl_gain, 0)}</td>
    <td>${candidate.eligible ? "通过" : "未通过"}</td>
    <td>${selected?.candidate === candidate.candidate ? "已采纳" : (ctx.selection?.candidates || []).some((item) => item.candidate === candidate.candidate) ? "复核未采纳" : "—"}</td>
  </tr>`).join("");
  const finalists = (ctx.selection?.candidates || []).map((candidate) => `<tr><td>${f.integer(candidate.candidate)}</td>${["scripts", "neural"].map((name) => {
    const paired = candidate[`paired_${name}`] || {};
    return `<td>${f.integer(paired.better)} / ${f.integer(paired.same)} / ${f.integer(paired.worse)}</td><td>${f.number(paired.wdl_gain, 0)}</td>`;
  }).join("")}</tr>`).join("");
  target.innerHTML = `<div class="search-live">${progress}</div>
    <p class="search-note">第 ${f.integer(completedGeneration)} 代完整结果 · 搜索对手：脚本 + 当代父模型；复核对手：脚本 + 固定参考模型。候选需两组 W−L 均不下降、且总计改善，才能替换父模型。</p>
    <details${keepOpen ? " open" : ""}><summary>查看本代 ${f.integer(ctx.search?.candidates?.length)} 个候选</summary>
      <p class="search-note">下表为搜索集相对父模型的 W−L 差；这些成绩不代表最终保留策略。</p>
      <div class="wdl-table-wrap"><table class="wdl-table"><thead><tr><th>候选</th><th>扰动幅度</th><th>脚本 W−L 差</th><th>父模型对手 W−L 差</th><th>搜索筛选</th><th>最终决策</th></tr></thead><tbody>${rows}</tbody></table></div>
      <p class="search-note">新种子复核：better / same / worse 统计逐局胜平负变化，W−L 差是净胜负变化。</p>
      <div class="wdl-table-wrap"><table class="wdl-table"><thead><tr><th>候选</th><th>脚本 better / same / worse</th><th>W−L 差</th><th>参考 better / same / worse</th><th>W−L 差</th></tr></thead><tbody>${finalists || '<tr><td colspan="5">没有候选进入复核，保留父模型</td></tr>'}</tbody></table></div>
    </details>`;
  target.dataset.runId = detail.run.id;
  target.dataset.generation = String(completedGeneration);
  target.querySelectorAll(".wdl-table-wrap").forEach((table, index) => {
    table.scrollLeft = scrollOffsets[index] || 0;
  });
}

export function renderSearchEvaluation(detail, f) {
  const ctx = detail.metrics?.context || {};
  const selection = ctx.selection || {};
  const reference = detail.inputs?.reference || {};
  const panels = [
    ["脚本总体 · 保留策略", selection.scripts], ["脚本总体 · 父模型", selection.baseline_scripts],
    ["固定参考 · 保留策略", selection.neural], ["固定参考 · 父模型", selection.baseline_neural],
    ...Object.entries(selection.scripts?.opponents || {}).map(([name, panel]) => [`${name} · 保留策略`, panel]),
  ];
  document.querySelector("#evaluation-asof").textContent = `第 ${f.integer(ctx.generation)} 代 · selection seed ${f.integer(selection.seed_start)}`;
  const target = document.querySelector("#evaluation-panel");
  target.className = "evaluation-panel";
  const short = (hash) => hash ? String(hash).slice(0, 12) : "未记录";
  target.innerHTML = `<div class="evaluation-head"><div class="decision"><div class="decision-icon retain">↺</div><div><strong>训练复核集 · ${selection.selected ? "采纳候选 " + f.integer(selection.selected.candidate) : "保留父模型"}</strong><span>参与训练策略选择；不是独立 confirmation。此处未验证部署时限，正式 incumbent 未改变。</span></div></div></div>
    <div class="wdl-table-wrap"><table class="wdl-table"><thead><tr><th>完整比赛面板</th><th>胜</th><th>平</th><th>负</th><th>终局现金</th><th>现金差</th></tr></thead><tbody>${panels.filter(([, panel]) => panel).map(([name, panel]) => `<tr><td>${f.escapeHtml(name)}</td><td class="w">${f.integer(panel.wins)}</td><td>${f.integer(panel.ties)}</td><td class="l">${f.integer(panel.losses)}</td><td>${f.number(panel.mean_cash)}</td><td>${f.number(panel.mean_cash_difference)}</td></tr>`).join("")}</tbody></table></div>
    <div class="search-note search-identity">当前权重：${f.escapeHtml(ctx.checkpoint?.path || "未记录")} · SHA ${f.escapeHtml(short(ctx.checkpoint?.sha256))}<br>父模型：${f.escapeHtml(ctx.parent || "未记录")} · SHA ${f.escapeHtml(short(ctx.parent_sha256))}<br>固定参考：${f.escapeHtml(reference.path || "未记录")} · SHA ${f.escapeHtml(short(reference.sha256))}<br>本代源码：${f.escapeHtml(short(ctx.source_revision))} · 全部策略 argmax 执行</div>`;
}
