// ---------------------------------------------------------------------------
// Palette (kept in sync with style.css tokens) — used for chart theming
// ---------------------------------------------------------------------------
const COLORS = {
  void: '#070A0F',
  panel: '#0E141D',
  line: '#1C2531',
  lineBright: '#2A3646',
  amber: '#FFB23E',
  crimson: '#FF4B5C',
  cyan: '#4FD8E8',
  textHi: '#EDF1F6',
  textMid: '#9FAEC1',
  textLo: '#5C6A7D',
};

function baseLayout(extra = {}) {
  return {
    paper_bgcolor: 'transparent',
    plot_bgcolor: 'transparent',
    font: { family: 'JetBrains Mono, monospace', color: COLORS.textMid, size: 11 },
    margin: { t: 8, r: 12, l: 40, b: 32 },
    xaxis: { gridcolor: COLORS.line, zerolinecolor: COLORS.line, color: COLORS.textLo, automargin: true },
    yaxis: { gridcolor: COLORS.line, zerolinecolor: COLORS.line, color: COLORS.textLo, automargin: true },
    ...extra,
  };
}
const PLOTLY_CONFIG = { displayModeBar: false, responsive: true };

// ---------------------------------------------------------------------------
// Fetch status + refresh
// ---------------------------------------------------------------------------
function renderFetchStatus(status) {
  const el = document.getElementById('fetch-status');
  const textEl = document.getElementById('fetch-status-text');
  if (!status || status.ok === null || status.ok === undefined) {
    textEl.textContent = 'Data freshness unknown';
    el.className = 'fetch-status';
    return;
  }
  if (status.ok) {
    textEl.textContent = `✓ Synced · ${status.when ? status.when.replace('T', ' ').slice(0, 19) : ''} UTC`;
    el.className = 'fetch-status ok';
  } else {
    textEl.textContent = `⚠ ${status.message}`;
    el.className = 'fetch-status err';
  }
}

async function manualRefresh() {
  const btn = document.getElementById('refresh-btn');
  btn.disabled = true;
  btn.textContent = '↻ Refreshing…';
  try {
    const res = await fetch('/api/refresh');
    const d = await res.json();
    renderFetchStatus(d.fetch_status);
    applyData(d.data);
  } finally {
    btn.disabled = false;
    btn.textContent = '↻ Refresh';
  }
}

// ---------------------------------------------------------------------------
// Stat strip — count-up animation
// ---------------------------------------------------------------------------
function animateCount(el, target, suffix = '', duration = 900) {
  const start = 0;
  const startTime = performance.now();
  function tick(now) {
    const p = Math.min(1, (now - startTime) / duration);
    const eased = 1 - Math.pow(1 - p, 3);
    const val = Math.round(start + (target - start) * eased);
    el.textContent = val.toLocaleString() + suffix;
    if (p < 1) requestAnimationFrame(tick);
  }
  requestAnimationFrame(tick);
}

function renderStats(totals) {
  animateCount(document.getElementById('stat-connections'), totals.total_connections || 0);
  animateCount(document.getElementById('stat-ips'), totals.unique_ips || 0);
  animateCount(document.getElementById('stat-critical'), totals.critical_pct || 0, '%');
  animateCount(document.getElementById('stat-reports'), totals.total_reports_sum || 0);
  animateCount(document.getElementById('stat-countries'), totals.countries_seen || 0);
  animateCount(document.getElementById('stat-commands'), totals.commands_typed || 0);
}

