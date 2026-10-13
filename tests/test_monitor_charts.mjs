import assert from "node:assert/strict";
import test from "node:test";

import { productionKlMetrics } from "../src/kagg_revue/monitor/static/charts.js";
import { evaluationSeries } from "../src/kagg_revue/monitor/static/evaluation.js";
import { scriptCharts, currentPopulationMetrics, learningCards, learningChartConfigurations, learningStage } from "../src/kagg_revue/monitor/static/learning.js";
import { visibleLines, pathFor, nearestPoint } from "../src/kagg_revue/monitor/static/plot.js";
import { explorerConfigurations } from "../src/kagg_revue/monitor/static/explorer.js";
import { leaguePairs, leagueEvaluationSummary, leagueLabel } from "../src/kagg_revue/monitor/static/league.js";

test("two-member native league omits retired A and displays the fifth script", () => {
  const run = { learning: { league: true, phase: "reinforcement_learning", members: { bc: {}, spataro: {} },
    script_opponents: ["router_95", "farming_v4", "kaito_v58", "shop_router_0908", "shop_router_0909"],
    games_per_script_per_member: 8 } };
  const pairs = ["bc_vs_spataro", "bc_vs_bc", "spataro_vs_spataro",
    ...Object.keys(run.learning.members).flatMap((member) => run.learning.script_opponents.map((script) => `${member}_vs_${script}`))];
  const latest = Object.fromEntries(["a_vs_bc", ...pairs].map((pair) => [`rl/league/pairs/${pair}/games`, 8]));
  const f = { metricCard: (title, value, note) => ({ title, value, note }),
    integer: String, number: String, duration: String, bytes: String };
  const cards = learningCards(run, latest, f);
  assert.ok(!cards.some((card) => card.title === "A · BC"));
  assert.equal(cards.find((card) => card.title === "Native 脚本对手").value, "5 个");
  assert.equal(learningStage(run), "2 模型联赛 PPO");
  const charts = learningChartConfigurations(run, { latest });
  assert.ok(charts.find((chart) => chart.title === "Update 阶段耗时").note.includes("2 个在训模型"));
  const tags = charts.flatMap((chart) => chart.lines.map(([tag]) => tag));
  assert.equal(new Set(tags).size, 75);
  assert.ok(!tags.some((tag) => tag.includes("/a/") || tag.includes("a_vs_")));
  assert.ok(tags.includes("rl/league/pairs/bc_vs_shop_router_0909/win_rate"));
  assert.deepEqual(Object.keys(leaguePairs(latest, ["bc", "spataro"])), pairs);
});

test("league cards and explorer retain three specialists and oriented model pairs", () => {
  const run = { learning: { league: true, phase: "reinforcement_learning", epochs: 6,
    pretraining: { a: { completed_epochs: 6, selection_nll: 0.1, rows: 100 } } } };
  const latest = { "rl/league/pairs/a_vs_bc/games": 64, "rl/league/pairs/a_vs_bc/win_rate": 0,
    "rl/league/pairs/a_vs_spataro/games": 64, "rl/league/pairs/bc_vs_spataro/games": 64 };
  const f = { metricCard: (title, value, note) => ({ title, value, note }), integer: String, number: String,
    duration: String, bytes: String, percent: String, escapeHtml: String };
  const cards = learningCards(run, latest, f);
  assert.equal(learningStage(run), "3 模型联赛 PPO");
  assert.equal(cards.find((card) => card.title === "A · BC").value, "6 / 6 epoch");
  assert.ok(!cards.some((card) => card.title === "历史对手比分"));
  const configs = learningChartConfigurations(run, { latest });
  const tags = new Set(configs.flatMap((config) => config.lines.map(([tag]) => tag)));
  assert.ok(tags.size <= 64);
  for (const name of ["a", "bc", "spataro"]) assert.ok(tags.has(`rl/league/optimization/${name}/value_loss`));
  const overview = explorerConfigurations(configs, { view: "overview", opponent: "all", layout: "overlay" });
  assert.deepEqual(overview.map((config) => config.title), ["联赛配对胜率", "各模型终局现金", "Update 阶段耗时"]);
  assert.equal(new Set(overview[0].lines.map((line) => line[2])).size, 3);
  const pairs = explorerConfigurations(configs, { view: "opponents", opponent: "a_vs_bc", layout: "overlay" });
  assert.equal(pairs[1].lines.length, 2);
  assert.notEqual(pairs[1].lines[0][2], pairs[1].lines[1][2]);
  assert.equal(leaguePairs(latest).a_vs_bc.win_rate, 0);
  const evaluation = leagueEvaluationSummary({ step: 0, physical_games: 64, pairs: leaguePairs(latest) }, f);
  assert.ok(evaluation.includes("A vs B+C 0"));
});

