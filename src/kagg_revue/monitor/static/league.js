export const activeMembers = (run) => Object.keys(run.learning?.members || { a: {}, bc: {}, spataro: {} });
const COLORS = ["#209f80", "#3398c5", "#c48a24"];

export function leagueLabel(name) {
  const sides = name.split("_vs_").map((member) => ({ a: "A", bc: "B+C", spataro: "SpaTaro" }[member] || member));
  return sides.length === 2 && sides[0] === sides[1] ? `${sides[0]} 自博弈` : sides.join(" vs ");
}

export const isSelfplay = (name) => { const sides = name.split("_vs_"); return sides.length === 2 && sides[0] === sides[1]; };

export function leagueCards(run, latest, f) {
  const { metricCard, integer, number, duration, bytes } = f;
  const live = run.learning || {}; const progress = run.progress || {};
  const members = activeMembers(run);
  const pretraining = live.phase === "demonstrations";
  const cards = pretraining ? [
    metricCard("当前阶段", `${leagueLabel(live.active_member || "a")} · BC`, "各模型分别完成监督预训练后进入联赛 PPO", 1),
    metricCard("示范 epoch", `${integer(live.epoch)} / ${integer(live.epochs)}`, `分片 ${integer(live.cursor)} / ${integer(live.total_shards)}`, 2),
    metricCard("当前分片 NLL", number(live.shard_nll, 4), `已学习 ${integer(live.rows)} 动作行`, 3),
    metricCard("在线 PPO 预算", integer(progress.target), "BC 不计入 PPO 轮数", 4),
  ] : [
    metricCard("联赛 PPO Update", `${integer(live.update ?? progress.current)} / ${integer(progress.target)}`, `预计剩余 ${duration(progress.eta_seconds)}`, 1),
    metricCard("恢复点", integer(live.checkpoint_update), `所有在训模型联合保存；每 ${integer(live.checkpoint_interval)} 轮`, 2),
    metricCard("训练对局", `${integer(live.games_per_update)} 场 / 轮`, `互战每对 ${integer(live.games_per_pair)} 场 · 自博弈每模型 ${integer(live.selfplay_games_per_member || 0)} 场`, 3),
    metricCard("累计在线比赛", integer(latest["rl/rollout/cumulative_physical_games"]), "双 GPU 的全局物理比赛数", 4),
    metricCard("Update 耗时", duration(latest["rl/system/update_elapsed_seconds"]), `${number(latest["rl/system/physical_games_per_second"], 2)} games/s；不含保存与评估`, 5),
    metricCard("单 GPU 显存峰值", bytes(latest["rl/system/cuda_peak_allocated_bytes"]), "两个 rank 中的最大已分配显存", 6),
  ];
  if (!pretraining && live.selfplay_games_per_member > 0) {
    cards.push(metricCard("本轮自博弈", `${integer(latest["rl/league/selfplay_physical_games"])} 场`, "在训模型各自控制双方；每席位半权重", cards.length + 1));
  }
  if (live.script_opponents?.length) {
    cards.push(metricCard("Native 脚本对手", `${integer(live.script_opponents.length)} 个`, `每模型对每个脚本 ${integer(live.games_per_script_per_member)} 场`, cards.length + 1));
  }
  for (const name of members) {
    const bc = live.pretraining?.[name] || {};
    const stage = bc.completed_epochs ? `${integer(bc.completed_epochs)} / ${integer(live.epochs)} epoch`
      : pretraining && live.active_member === name ? "训练中" : "等待训练";
    cards.push(metricCard(`${leagueLabel(name)} · BC`, stage,
      `留出 NLL ${number(bc.selection_nll, 4)} · ${integer(bc.rows)} 动作行`, cards.length + 1));
  }
  return cards;
}

