export function escapeHtml(value) {
  return String(value).replaceAll("&", "&amp;").replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;").replaceAll('"', "&quot;");
}

export function formatValue(value, config = {}) {
  if (value == null || !Number.isFinite(value)) return "—";
  if (config.percent) return `${(value * 100).toFixed(1)}%`;
  if (config.bytes) return `${(value / 1024 ** 3).toFixed(1)} GiB`;
  if (value !== 0 && Math.abs(value) < 0.001) return value.toExponential(2);
  return value.toLocaleString("zh-CN", { maximumFractionDigits: Math.abs(value) < 1 ? 5 : 1 });
}

export function pathFor(points, x, y) {
  return points.map((point, index) => `${index && point.segment === points[index - 1].segment ? "L" : "M"}${x(point.step).toFixed(2)},${y(point.value).toFixed(2)}`).join(" ");
}

export function nearestPoint(points, step) {
  if (!points.length || step < points[0].step || step > points.at(-1).step) return null;
  let lo = 0; let hi = points.length - 1;
  while (lo < hi) {
    const mid = (lo + hi) >> 1;
    if (points[mid].step < step) lo = mid + 1; else hi = mid;
  }
  if (lo > 0 && points[lo - 1].step < step && points[lo].step > step
      && points[lo - 1].segment !== points[lo].segment) return null;
  return lo > 0 && Math.abs(points[lo - 1].step - step) < Math.abs(points[lo].step - step)
    ? points[lo - 1] : points[lo];
}

export function visibleLines(config, data, raw) {
  return config.lines.flatMap(([tag, label, color]) => {
    const trend = data.trends?.[tag] || [];
    return [
      ...(raw ? [{ tag, label, color, raw: true, points: data.series?.[tag] || [] }] : []),
      { tag, label, color, raw: false, points: trend },
    ];
  }).filter((line) => line.points.length);
}

