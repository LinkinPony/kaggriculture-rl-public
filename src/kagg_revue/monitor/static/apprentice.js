const C = ["#22b99a", "#ff705d", "#7d9fff", "#e0a72e"];
export function apprenticeCards(run, metrics, f) {
  const v = (tag) => metrics?.latest?.[`rl/${tag}`];
  const fitting = metrics?.context?.learning?.performed !== false;
  return [
    f.metricCard("搜索—学习迭代", `${f.integer(run.progress.current)} <small>/ ${f.integer(run.progress.target)}</small>`, fitting ? `本轮整网学习 · ${f.integer(v("optimization/actor_steps"))} 次 Adam 更新` : "本轮仅搜索 · 专家学习预算已用完", 1),
    f.metricCard("累计梯度更新", f.integer(v("optimization/optimizer_steps")), `学习率 ${v("optimization/learning_rate")}`, 2),
    f.metricCard("专家 KL 损失", f.number(v("optimization/teacher_kl_loss"), 7), fitting ? `条件动作一致率 ${f.percent(v("optimization/conditional_action_agreement"))} · 拟合诊断` : "最近学习轮的拟合诊断 · 本轮未拟合", 3),
    f.metricCard("编码器参数变化", f.number(v("optimization/encoder_parameter_delta_l2"), 6), "本轮编码器参数差的 L2 范数 · 验证主干实际更新", 4),
    ...[["scripts", "学生对脚本"], ["neural", "学生对原 PPO"]].map(([population, label], i) => {
      const w = v(`evaluation/${population}/student/wins`), d = v(`evaluation/${population}/student/ties`), l = v(`evaluation/${population}/student/losses`);
      return f.metricCard(`${label} · 胜 / 平 / 负`, `${f.integer(w)} / ${f.integer(d)} / ${f.integer(l)}`, fitting ? "独立执行 argmax · 新种子选择集" : "最近学习轮的评估 · 学生权重未变", i + 5, "", f.wdlStrip(w, d, l));
    }),
    f.metricCard("端到端吞吐", `${f.number(v("system/physical_games_per_second"))} <small>games/s</small>`, `包含搜索、采集、梯度学习和评估 · ${f.duration(v("system/update_elapsed_seconds"))}`, 7),
  ];
}

export function apprenticeCharts() {
  return [
    ...[["scripts", "脚本"], ["neural", "原 PPO"]].map(([key, label]) => ({
      title: `学生对${label} · 胜平负`, note: "学生独立 argmax；新种子完整配对选择集", unit: "局",
      lines: ["wins", "ties", "losses"].map((metric, i) => [`rl/evaluation/${key}/student/${metric}`, ["胜", "平", "负"][i], [C[0], C[3], C[1]][i]]),
    })),
    ...[["scripts", "脚本"], ["neural", "原 PPO"]].map(([key, label]) => ({
      title: `${label}面板 · 学生相对专家`, note: "同种子、同席位；学生 W−L 减搜索专家 W−L，0 表示净胜负持平", unit: "W−L 差", zero: true,
      lines: [[`rl/evaluation/${key}/paired_to_expert/wdl_gain`, "相对专家", C[2]], [`rl/evaluation/${key}/paired_to_origin/wdl_gain`, "相对原 PPO", C[0]]],
    })),
    {title: "专家分布拟合", note: "学生实际访问状态上的条件 KL；不代表闭环比赛质量", unit: "KL", lines: [["rl/optimization/teacher_kl_loss", "专家 KL", C[2]]]},
    {title: "编码器实际更新", note: "每轮编码器参数变化的 L2 范数", unit: "L2", lines: [["rl/optimization/encoder_parameter_delta_l2", "编码器变化", C[0]]]},
    {title: "梯度更新次数", note: "真实 Adam optimizer.step 累计次数", unit: "次", lines: [["rl/optimization/optimizer_steps", "累计梯度更新", C[0]]]},
    {title: "更新阶段耗时", note: "整轮 wall time；并行采集/学习取最慢 rank", unit: "秒", lines: [
      ["rl/system/update_elapsed_seconds", "整轮", C[1]], ["rl/rollout/elapsed_seconds", "采集", C[2]],
      ["rl/system/optimization_seconds", "梯度学习", C[0]], ["rl/system/search_seconds", "专家搜索", C[3]],
    ]},
    {title: "完整比赛吞吐", note: "端到端包含学习与评估；采集仅统计实际采集的物理比赛", unit: "games/s", lines: [["rl/system/physical_games_per_second", "端到端", C[0]], ["rl/rollout/games_per_second", "采集", C[2]]]},
    {title: "显存峰值", note: "各 rank 最大值；Reserved 包含 CUDA Graph 内存池", unit: "bytes", bytes: true, lines: [["rl/system/cuda_peak_reserved_bytes", "Reserved", C[3]], ["rl/system/cuda_peak_allocated_bytes", "Allocated", C[0]]]},
  ];
}