// ---------------------------------------------------------------------------
// Radar — the signature element
// ---------------------------------------------------------------------------
function escapeXml(s) {
  return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

function hashCode(str) {
  let h = 0;
  for (let i = 0; i < str.length; i++) { h = (h * 31 + str.charCodeAt(i)) >>> 0; }
  return h;
}

function polar(cx, cy, angleDeg, radius) {
  const a = (angleDeg - 90) * Math.PI / 180;
  return { x: cx + radius * Math.cos(a), y: cy + radius * Math.sin(a) };
}

function scoreColor(score) {
  if (score === null || score === undefined) return COLORS.amber;
  if (score >= 90) return COLORS.crimson;
  if (score >= 40) return COLORS.amber;
  return COLORS.cyan;
}

function renderRadar(recentConnections, scoreByIp) {
  const size = 440, cx = size / 2, cy = size / 2, maxR = 190;
  const rings = [0.28, 0.52, 0.76, 1.0].map(f => maxR * f);

  let svg = `<svg viewBox="0 0 ${size} ${size}" xmlns="http://www.w3.org/2000/svg">`;

  // range rings
  rings.forEach(r => {
    svg += `<circle cx="${cx}" cy="${cy}" r="${r}" fill="none" stroke="${COLORS.line}" stroke-width="1"/>`;
  });
  // crosshair
  svg += `<line x1="${cx - maxR}" y1="${cy}" x2="${cx + maxR}" y2="${cy}" stroke="${COLORS.line}" stroke-width="1"/>`;
  svg += `<line x1="${cx}" y1="${cy - maxR}" x2="${cx}" y2="${cy + maxR}" stroke="${COLORS.line}" stroke-width="1"/>`;

  // rotating sweep (SMIL — reliable continuous rotation, no JS animation loop needed)
  const p2 = polar(cx, cy, 0, maxR);
  const p3 = polar(cx, cy, -46, maxR);
  svg += `<g>
      <path d="M ${cx} ${cy} L ${p2.x.toFixed(1)} ${p2.y.toFixed(1)} A ${maxR} ${maxR} 0 0 0 ${p3.x.toFixed(1)} ${p3.y.toFixed(1)} Z"
            fill="${COLORS.amber}" opacity="0.10"/>
      <line x1="${cx}" y1="${cy}" x2="${p2.x.toFixed(1)}" y2="${p2.y.toFixed(1)}"
            stroke="${COLORS.amber}" stroke-width="1.5" opacity="0.85"/>
      <animateTransform attributeName="transform" type="rotate" from="0 ${cx} ${cy}" to="360 ${cx} ${cy}"
            dur="6s" repeatCount="indefinite"/>
    </g>`;

  // blips — radiusFrac capped well inside maxR so ping-ring growth never
  // reaches the frame edge (0.82 * maxR + 13px ping growth stays inside 190)
  const list = (recentConnections || []).slice(0, 14);
  list.forEach((conn, i) => {
    const ip = conn.src_ip || 'unknown';
    const angle = hashCode(ip) % 360;
    const radiusFrac = 0.26 + 0.56 * ((hashCode(ip + 'r') % 1000) / 1000);
    const r = maxR * radiusFrac;
    const pos = polar(cx, cy, angle, r);
    const score = scoreByIp[ip];
    const color = scoreColor(score);
    const isFresh = i < 4;
    const baseRadius = isFresh ? 4.5 : 3;
    const delay = (i * 0.18).toFixed(2);
    const safeIp = escapeXml(ip);

    svg += `<circle cx="${pos.x.toFixed(1)}" cy="${pos.y.toFixed(1)}" r="${baseRadius}" fill="${color}">
        <title>${safeIp}</title>
        <animate attributeName="opacity" values="0.45;1;0.45" dur="2.6s" begin="${delay}s" repeatCount="indefinite"/>
      </circle>`;

    if (isFresh) {
      svg += `<circle cx="${pos.x.toFixed(1)}" cy="${pos.y.toFixed(1)}" r="${baseRadius}" fill="none" stroke="${color}" stroke-width="1.5">
          <animate attributeName="r" values="${baseRadius};13" dur="2.4s" begin="${delay}s" repeatCount="indefinite"/>
          <animate attributeName="opacity" values="0.6;0" dur="2.4s" begin="${delay}s" repeatCount="indefinite"/>
        </circle>`;
    }
  });

  svg += `</svg>`;
  document.getElementById('radar-mount').innerHTML = svg;
  document.getElementById('radar-count').textContent = list.length;
}

// ---------------------------------------------------------------------------
// Charts
// ---------------------------------------------------------------------------
function renderTimeline(timeline) {
  const x = timeline.map(d => d[0]);
  const y = timeline.map(d => d[1]);
  Plotly.newPlot('chart-timeline', [{
    x, y, type: 'bar',
    marker: { color: COLORS.amber, opacity: 0.9 },
  }], baseLayout({ height: 260 }), PLOTLY_CONFIG);
}

function renderDonut(buckets) {
  const order = ['critical (90-100)', 'elevated (40-89)', 'low (1-39)', 'clean (0)', 'unscored'];
  const colorMap = {
    'critical (90-100)': COLORS.crimson,
    'elevated (40-89)': COLORS.amber,
    'low (1-39)': COLORS.textLo,
    'clean (0)': COLORS.cyan,
    'unscored': COLORS.lineBright,
  };
  const labels = order.filter(k => buckets[k] > 0);
  const values = labels.map(k => buckets[k]);
  const colors = labels.map(k => colorMap[k]);

  Plotly.newPlot('chart-donut', [{
    labels, values, type: 'pie', hole: 0.62,
    marker: { colors, line: { color: COLORS.panel, width: 2 } },
    textinfo: 'none',
  }], baseLayout({
    height: 260,
    showlegend: true,
    legend: { orientation: 'h', y: -0.15, font: { size: 10, color: COLORS.textMid } },
  }), PLOTLY_CONFIG);
}

function renderCountries(countries) {
  const sorted = [...countries].sort((a, b) => a[1] - b[1]);
  Plotly.newPlot('chart-countries', [{
    x: sorted.map(d => d[1]), y: sorted.map(d => d[0]),
    type: 'bar', orientation: 'h',
    marker: { color: COLORS.cyan, opacity: 0.85 },
  }], baseLayout({ height: 260 }), PLOTLY_CONFIG);
}

function renderEvents(events) {
  const sorted = [...events].sort((a, b) => a[1] - b[1]);
  Plotly.newPlot('chart-events', [{
    x: sorted.map(d => d[1]), y: sorted.map(d => d[0]),
    type: 'bar', orientation: 'h',
    marker: { color: COLORS.amber, opacity: 0.85 },
  }], baseLayout({ height: 260 }), PLOTLY_CONFIG);
}

// ---------------------------------------------------------------------------
// Tables
// ---------------------------------------------------------------------------
function scoreBadgeClass(score) {
  if (score === null || score === undefined) return 'score-unk';
  if (score >= 90) return 'score-crit';
  if (score >= 40) return 'score-warn';
  return 'score-clean';
}

function renderOffenders(offenders) {
  const body = document.getElementById('offenders-body');
  body.innerHTML = '';
  offenders.forEach((o, i) => {
    const tr = document.createElement('tr');
    tr.style.animationDelay = `${i * 0.04}s`;
    const scoreLabel = (o.score === null || o.score === undefined) ? 'N/A' : o.score;
    tr.innerHTML = `
      <td>${o.ip}</td>
      <td><span class="score-badge ${scoreBadgeClass(o.score)}">${scoreLabel}</span></td>
      <td>${o.reports === null || o.reports === undefined ? 'N/A' : o.reports.toLocaleString()}</td>
      <td>${o.country || 'N/A'}</td>
      <td>${o.isp || 'N/A'}</td>
      <td>${o.attempts === null || o.attempts === undefined ? 'N/A' : o.attempts}</td>
    `;
    body.appendChild(tr);
  });
}

const COMMAND_TRUNCATE_LEN = 140;

function renderCommands(commands) {
  const panel = document.getElementById('commands-panel');
  const body = document.getElementById('commands-body');
  body.innerHTML = '';
  if (!commands || commands.length === 0) { panel.style.display = 'none'; return; }
  panel.style.display = 'block';
  commands.forEach((c, i) => {
    const tr = document.createElement('tr');
    tr.style.animationDelay = `${i * 0.04}s`;
    const full = c.input || '';
    const isLong = full.length > COMMAND_TRUNCATE_LEN;
    const short = isLong ? full.slice(0, COMMAND_TRUNCATE_LEN) + '…' : full;

    const cmdCell = document.createElement('td');
    cmdCell.className = 'cmd-cell';
    const codeSpan = document.createElement('span');
    codeSpan.className = 'cmd-text';
    codeSpan.textContent = short;
    cmdCell.appendChild(codeSpan);

    if (isLong) {
      const toggle = document.createElement('button');
      toggle.className = 'cmd-toggle';
      toggle.type = 'button';
      toggle.textContent = 'show full';
      let expanded = false;
      toggle.addEventListener('click', () => {
        expanded = !expanded;
        codeSpan.textContent = expanded ? full : short;
        toggle.textContent = expanded ? 'show less' : 'show full';
      });
      cmdCell.appendChild(toggle);
    }

    tr.innerHTML = `<td>${c.timestamp}</td><td>${c.src_ip}</td>`;
    tr.appendChild(cmdCell);
    body.appendChild(tr);
  });
}

function escapeHtml(s) {
  const div = document.createElement('div');
  div.textContent = s || '';
  return div.innerHTML;
}

function renderTerminal(connections) {
  const body = document.getElementById('terminal-body');
  body.innerHTML = '';
  if (!connections || connections.length === 0) {
    body.innerHTML = '<div class="terminal-line dim">// no recent sessions</div>';
    return;
  }
  connections.forEach((c, i) => {
    const line = document.createElement('div');
    line.className = 'terminal-line';
    line.style.animationDelay = `${i * 0.05}s`;
    const port = c.dst_port !== undefined && c.dst_port !== null ? c.dst_port : '';
    line.innerHTML = `<span class="action">connect</span><span class="ip">${c.src_ip}</span><span>→ :${port}</span><span class="ts">${c.timestamp || ''}</span>`;
    body.appendChild(line);
  });
}

// ---------------------------------------------------------------------------
// Orchestration
// ---------------------------------------------------------------------------
function buildScoreLookup(offenders) {
  const map = {};
  (offenders || []).forEach(o => { map[o.ip] = o.score; });
  return map;
}

function applyData(d) {
  document.getElementById('gen-time').textContent = d.generated_at;
  document.getElementById('sensor-ip').textContent = '3.110.222.106:2222';

  renderStats(d.totals);
  renderRadar(d.recent_connections, buildScoreLookup(d.top_offenders));
  renderTimeline(d.timeline);
  renderDonut(d.score_buckets);
  renderCountries(d.countries);
  renderEvents(d.event_breakdown);
  renderOffenders(d.top_offenders);
  renderCommands(d.commands);
  renderTerminal(d.recent_connections);
}

async function loadDashboard() {
  const res = await fetch('/api/data');
  const d = await res.json();
  renderFetchStatus(d.fetch_status);
  applyData(d);
}

loadDashboard();