export function renderPlot(card, config, data, options) {
  const lines = visibleLines(config, data, options.raw);
  const value = (number) => formatValue(number, config);
  const statistics = config.lines.map(([tag, label, color]) => {
    const summary = data.summaries?.[tag];
    const delta = summary?.delta;
    const difference = delta == null ? "前窗不足" : config.percent
      ? `${delta >= 0 ? "+" : ""}${(delta * 100).toFixed(1)} pp`
      : `${delta >= 0 ? "+" : ""}${value(delta)}`;
    const coverage = summary ? `U${summary.window_start}–${summary.step} · ${summary.count} 条记录${config.percent || tag.includes("cash") ? ` · ${summary.samples} 场` : ""}` : "当前区间没有记录";
    return `<button class="trend-legend" data-tag="${escapeHtml(tag)}" title="${escapeHtml(coverage)}；窗口均值及相对上一窗口变化${tag.startsWith("rl/rollout/opponents/") ? "；点击筛选对手" : ""}">
      <i style="background:${color}"></i><span>${escapeHtml(label)}</span><b>${value(summary?.mean)}</b>
      <small>${difference}</small></button>`;
  }).join("");
  const peak = config.lines.filter(([tag]) => tag.endsWith("_kl"))
    .map(([tag, label]) => `${label} ${value(data.summaries?.[tag]?.max)}`).join(" · ");
  card.innerHTML = `<div class="chart-head"><div class="chart-title"><h3>${escapeHtml(config.title)}</h3>
    <p>${escapeHtml(config.note)}</p></div><button class="plot-expand" aria-label="放大 ${escapeHtml(config.title)}">放大</button></div>
    <div class="trend-legends">${statistics}</div><div class="chart-canvas"></div>
    <div class="plot-footnote">${peak ? `区间原始峰值：${peak}` : `粗线：${data.smoothing} 轮趋势${options.raw ? " · 淡线：原始数据" : " · 原始数据已隐藏"}`}</div>`;
  card.querySelector(".plot-expand").addEventListener("click", () => options.expand(config));
  card.querySelectorAll("[data-tag]").forEach((button) => {
    button.addEventListener("click", () => options.select(button.dataset.tag));
  });
  const canvas = card.querySelector(".chart-canvas");
  if (!lines.length) {
    canvas.innerHTML = '<div class="chart-empty">所选区间没有该指标</div>';
    return () => {};
  }
  const width = Math.max(280, Math.round(canvas.getBoundingClientRect().width));
  const height = options.expanded ? Math.max(300, Math.min(600, innerHeight * 0.6)) : 246;
  const margin = { left: 64, right: 14, top: 20, bottom: 32 };
  const plotWidth = width - margin.left - margin.right;
  const plotHeight = height - margin.top - margin.bottom;
  const xMin = data.range.start; const xMax = Math.max(xMin + 1, data.range.end);
  const values = lines.flatMap((line) => line.points.map((p) => p.value));
  let yMin = Math.min(...values); let yMax = Math.max(...values);
  if (config.percent) { yMin = 0; yMax = 1; }
  else {
    if (config.zero) { yMin = Math.min(0, yMin); yMax = Math.max(0, yMax); }
    const padding = (yMax - yMin || Math.abs(yMin) || 1) * 0.08;
    yMin -= padding; yMax += padding;
  }
  const x = (step) => margin.left + (step - xMin) / (xMax - xMin) * plotWidth;
  const y = (number) => margin.top + (yMax - number) / (yMax - yMin) * plotHeight;
  const grid = Array.from({ length: 5 }, (_, index) => {
    const tick = yMin + (yMax - yMin) * index / 4;
    return `<line class="chart-grid-line" x1="${margin.left}" x2="${width - margin.right}" y1="${y(tick)}" y2="${y(tick)}"/>
      <text class="chart-axis-label" x="${margin.left - 7}" y="${y(tick) + 3}" text-anchor="end">${value(tick)}</text>`;
  }).join("");
  const labels = Array.from({ length: 4 }, (_, index) => {
    const step = Math.round(xMin + (xMax - xMin) * index / 3);
    return `<text class="chart-axis-label" x="${x(step)}" y="${height - 8}" text-anchor="middle">${step.toLocaleString("zh-CN")}</text>`;
  }).join("");
  const events = data.events.filter((event) => event.step >= xMin && event.step <= xMax);
  const eventLines = events.map((event) => `<line class="plot-event" x1="${x(event.step)}" x2="${x(event.step)}" y1="${margin.top}" y2="${height - margin.bottom}"/>
    <text class="plot-event-label" x="${x(event.step) + 3}" y="12">U${event.step}</text>`).join("");
  const paths = lines.map((line) => `<path class="chart-path ${line.raw ? "plot-raw" : "plot-trend"}" stroke="${line.color}" d="${pathFor(line.points, x, y)}"/>
    ${!line.raw ? `<circle fill="${line.color}" cx="${x(line.points.at(-1).step)}" cy="${y(line.points.at(-1).value)}" r="3"/>` : ""}`).join("");
  canvas.innerHTML = `<svg class="chart-svg" style="height:${height}px" viewBox="0 0 ${width} ${height}" role="img" aria-label="${escapeHtml(config.title)}">
    ${grid}${config.zero ? `<line class="zero-line" x1="${margin.left}" x2="${width - margin.right}" y1="${y(0)}" y2="${y(0)}"/>` : ""}${paths}${eventLines}${labels}
    <rect class="plot-selection" y="${margin.top}" height="${plotHeight}" width="0"/>
    <line class="hover-line" y1="${margin.top}" y2="${height - margin.bottom}"/>
    <rect class="chart-hit" x="${margin.left}" y="${margin.top}" width="${plotWidth}" height="${plotHeight}"/>
    </svg><div class="chart-tooltip"></div>`;
  const svg = canvas.querySelector("svg"); const hit = canvas.querySelector(".chart-hit");
  const hover = canvas.querySelector(".hover-line"); const tooltip = canvas.querySelector(".chart-tooltip");
  const selection = canvas.querySelector(".plot-selection");
  const showHover = (step) => {
    if (step == null || step < xMin || step > xMax) {
      hover.style.opacity = "0"; tooltip.classList.remove("visible"); return;
    }
    hover.setAttribute("x1", x(step)); hover.setAttribute("x2", x(step)); hover.style.opacity = "1";
    const rows = lines.map((line) => ({ ...line, point: nearestPoint(line.points, step) }))
      .filter((line) => line.point);
    tooltip.innerHTML = `<div class="tooltip-step">Update ${Math.round(step).toLocaleString("zh-CN")}</div>`
      + rows.map((line) => `<div class="tooltip-row"><span><i style="background:${line.color}"></i>${escapeHtml(line.label)} · ${line.raw ? "原始" : "趋势"}</span><b>${value(line.point.value)}</b></div>
        <div class="tooltip-observation">实际 U${line.point.step}${line.point.bucket ? ` · 桶 ${line.point.bucket.start}–${line.point.bucket.end}，${line.point.bucket.count} 条；范围 ${value(line.point.bucket.min)}–${value(line.point.bucket.max)}` : ""}</div>`).join("");
    tooltip.style.left = `${x(step) / width * 100}%`;
    tooltip.style.top = "42%";
    tooltip.style.transform = x(step) > width / 2 ? "translate(calc(-100% - 10px), -50%)" : "translate(10px, -50%)";
    tooltip.classList.toggle("visible", rows.length > 0);
  };
  const eventStep = (event) => {
    const bounds = svg.getBoundingClientRect();
    return xMin + Math.max(0, Math.min(1, ((event.clientX - bounds.left) * width / bounds.width - margin.left) / plotWidth)) * (xMax - xMin);
  };
  let drag = null;
  hit.addEventListener("pointerdown", (event) => {
    if (event.button !== 0) return;
    drag = eventStep(event); hit.setPointerCapture(event.pointerId);
  });
  hit.addEventListener("pointermove", (event) => {
    const step = eventStep(event); options.hover(step);
    if (drag != null) {
      selection.setAttribute("x", x(Math.min(step, drag)));
      selection.setAttribute("width", Math.abs(x(step) - x(drag)));
    }
  });
  hit.addEventListener("pointerup", (event) => {
    const end = eventStep(event); const start = drag; drag = null;
    selection.setAttribute("width", 0);
    if (hit.hasPointerCapture(event.pointerId)) hit.releasePointerCapture(event.pointerId);
    if (start != null && Math.abs(x(end) - x(start)) >= 8) options.zoom(
      Math.max(xMin, Math.floor(Math.min(start, end))), Math.min(xMax, Math.ceil(Math.max(start, end))),
    );
  });
  hit.addEventListener("pointercancel", () => { drag = null; selection.setAttribute("width", 0); });
  hit.addEventListener("pointerleave", () => { if (drag == null) options.hover(null); });
  return showHover;
}