test("self-play has independent diagnostics and preserves the SpaTaro display name", () => {
  assert.equal(leagueLabel("spataro"), "SpaTaro");
  assert.equal(leagueLabel("spataro_vs_spataro"), "SpaTaro 自博弈");
  const latest = Object.fromEntries(["a_vs_a", "bc_vs_bc", "spataro_vs_spataro", "a_vs_bc", "a_vs_spataro", "bc_vs_spataro"].map((name) => [`rl/league/pairs/${name}/games`, 32]));
  const charts = learningChartConfigurations({ learning: { league: true } }, { latest });
  const tags = new Set(charts.flatMap((config) => config.lines.map(([tag]) => tag)));
  assert.ok(tags.size <= 64);
  assert.ok(tags.has("rl/league/pairs/spataro_vs_spataro/mean_terminal_cash"));
  assert.ok(!tags.has("rl/league/pairs/spataro_vs_spataro/win_rate"));
  const filtered = explorerConfigurations(charts, { view: "opponents", opponent: "spataro_vs_spataro", layout: "overlay" });
  assert.equal(filtered.length, 3);
  assert.ok(filtered.every((chart) => chart.lines.length === 1));
});

test("hiding raw observations leaves only trends, including when no raw points exist", () => {
  const config = { lines: [["cash", "现金", "green"]] };
  const raw = [{ step: 1, value: 100 }];
  const trend = [{ step: 1, value: 50 }];
  const data = { series: { cash: raw }, trends: { cash: trend } };
  assert.deepEqual(visibleLines(config, data, false).map((line) => line.points), [trend]);
  assert.deepEqual(visibleLines(config, data, true).map((line) => line.points), [raw, trend]);
  assert.equal(visibleLines(config, { trends: data.trends }, false).length, 1);
});

test("lines and crosshairs never bridge missing data or configuration boundaries", () => {
  const points = [{ step: 1, value: 0, segment: 0 }, { step: 2, value: 1, segment: 0 },
    { step: 10, value: 2, segment: 1 }];
  assert.equal(pathFor(points, (n) => n, (n) => n), "M1.00,0.00 L2.00,1.00 M10.00,2.00");
  assert.equal(nearestPoint(points, 0), null);
  assert.equal(nearestPoint(points, 6), null);
  assert.equal(nearestPoint(points, 10), points[2]);
});

test("opponent filtering applies across metrics and retains colors between layouts", () => {
  const configurations = ["win_rate", "mean_cash_difference"].map((field) => ({
    title: field, group: "opponents", lines: ["router_95", "farming_v4"].map((name) => [
      `rl/rollout/opponents/${name}/${field}`, name,
    ]),
  }));
  const settings = { view: "opponents", opponent: "all", layout: "separate" };
  const separate = explorerConfigurations(configurations, settings);
  assert.equal(separate.length, 4);
  const filtered = explorerConfigurations(configurations, { ...settings, opponent: "router_95", layout: "overlay" });
  assert.equal(filtered.length, 2);
  assert.ok(filtered.every((config) => config.lines.length === 1));
  assert.equal(filtered[0].lines[0][2], separate[0].lines[0][2]);
});

