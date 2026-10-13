import { apprenticeCharts } from "./apprentice.js";

export function branchCards(run, metrics, f) {
  const v = (tag) => metrics?.latest?.[`rl/${tag}`];
  return [
    f.metricCard("状态分支迭代", `${f.integer(run.progress.current)} <small>/ ${f.integer(run.progress.target)}</small>`, `本轮 ${f.integer(v("optimization/actor_steps"))} 次整网 Adam 更新`, 1),
    f.metricCard("累计梯度更新", f.integer(v("optimization/optimizer_steps")), `学习率 ${v("optimization/learning_rate")}`, 2),
    f.metricCard("搜索发现改善的状态", `${f.integer(v("search/improved_roots"))} <small>/ ${f.integer(v("search/roots"))}</small>`, `脚本 ${f.integer(v("search/script_improved_roots"))} · self-play ${f.integer(v("search/selfplay_improved_roots"))} · 仅训练标签`, 3),
    f.metricCard("方案偏好损失", f.number(v("optimization/preference_loss"), 6), `编码器本轮变化 ${f.number(v("optimization/encoder_parameter_delta_l2"), 6)} · 拟合诊断`, 4),
    ...[["scripts", "学生对脚本"], ["neural", "学生对原 PPO"]].map(([population, label], i) => {
      const w = v(`evaluation/${population}/student/wins`), d = v(`evaluation/${population}/student/ties`), l = v(`evaluation/${population}/student/losses`);
      return f.metricCard(`${label} · 胜 / 平 / 负`, `${f.integer(w)} / ${f.integer(d)} / ${f.integer(l)}`, "最近独立 argmax 完整比赛 · 无搜索协助", i + 5, "", f.wdlStrip(w, d, l));
    }),
    f.metricCard("端到端完成对局", `${f.number(v("system/physical_games_per_second"))} <small>games/s</small>`, `含复用前缀的分支、学习及评估 · ${f.duration(v("system/update_elapsed_seconds"))}`, 7),
  ];
}

export function branchCharts() {
  return [
    ...apprenticeCharts().filter((chart) => !["专家分布拟合", "完整比赛吞吐"].includes(chart.title)),
    {title: "具有胜负改善的状态", note: "相同根状态、对手与后续策略下的配对 WDL；这是训练标签数量", unit: "状态", lines: [["rl/search/script_improved_roots", "脚本", "#22b99a"], ["rl/search/selfplay_improved_roots", "self-play", "#7d9fff"]]},
    {title: "方案偏好损失", note: "基于终局 WDL 的相对方案概率；不代表模型比赛胜率", unit: "loss", lines: [["rl/optimization/preference_loss", "偏好损失", "#7d9fff"]]},
    {title: "学生相对训练起点", note: "同种子、同席位的 W−L 差；学生独立执行", unit: "W−L 差", zero: true, lines: [["rl/evaluation/scripts/paired_to_initial/wdl_gain", "脚本", "#22b99a"], ["rl/evaluation/neural/paired_to_initial/wdl_gain", "原 PPO 对手", "#7d9fff"]]},
  ];
}

export function renderBranch(detail, f) {
  document.querySelector("#search-section").classList.remove("hidden");
  document.querySelector("#search-section h2").textContent = "状态分支搜索与整网学习";
  const ctx = detail.metrics?.context || {};
  const phases = {prefix: "学生公共前缀", continuation: "分支完整终局比较", learn: "整网偏好学习", evaluate: "独立学生与冻结对照比赛", checkpoint: "保存权重及优化器", complete: "本轮完成"};
  const live = (detail.search_progress || []).map((r) => `<div class="search-live-row"><strong>Rank ${f.integer(r.rank)} · Update ${f.integer(r.generation)}</strong><span>${f.escapeHtml(phases[r.phase] || r.phase)} · ${f.integer(r.completed)} / ${f.integer(r.total)}</span></div>`).join("");
  const target = document.querySelector("#search-panel");
  const sameRun = target.dataset.runId === detail.run.id;
  if (sameRun && target.dataset.generation === String(ctx.update)) {
    target.querySelector(".search-live").innerHTML = live;
    return;
  }
  const open = sameRun && target.querySelector("details")?.open;
  const candidates = new Map();
  for (const worker of ctx.branch_workers || []) for (const row of worker.search.candidates) {
    const entry = candidates.get(row.candidate) || {candidate: row.candidate, scripts: 0, selfplay: 0};
    for (const key of ["scripts", "selfplay"]) entry[key] += row[key].wdl_gain;
    candidates.set(row.candidate, entry);
  }
  target.innerHTML = `<div class="search-live">${live}</div><p class="search-note">每个状态的候选由模型单独生成；原方案作为配对对照。下面的候选编号仅表示各状态的抽样槽位，不是一套可部署策略。学生通过完整方案的偏好信号更新所有网络参数；下方模型表现来自另外的独立完整比赛。</p><details${open ? " open" : ""}><summary>本轮分支候选 · Update ${f.integer(ctx.update)}</summary><div class="wdl-table-wrap"><table class="wdl-table"><thead><tr><th>候选槽位</th><th>脚本 W−L 差</th><th>self-play W−L 差</th></tr></thead><tbody>${[...candidates.values()].map((r) => `<tr><td>${r.candidate === 0 ? "原方案" : f.integer(r.candidate)}</td><td>${f.number(r.scripts, 0)}</td><td>${f.number(r.selfplay, 0)}</td></tr>`).join("")}</tbody></table></div></details>`;
  target.dataset.runId = detail.run.id;
  target.dataset.generation = String(ctx.update);
}
