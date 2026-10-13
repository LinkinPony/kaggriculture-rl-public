import assert from "node:assert/strict";
import test from "node:test";
import { currentPopulationMetrics, pfspTable, learningChartConfigurations } from "../learning.js";
import { explorerConfigurations } from "../explorer.js";

test("PFSP pending allocations retain last committed metrics and show history", () => {
  const latest = { "rl/pfsp/enabled": 1, "rl/rollout/opponents/self_play/games": 32,
    "rl/rollout/opponents/history/games": 32, "rl/rollout/opponents/router_95/games": 16 };
  const live = { population_games: { self_play: 32, historical_self_play: 32, router_95: 24 },
    pfsp: { enabled: true, update: 641, history: [{ update: 0, games: 32, score: 0.5, probability: 0.2 }] } };
  assert.equal(currentPopulationMetrics(latest, live), latest);
  assert.deepEqual(currentPopulationMetrics({ ...latest, "rl/pfsp/enabled": 0 }, live), {});
  const html = pfspTable(live, { integer: String, percent: (value) => `${100 * value}%` });
  assert.match(html, /BC 终点/);
  assert.match(html, /20%/);
  assert.match(html, /U641/);
  const charts = learningChartConfigurations({ learning: live }, { latest });
  assert.ok(explorerConfigurations(charts, { view: "overview", opponent: "all" }).some((chart) => chart.title === "历史对手比分"));
});

test("unified pool shows scripts and history with one probability distribution", () => {
  const latest = { "rl/pfsp/enabled": 1, "rl/rollout/opponents/self_play/games": 44,
    "rl/rollout/opponents/router_95/games": 84 };
  const live = { population_games: { self_play: 44, router_95: 84 },
    pfsp: { enabled: true, unified: true, update: 1024, history: [
      { kind: "script", name: "router_95", games: 84, score: 0.4, probability: 0.6 },
      { kind: "history", update: 3575, source_run: "outputs/learning/context", games: 0, score: 0.5, probability: 0.4 },
    ] } };
  assert.equal(currentPopulationMetrics(latest, live), latest);
  const html = pfspTable(live, { integer: String, percent: (value) => `${100 * value}%` });
  assert.match(html, /统一对手池/);
  assert.match(html, /Thomas Router/);
  assert.match(html, /context · U3575/);
  const charts = learningChartConfigurations({ learning: live }, { latest });
  assert.ok(charts.some((chart) => chart.note.includes("共享概率分布")));
});

test("independent scripts show their own probabilities and reject prior-phase metrics", () => {
  const latest = { "rl/pfsp/enabled": 1, "rl/pfsp/separate_scripts": 1,
    "rl/rollout/opponents/self_play/games": 40, "rl/rollout/opponents/history/games": 64,
    "rl/rollout/opponents/router_95/games": 24 };
  const names = ["router_95", "farming_v4", "kaito_v58", "shop_router_0908", "shop_router_0909"];
  const live = { target_script_fraction: 0.2,
    population_games: { self_play: 40, historical_self_play: 64, router_95: 24 },
    pfsp: { enabled: true, separate_scripts: true, update: 1860,
      history: [{ kind: "history", update: 1792, games: 64, score: 0.5, probability: 1 }],
      scripts: Object.fromEntries(names.map((name, index) => [name, { score: 0.3, probability: [0.4, 0.1, 0.2, 0.2, 0.1][index], overall_probability: [0.08, 0.02, 0.04, 0.04, 0.02][index] }])) } };
  assert.equal(currentPopulationMetrics(latest, live), latest);
  assert.deepEqual(currentPopulationMetrics({ ...latest, "rl/pfsp/separate_scripts": 0 }, live), {});
  const html = pfspTable(live, { integer: String, percent: (value) => `${100 * value}%` });
  assert.match(html, /独立脚本池/);
  assert.match(html, /总对局抽样概率/);
  assert.match(html, /8%/);
  assert.match(html, /40%/);
  assert.match(html, /学习方预估比分/);
  assert.equal((html.match(/<table /g) || []).length, 2);
  const chart = learningChartConfigurations({ learning: live }, { latest }).find((item) => item.title === "脚本池抽样概率");
  assert.deepEqual(chart.lines.map(([tag]) => tag), names.map((name) => `rl/pfsp/scripts/${name}/probability`));
});

test("saved PFSP details survive live quota and opponent changes within the same phase", () => {
  const latest = { "rl/pfsp/enabled": 1, "rl/pfsp/separate_scripts": 1,
    "rl/rollout/opponents/self_play/games": 40, "rl/rollout/opponents/history/games": 64,
    "rl/rollout/opponents/router_95/games": 24, "rl/rollout/opponents/history/win_rate": 0.25 };
  const live = { population_games: { self_play: 36, historical_self_play: 64, farming_v4: 28 },
    pfsp: { enabled: true, separate_scripts: true, started_update: 1865 } };
  assert.equal(currentPopulationMetrics(latest, live, 2032), latest);
  assert.deepEqual(currentPopulationMetrics(latest, live, 1864), {});
  const unified = { ...live, pfsp: { enabled: true, unified: true, started_update: 1029 } };
  assert.deepEqual(currentPopulationMetrics(latest, unified, 2032), {});
  const unifiedLatest = { ...latest, "rl/pfsp/separate_scripts": 0 };
  assert.equal(currentPopulationMetrics(unifiedLatest, unified, 2032), unifiedLatest);
});