test("new script mixture shows exact physical-game counts and waits for matching metrics", () => {
  const names = ["router_95", "farming_v4", "kaito_v58", "shop_router_0908"];
  const live = { population_games: { self_play: 64, ...Object.fromEntries(names.map((name) => [name, 16])) },
    selfplay_fraction: 0.5, script_fraction: 0.5, history_fraction: 0, games_per_update: 128 };
  assert.deepEqual(currentPopulationMetrics({ "rl/rollout/opponents/self_play/games": 128 }, live), {});
  const latest = Object.fromEntries(Object.entries(live.population_games).map(([name, count]) => [`rl/rollout/opponents/${name}/games`, count]));
  assert.equal(currentPopulationMetrics(latest, live), latest);
  const f = { metricCard: (title, value, note) => ({ title, value, note }), integer: String, number: String,
    duration: String, bytes: String, percent: (value) => `${100 * value}%` };
  const cards = learningCards({ learning: live }, latest, f);
  const composition = cards.find((card) => card.title === "训练对局");
  assert.equal(composition.value, "50% Self-play · 50% 脚本");
  for (const label of ["Thomas Router 95.5%", "Farming V4", "Kaito v58", "Shop Router 0908"]) assert.ok(composition.note.includes(`${label} 16 场`));
  assert.ok(!cards.some((card) => card.title === "历史对手比分"));
  const series = Object.fromEntries([...names, "boatlee_v29", "self_play"].map((name) => [`rl/rollout/opponents/${name}/games`, [{ step: 106, value: 16 }]]));
  const charts = scriptCharts({ series }, (title, note, unit, lines) => ({ lines }), live.population_games);
  assert.equal(charts[0].lines.length, 4);
  assert.ok(charts[0].lines.every(([tag]) => !tag.includes("boatlee_v29")));
});

test("learning script curves discover scripts while excluding self-play and history", () => {
  assert.deepEqual(scriptCharts({}, () => null), []);
  const series = Object.fromEntries(["kaito_v39", "boatlee_v21", "self_play", "history"].map(
    (name) => [`rl/rollout/opponents/${name}/games`, [{ step: 459, value: 32 }]],
  ));
  const charts = scriptCharts({ series }, (title, note, unit, lines) => ({ title, note, unit, lines }));
  assert.equal(charts.length, 3);
  assert.deepEqual(charts[0].lines.map((line) => line[1]), ["boatlee_v21", "kaito_v39"]);
  assert.ok(charts[0].lines.every((line) => line[0].endsWith("/win_rate")));
});

test("KL scope discovery agrees for cards and curves, including zero", () => {
  for (const scope of ["prefix", "plan", "field", "new_scope"]) {
    const tag = `rl/optimization/maximum_${scope}_kl`;
    const cards = productionKlMetrics({ [tag]: 0 });
    const curves = productionKlMetrics({ [tag]: [{ step: 1, value: 0 }] });
    assert.equal(cards.length, 1);
    assert.equal(cards[0].tag, tag);
    assert.deepEqual(cards, curves);
  }
});

test("KL scope discovery ignores missing data without relabeling other scopes", () => {
  const prefix = "rl/optimization/maximum_prefix_kl";
  const plan = "rl/optimization/maximum_plan_kl";
  const values = { [plan]: 0.5, [prefix]: null, "rl/optimization/value_loss": 0 };
  assert.deepEqual(productionKlMetrics(values).map(({ tag }) => tag), [plan]);
  assert.equal(productionKlMetrics({ [prefix]: [] }).length, 0);
  assert.equal(productionKlMetrics({ [prefix]: NaN }).length, 0);
  const combined = productionKlMetrics({ ...values, [prefix]: 0 });
  assert.deepEqual(combined.map(({ tag }) => tag), [prefix, plan]);
  assert.notEqual(combined[0].label, combined[1].label);
});

test("independent evaluation curves retain zero wins and omit missing opponents", () => {
  const loss = { games: 2, wins: 0, ties: 1, losses: 1, mean_cash_difference: -3 };
  const win = { games: 4, wins: 1, ties: 1, losses: 2, mean_cash_difference: 0 };
  const series = evaluationSeries([
    { step: 3, overall: win, opponents: {} },
    { step: 1, overall: loss, opponents: { "alpha/beta": loss } },
  ]);
  assert.deepEqual(series["overall/win_rate"], [{ step: 1, value: 0 }, { step: 3, value: 25 }]);
  assert.deepEqual(series["opponent/alpha%2Fbeta/win_rate"], [{ step: 1, value: 0 }]);
  assert.deepEqual(series["overall/mean_cash_difference"], [{ step: 1, value: -3 }, { step: 3, value: 0 }]);
  assert.equal(series["overall/mean_terminal_cash"], undefined);
});
