const prefix = "rl/land/quadrants/";
const names = ["NW", "NE", "SW", "SE"];

export function quadrantCards(latest, { metricCard, percent, integer }) {
  const count = latest["rl/land/trajectories"];
  if (!Number.isFinite(count)) return [];
  return [
    metricCard("SE 购地率", percent(latest[`${prefix}SE/unlocked_rate`]), `本轮 ${integer(count)} 条学习方轨迹；不含冻结对手席位`, 13),
    metricCard("SE 生产使用率", percent(latest[`${prefix}SE/productive_rate`]), `曾种植或养殖；买后未使用 ${percent(latest[`${prefix}SE/unused_rate`])}`, 14),
  ];
}

export function quadrantCharts(metrics, chart) {
  if (!Number.isFinite(metrics?.latest?.["rl/land/trajectories"])) return [];
  const lines = (field, quadrants = names) => quadrants.map((name) => [`${prefix}${name}/${field}`, name]);
  const note = "完整训练对局中学习方席位的比例；自博弈双方计入，冻结对手不计入；PFSP 对手变化会影响结果";
  return [
    { ...chart("象限购地率", note, "比例", lines("unlocked_rate", names.slice(1))), overview: true },
    { ...chart("象限生产使用率", `曾有作物或已放入动物的设施；${note}`, "比例", lines("productive_rate")), overview: true },
    chart("买地后未使用率", `已解锁但整局未种植或养殖；${note}`, "比例", lines("unused_rate", names.slice(1))),
    chart("象限最大生产格数", "逐条学习方轨迹取整局最大值后平均；未使用计 0，空设施不计生产", "格", lines("mean_peak_productive_tiles")),
    chart("购地平均回合", "仅在买到该象限的轨迹中取平均；未购买时无数据，回合 1 表示第一次动作结算后", "回合", lines("mean_unlock_step", names.slice(1))),
    { ...chart("象限统计耗时", "每轮采样结束后批量汇总，包含最终状态编码；双卡取较慢者", "秒", [["rl/rollout/quadrant_monitor_seconds", "统计耗时"]]), group: "resources" },
  ];
}