export function renderApprentice(detail, f) {
  document.querySelector("#search-section").classList.remove("hidden");
  document.querySelector("#search-section h2").textContent = "搜索与梯度学习进度";
  const ctx = detail.metrics?.context || {};
  const phases = {collect: "学生整局采集", learn: "整网梯度学习", evaluate: "学生 / 专家 / 原 PPO 比赛", checkpoint: "保存模型与优化器", control: "搜索基线", search: "搜索候选", selection: "专家新种子复核", complete: "本轮完成"};
  const live = (detail.search_progress || []).map((row) => `<div class="search-live-row"><strong>Rank ${f.integer(row.rank)} · Update ${f.integer(row.generation)}</strong><span>${f.escapeHtml(phases[row.phase] || row.phase)} · ${f.integer(row.completed)} / ${f.integer(row.total)}</span></div>`).join("");
  const target = document.querySelector("#search-panel");
  const sameRun = target.dataset.runId === detail.run.id;
  if (sameRun && target.dataset.generation === String(ctx.update)) {
    target.querySelector(".search-live").innerHTML = live;
    return;
  }
  const keepOpen = sameRun && target.querySelector("details")?.open;
  const search = ctx.search;
  const candidates = search?.policy_search?.search?.candidates || [];
  const learning = ctx.learning;
  const budget = learning?.fits_per_expert == null ? "" : `<br>当前专家已学习 ${f.integer(learning.fits)} / ${f.integer(learning.fits_per_expert)} 轮；${learning.performed ? "本轮完成梯度更新" : "本轮跳过重复拟合，继续寻找新专家"}。`;
  target.innerHTML = `<div class="search-live">${live}</div><p class="search-note search-identity">当前专家：${f.escapeHtml(ctx.expert?.path || detail.inputs?.teacher?.path)}<br>学生只通过梯度更新参数；搜索在独立专家副本上进行。下方模型面板分别报告 student、expert、origin。${budget}</p>
    <details${keepOpen ? " open" : ""}><summary>最近专家搜索 · ${search ? `Update ${f.integer(search.update)} · ${search.expert_replaced ? "已更换专家" : "保留原专家"}` : "先学习已验证专家"}</summary>
    <div class="wdl-table-wrap"><table class="wdl-table"><thead><tr><th>候选</th><th>扰动幅度</th><th>脚本 W−L 差</th><th>父模型对手 W−L 差</th><th>搜索筛选</th></tr></thead><tbody>${candidates.map((candidate) => `<tr><td>${f.integer(candidate.candidate)}</td><td>${f.number(candidate.scale, 3)}</td><td>${f.number(candidate.scripts_wdl_gain, 0)}</td><td>${f.number(candidate.neural_wdl_gain, 0)}</td><td>${candidate.eligible ? "通过" : "未通过"}</td></tr>`).join("")}</tbody></table></div></details>`;
  target.dataset.runId = detail.run.id;
  target.dataset.generation = String(ctx.update);
}