export function leagueChartConfigurations(run, metrics) {
  const members = activeMembers(run);
  const names = Object.keys(metrics?.latest || {})
    .filter((tag) => tag.startsWith("rl/league/pairs/") && tag.endsWith("/games"))
    .map((tag) => tag.split("/")[3]).filter((name) => name.split("_vs_").every((side) => side !== "a" || members.includes("a"))).sort();
  const pairs = names.filter((name) => !isSelfplay(name));
  const selfplay = names.filter(isSelfplay);
  const chart = (title, group, unit, note, lines, extra = {}) => ({
    title, group, unit, note, percent: unit === "比例", bytes: unit === "bytes", ...extra,
    lines: lines.map(([tag, label], index) => [tag, label, COLORS[index % COLORS.length]]),
  });
  const memberLines = (field) => members.map((name) => [`rl/league/optimization/${name}/${field}`, leagueLabel(name)]);
  return [
    chart("联赛配对胜率", "opponents", "比例", "每条曲线表示配对名称左侧模型的胜率；训练采样统计", pairs.map((name) => [`rl/league/pairs/${name}/win_rate`, leagueLabel(name)]), { overview: true }),
    chart("配对终局现金", "opponents", "现金", "每个配对分别显示双方的平均现金", pairs.flatMap((name) => name.split("_vs_").map((member, index) => [`rl/league/pairs/${name}/mean_cash_${index ? "right" : "left"}`, `${leagueLabel(name)} · ${leagueLabel(member)}`]))),
    chart("配对现金差", "opponents", "现金", "配对左侧模型减右侧模型；正值表示左侧领先", pairs.map((name) => [`rl/league/pairs/${name}/mean_cash_difference`, leagueLabel(name)]), { zero: true }),
    ...[
      ["自博弈终局现金", "现金", "双方终局现金先取均值，再按物理场数统计", "mean_terminal_cash"],
      ["自博弈现金差绝对值", "现金", "每场两席位现金差的绝对值；不会因合并双方而抵消为零", "mean_absolute_cash_difference"],
      ["自博弈平局率", "比例", "平局数 / 物理场数；不合并双席位生成约 50% 胜率", "tie_rate"],
    ].filter(() => selfplay.length).map(([title, unit, note, field], index) => chart(title, "opponents", unit, note,
      selfplay.map((name) => [`rl/league/pairs/${name}/${field}`, leagueLabel(name)]), { overview: index === 0 })),
    chart("各模型终局现金", "overview", "现金", "包含互战、自博弈与脚本对战，按实际场数加权；自博弈先平均双方现金", members.map((name) => [`rl/league/members/${name}/mean_terminal_cash`, leagueLabel(name)]), { overview: true }),
    chart("更新前最大 KL", "diagnostics", "KL", "每个模型的最大前缀条件 KL", memberLines("maximum_prefix_kl")),
    chart("已接受更新后 KL", "diagnostics", "KL", "各模型已接受的优化步；取两 rank 的最大 KL", memberLines("maximum_accepted_post_step_kl")),
    chart("价值损失", "diagnostics", "损失", "各模型的 Critic 分别显示；DDP 副本取均值", memberLines("value_loss")),
    chart("Actor 学习率", "diagnostics", "学习率", "各模型的 Actor 优化器的实际学习率", memberLines("actor_learning_rate")),
    chart("Actor 优化步数", "diagnostics", "步", "同步优化步数；双 GPU 不重复累计", memberLines("actor_steps")),
    chart("Critic 优化步数", "diagnostics", "步", "各模型本轮已完成的 Critic 更新", memberLines("critic_steps")),
    chart("拒绝的 Actor 步数", "diagnostics", "步", "超出 KL 约束而回滚的优化步数", memberLines("rejected_actor_steps")),
    chart("Update 阶段耗时", "resources", "秒", `取最慢 rank；优化耗时包含 ${members.length} 个在训模型`, [
      ["rl/system/update_elapsed_seconds", "Update"], ["rl/rollout/elapsed_seconds", "采样"], ["rl/system/optimization_seconds", "优化"],
    ], { overview: true }),
    chart("各模型优化耗时", "resources", "秒", "每个模型的 learner 耗时；取两个 rank 的最大值", memberLines("learner_seconds")),
    chart("物理比赛吞吐", "resources", "games/s", "全局物理比赛数除以最慢 rank 耗时", [
      ["rl/system/physical_games_per_second", "Update"], ["rl/rollout/games_per_second", "采样"],
    ]),
    chart("GPU 内存峰值", "resources", "bytes", "每个 rank 本轮已分配显存", [0, 1].map((rank) => [`rl/league/ranks/${rank}/peak_allocated_bytes`, `Rank ${rank}`])),
  ];
}

