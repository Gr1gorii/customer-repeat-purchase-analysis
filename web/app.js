'use strict';
const el = id => document.getElementById(id);
const count = n => new Intl.NumberFormat('en-GB').format(n);
const money = n => new Intl.NumberFormat('en-GB', {style: 'currency', currency: 'GBP', maximumFractionDigits: 0}).format(n);
const percent = n => `${(100 * n).toFixed(1)}%`;
const sum = (rows, key) => rows.reduce((total, row) => total + Number(row[key] || 0), 0);
let data;

// Source dimensions enter HTML only through textContent or escaped text.
const escapeText = text => String(text).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function options(id, values) {
  for (const value of values) {
    const option = document.createElement('option'); option.value = value; option.textContent = value;
    el(id).append(option);
  }
}
function render() {
  const country = el('country').value, cohort = el('cohort').value;
  const matchCountry = row => country === 'all' || row.country === country;
  const matchCohort = row => cohort === 'all' || row.cohort_month.slice(0, 7) === cohort;
  const sales = data.sales.filter(matchCountry);
  const repeat = data.repeat.filter(row => matchCountry(row) && matchCohort(row));
  const cohorts = data.cohorts.filter(row => matchCountry(row) && matchCohort(row));
  el('net').textContent = money(sum(sales, 'net_sales'));
  el('gross').textContent = money(sum(sales, 'gross_positive_sales'));
  el('negative').textContent = money(sum(sales, 'negative_value'));
  el('customers').textContent = count(sum(repeat.filter(row => row.days === 30), 'customers'));
  el('repeat').innerHTML = [30, 60, 90].map(days => {
    const rows = repeat.filter(row => row.days === days);
    const eligible = sum(rows, 'eligible_customers'), repeated = sum(rows, 'repeat_customers');
    const rate = eligible ? repeated / eligible : null;
    return `<div class="repeat-row"><b>${days} days</b><div><small>${count(repeated)} / ${count(eligible)} eligible customers</small><div class="track"><i style="width:${rate === null ? 0 : rate * 100}%"></i></div></div><strong>${rate === null ? '-' : percent(rate)}</strong></div>`;
  }).join('');
  renderMonthly(sales);
  renderCohorts(cohorts);
  const candidates = data.candidates.filter(matchCountry);
  const labels = {missing_customer:'Missing identity',no_candidate:'No prior candidate',one_candidate:'One candidate',multiple_candidates:'Multiple candidates'};
  el('candidates').innerHTML = '<div class="candidate-grid">' + Object.entries(labels).map(([key, label]) => {
    const rows = candidates.filter(row => row.candidate_status === key);
    return `<article><span>${label}</span><strong>${count(sum(rows, 'negative_rows'))}</strong><small>lines · ${money(sum(rows, 'negative_value'))}</small></article>`;
  }).join('') + '</div>';
  el('empty').hidden = cohorts.length > 0;
}
function renderMonthly(rows) {
  const grouped = new Map();
  for (const row of rows) { const month = row.month.slice(0, 7); grouped.set(month, (grouped.get(month) || 0) + row.net_sales); }
  const months = [...grouped.keys()].sort();
  if (!months.length) { el('monthly').textContent = 'No ledger records for this country.'; return; }
  const values = months.map(m => grouped.get(m));
  const low = Math.min(0, ...values), high = Math.max(1, ...values), span = high - low;
  const y = v => 195 - (v - low) / span * 160;
  const zero = y(0), step = 480 / months.length;
  let svg = `<svg viewBox="0 0 540 245" role="img" aria-label="Monthly net sales in GBP"><line x1="45" y1="${zero}" x2="530" y2="${zero}" stroke="#9aaea3"/><text x="4" y="20" font-size="10" fill="#5b716c">${escapeText(money(high))}</text>`;
  months.forEach((month, i) => {
    const value = values[i], x = 48 + i * step, top = Math.min(y(value), zero), height = Math.max(1, Math.abs(y(value) - zero));
    svg += `<rect x="${x}" y="${top}" width="${step * .72}" height="${height}" fill="${month === '2011-12' ? '#b46036' : '#276f61'}"><title>${month}: ${escapeText(money(value))}${month === '2011-12' ? ' (partial)' : ''}</title></rect><text transform="translate(${x + 5},211) rotate(40)" font-size="9" fill="#5b716c">${month}</text>`;
  });
  el('monthly').innerHTML = svg + '</svg>';
}
function renderCohorts(rows) {
  const grouped = new Map();
  for (const row of rows) {
    const key = row.cohort_month.slice(0, 7);
    if (!grouped.has(key)) grouped.set(key, {size: 0, cells: new Map()});
    const group = grouped.get(key);
    if (row.month_index === 0) group.size += row.cohort_size;
    const cell = group.cells.get(row.month_index) || {active: 0, size: 0, complete: true};
    cell.active += row.active_customers; cell.size += row.cohort_size; cell.complete &&= row.complete_month;
    group.cells.set(row.month_index, cell);
  }
  if (!grouped.size) {el('cohort-table').innerHTML = ''; return;}
  const maxIndex = Math.max(...rows.map(row => row.month_index));
  let html = '<table aria-label="Monthly cohort activity"><thead><tr><th>Cohort</th><th>Customers</th>' + Array.from({length:maxIndex + 1}, (_, i) => `<th>M${i}</th>`).join('') + '</tr></thead><tbody>';
  for (const [month, group] of [...grouped].sort(([a], [b]) => a.localeCompare(b))) {
    html += `<tr><th class="cohort-name">${month}</th><th>${count(group.size)}</th>`;
    for (let i = 0; i <= maxIndex; i++) {
      const cell = group.cells.get(i);
      if (!cell) html += '<td></td>';
      else if (!cell.complete) html += `<td class="unobserved" title="Incomplete month; ${cell.active} observed active customers">-</td>`;
      else {
        const rate = cell.active / cell.size;
        html += `<td style="background:hsl(162 35% ${95 - 65 * rate}%);color:${rate > .55 ? '#fff' : '#183f3a'}" title="${cell.active} / ${cell.size} customers">${percent(rate)}</td>`;
      }
    }
    html += '</tr>';
  }
  el('cohort-table').innerHTML = html + '</tbody></table>';
}
async function load() {
  try {
    const response = await fetch('data.json');
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    data = await response.json();
    options('country', [...new Set(data.sales.map(row => row.country).filter(Boolean))].sort());
    options('cohort', [...new Set(data.repeat.map(row => row.cohort_month.slice(0, 7)))].sort());
    el('validation').textContent = 'SQL ↔ Python reconciled · 541,909 source lines';
    const labels = {exact_duplicates_removed:'Exact duplicates removed',missing_customer_rows_raw:'Raw lines without CustomerID',missing_description_rows_raw:'Raw lines without description',zero_price_rows:'Zero-price lines excluded',negative_quantity_rows:'Negative quantity lines',invalid_rows:'Invalid retained lines'};
    el('quality').innerHTML = '<div class="quality-grid">' + Object.entries(labels).map(([key,label]) => `<div><strong>${count(data.quality[key])}</strong><span>${label}</span></div>`).join('') + '</div>';
    el('country').addEventListener('change', render); el('cohort').addEventListener('change', render);
    el('reset').addEventListener('click', () => {el('country').value = 'all'; el('cohort').value = 'all'; render();});
    el('content').hidden = false; render();
  } catch (error) {
    el('validation').textContent = 'Results unavailable'; el('error').hidden = false;
    el('error').textContent = `Could not load reviewed data (${error.message}). Run the pipeline and serve the project with python -m http.server; see README.`;
  }
}
load();
