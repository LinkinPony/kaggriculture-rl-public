import assert from "node:assert/strict";
import test from "node:test";
import { learningChartConfigurations } from "../learning.js";
import { quadrantCards } from "../quadrants.js";
import { explorerConfigurations } from "../explorer.js";

test("quadrant charts expose real zeroes and omit unmeasured historical runs", () => {
  const run = { learning: { pure_selfplay: true } };
  const latest = { "rl/land/trajectories": 168, "rl/land/quadrants/SE/unlocked_rate": 0,
    "rl/land/quadrants/SE/productive_rate": 0, "rl/land/quadrants/SE/unused_rate": 0 };
  const charts = learningChartConfigurations(run, { latest });
  const overview = explorerConfigurations(charts, { view: "overview" });
  assert.ok(overview.some((c) => c.title === "象限购地率" && c.percent));
  assert.ok(overview.some((c) => c.title === "象限生产使用率"));
  assert.equal(charts.find((c) => c.title === "象限统计耗时").group, "resources");
  assert.ok(!learningChartConfigurations(run, { latest: {} }).some((c) => c.title.includes("象限")));
  const format = { metricCard: (...args) => args, percent: String, integer: String };
  assert.equal(quadrantCards(latest, format)[0][1], "0");
  assert.deepEqual(quadrantCards({}, format), []);
});