export function leaguePairTable(pairs, f) {
  const { escapeHtml, integer, number, percent } = f;
  const rows = Object.entries(pairs).map(([name, panel]) => `<tr>
    <td>${escapeHtml(leagueLabel(name))}${isSelfplay(name) ? "（席位 0 vs 1）" : ""}</td><td>${integer(panel.games)}</td>
    <td>${integer(panel.wins)} · ${integer(panel.ties)} · ${integer(panel.losses)}</td>
    <td>${percent(panel.win_rate)}</td><td>${number(panel.mean_cash_left)}</td>
    <td>${number(panel.mean_cash_right)}</td><td>${number(panel.mean_cash_difference)}</td></tr>`).join("");
  return `<div class="opponent-table-wrap"><table class="opponent-table"><thead><tr>
    <th>配对（左 vs 右）</th><th>比赛</th><th>左方胜 · 平 · 负</th><th>左方胜率</th>
    <th>左方现金</th><th>右方现金</th><th>左减右现金差</th></tr></thead><tbody>${rows}</tbody></table></div>
    ${Object.keys(pairs).some(isSelfplay) ? '<p>自博弈每场只统计一次，左方为席位 0、右方为席位 1；两个席位都进入训练，各占半份权重。</p>' : ""}`;
}

export function leaguePairs(latest, members = null) {
  const output = {};
  for (const [tag, value] of Object.entries(latest || {})) {
    if (!tag.startsWith("rl/league/pairs/")) continue;
    const [, , , name, field] = tag.split("/");
    if (members && name.split("_vs_").some((side) => ["a", "bc", "spataro"].includes(side) && !members.includes(side))) continue;
    (output[name] ||= {})[field] = value;
  }
  return output;
}

export function leagueEvaluationSummary(point, f) {
  const mutual = Object.entries(point.pairs).filter(([name]) => !isSelfplay(name));
  const selfplay = Object.entries(point.pairs).filter(([name]) => isSelfplay(name));
  return `<div><h3>最近固定种子联赛评估 · U${f.integer(point.step)}</h3><p>${f.integer(point.physical_games)} 场；配对左侧模型胜率：</p><p>${mutual.map(([name, panel]) => `${f.escapeHtml(leagueLabel(name))} ${f.percent(panel.win_rate)}`).join(" · ")}</p>
    ${selfplay.length ? `<p>自博弈：${selfplay.map(([name, panel]) => `${f.escapeHtml(leagueLabel(name))} ${f.integer(panel.games)} 场`).join(" · ")}</p>` : ""}
    <p>模型随训练共同变化；脚本对手保持固定。</p></div>`;
}

export function renderLeagueEvaluation(target, points, f) {
  const selected = target.querySelector("select")?.value;
  const latest = points.at(-1);
  target.className = "evaluation-panel";
  target.innerHTML = `<label>固定种子联赛评估 <select>${points.map((point) => `<option value="${point.step}">Update ${f.integer(point.step)}</option>`).join("")}</select></label><div class="league-evaluation-result"></div>`;
  const select = target.querySelector("select");
  select.value = points.some((point) => String(point.step) === selected) ? selected : String(latest.step);
  const render = () => {
    const point = points.find((entry) => String(entry.step) === select.value);
    target.querySelector(".league-evaluation-result").innerHTML = leagueEvaluationSummary(point, f) + leaguePairTable(point.pairs, f);
  };
  select.addEventListener("change", render); render();
}
