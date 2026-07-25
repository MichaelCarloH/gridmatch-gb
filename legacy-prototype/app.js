const $ = (selector) => document.querySelector(selector);
const svgEl = (name, attrs = {}) => {
  const el = document.createElementNS('http://www.w3.org/2000/svg', name);
  Object.entries(attrs).forEach(([key, value]) => el.setAttribute(key, value));
  return el;
};
const path = (points) => points.map((p, i) => `${i ? 'L' : 'M'}${p[0].toFixed(1)},${p[1].toFixed(1)}`).join(' ');

function renderForecast(multiplier = 1) {
  const svg = $('#forecastChart'); svg.replaceChildren();
  const width = 720, height = 248, left = 6, bottom = 225;
  const values = Array.from({ length: 49 }, (_, i) => (0.46 + .25 * Math.sin((i / 2 - 6) * Math.PI / 12) ** 2 + ((i > 14 && i < 38) ? .13 : 0)) * multiplier);
  const y = (value) => bottom - value * 225;
  for (let level = 0; level < 4; level++) svg.append(svgEl('line', { x1: left, x2: width - 5, y1: 25 + level * 62, y2: 25 + level * 62, stroke: '#e8ebeb', 'stroke-width': 1 }));
  const upper = values.map((v, i) => [left + i * (width - 12) / 48, y(v + .11)]);
  const lower = values.map((v, i) => [left + i * (width - 12) / 48, y(Math.max(.05, v - .11))]).reverse();
  svg.append(svgEl('path', { d: `${path(upper)} ${path(lower)} Z`, fill: 'rgba(47,115,217,.14)' }));
  svg.append(svgEl('path', { d: path(values.map((v, i) => [left + i * (width - 12) / 48, y(v)])), fill: 'none', stroke: '#2f73d9', 'stroke-width': 3, 'stroke-linecap': 'round', 'stroke-linejoin': 'round' }));
  const last = values.length - 1;
  svg.append(svgEl('circle', { cx: left + last * (width - 12) / 48, cy: y(values[last]), r: 4.5, fill: '#fff', stroke: '#2f73d9', 'stroke-width': 2.5 }));
}

function renderMatch(residual = false) {
  const svg = $('#matchChart'); svg.replaceChildren();
  const width = 800, height = 280, base = 242, scale = 190;
  const demand = Array.from({ length: 49 }, (_, i) => .49 + .29 * Math.sin((i / 2 - 7) * Math.PI / 12) ** 2 + (i > 15 && i < 37 ? .12 : 0));
  const generation = Array.from({ length: 49 }, (_, i) => Math.max(0, .56 * Math.sin((i / 2 - 4) * Math.PI / 16)) + .18 + .15 * Math.sin((i / 2 + 2) * Math.PI / 12) ** 2);
  const coordinate = (data) => data.map((v, i) => [i * width / 48, base - v * scale]);
  for (let level = 0; level < 4; level++) svg.append(svgEl('line', { x1: 0, x2: width, y1: 16 + level * 66, y2: 16 + level * 66, stroke: '#29333c', 'stroke-width': 1 }));
  if (residual) {
    const residualValues = demand.map((v, i) => Math.max(0, v - generation[i]));
    svg.append(svgEl('path', { d: `${path(coordinate(residualValues))} L800,242 L0,242 Z`, fill: 'rgba(47,115,217,.35)' }));
    svg.append(svgEl('path', { d: path(coordinate(residualValues)), fill: 'none', stroke: '#78a8fa', 'stroke-width': 3, 'stroke-linejoin': 'round' }));
    return;
  }
  svg.append(svgEl('path', { d: `${path(coordinate(generation))} L800,242 L0,242 Z`, fill: 'rgba(76,168,85,.18)' }));
  svg.append(svgEl('path', { d: path(coordinate(generation)), fill: 'none', stroke: '#4ca855', 'stroke-width': 3, 'stroke-linejoin': 'round' }));
  svg.append(svgEl('path', { d: path(coordinate(demand)), fill: 'none', stroke: '#6aa1f4', 'stroke-width': 3, 'stroke-linejoin': 'round' }));
}

renderForecast(); renderMatch();

$('#portfolioSelect').addEventListener('change', (event) => {
  const selected = event.target.value;
  renderForecast(selected === 'Buy power' ? 1.08 : selected === 'Sell power' ? .68 : 1);
});

let residual = false;
$('#toggleView').addEventListener('click', (event) => {
  residual = !residual; renderMatch(residual);
  event.currentTarget.textContent = residual ? 'Show matched view' : 'Show residual view';
});

const dialog = $('#insightDialog');
$('#explainHedge').addEventListener('click', () => { $('#dialogTitle').textContent = 'A transparent hedge recommendation'; $('#dialogText').textContent = 'The selected quantity sits above the median forecast because a short imbalance costs more than a long imbalance. It is a recommendation for review, not an automated trade.'; dialog.showModal(); });
$('#openAlert').addEventListener('click', () => { $('#dialogTitle').textContent = 'West Coast Wind anomaly'; $('#dialogText').textContent = 'The observed output is 11.4% below the weather-normalised expectation from 09:30. Investigate availability, curtailment and telemetry quality before estimating any lost revenue.'; dialog.showModal(); });
$('.close-dialog').addEventListener('click', () => dialog.close());
dialog.addEventListener('click', (event) => { if (event.target === dialog) dialog.close(); });

$('#downloadBrief').addEventListener('click', () => {
  const brief = 'GRIDMATCH GB — DAY-AHEAD BRIEFING\n24 July 2026\n\nDemand forecast: 38.4 MWh\nRenewable supply: 26.1 MWh\nDirectly matched: 23.7 MWh (61.7%)\nResidual grid import: 14.7 MWh\nSuggested hedge: 16.2 MWh (P67)\n\nIndependent prototype using public and simulated data.';
  const link = Object.assign(document.createElement('a'), { href: URL.createObjectURL(new Blob([brief], { type: 'text/plain' })), download: 'gridmatch-day-ahead-briefing.txt' });
  link.click(); URL.revokeObjectURL(link.href);
});

fetch('/api/summary').then((response) => response.ok ? response.json() : null).then((summary) => {
  if (summary) $('#ringValue').innerHTML = `${summary.greenMatchRate.toFixed(1)}<small>%</small>`;
}).catch(() => {});
