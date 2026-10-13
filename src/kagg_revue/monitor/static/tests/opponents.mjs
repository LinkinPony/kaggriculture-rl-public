import assert from "node:assert/strict";
import test from "node:test";
import { filteredEntries, summaryTable, detailHtml, label } from "../opponent-view.js";

const stats = (games, wins) => ({ games, wins, ties: 0, losses: games - wins, win_rate: games ? wins / games : null, observed_score: games ? wins / games : null, mean_terminal_cash: null, mean_cash_difference: null });
const filters = { search: "", kind: "all", membership: "all", sort: "last_update", direction: -1 };
const entries = [
  { key: "history:a", name: "a", kind: "history", source_run: "outputs/learning/source-a", update: 512, last_update: 7, in_pool: false, lifetime: stats(8, 0), interval: stats(0, 0), score: null, probability: null },
  { key: "history:b", name: "b", kind: "history", source_run: "outputs/learning/source-b", update: 512, last_update: 9, in_pool: true, lifetime: stats(8, 4), interval: stats(8, 4), score: 0.5, probability: 0.2 },
  { key: "script:new", name: "<script>", kind: "script", last_update: null, in_pool: true, lifetime: stats(0, 0), interval: stats(0, 0), score: 0.5, probability: 0.2 },
];

test("search, identity, membership, and numeric sorts preserve missing-value semantics", () => {
  assert.deepEqual(filteredEntries(entries, filters).map((row) => row.key), ["history:b", "history:a", "script:new"]);
  assert.equal(filteredEntries(entries, { ...filters, search: "source-a" })[0].key, "history:a");
  assert.deepEqual(filteredEntries(entries, { ...filters, membership: "retired" }).map((row) => row.key), ["history:a"]);
  assert.equal(filteredEntries(entries, { ...filters, kind: "script" }).length, 1);
  assert.deepEqual(filteredEntries(entries, { ...filters, sort: "lifetime.win_rate", direction: 1 }).map((row) => row.key), ["history:a", "history:b", "script:new"]);
  assert.notEqual(label(entries[0]), label(entries[1]));
});

test("summary preserves zero win rate and distinguishes unsampled members from losses", () => {
  const html = summaryTable(entries, filters, "history:b", 10);
  assert.match(html, /0\.0%/);
  assert.match(html, /无交手/);
  assert.match(html, /尚未交手/);
  assert.match(html, /aria-expanded="true"/);
  assert.match(html, /已退出池/);
  assert.match(html, /&lt;script&gt;/);
  assert.ok(!html.includes("<script>"));
  assert.ok(!html.includes("NaN"));
});

test("expanded history labels sampling-time estimates and empty selected ranges", () => {
  const html = detailHtml({ ...entries[0], batches: { rows: [], total: 0, next_before: null } }, { start: 100, end: 500 });
  assert.match(html, /U100–U500/);
  assert.match(html, /抽样前预估比分/);
  assert.match(html, /所选区间没有交手记录/);
  assert.match(html, /实测比分/);
  assert.match(html, /data-batches-next disabled/);
});
