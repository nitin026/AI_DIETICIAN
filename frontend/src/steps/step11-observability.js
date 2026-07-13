import { getJSON, escapeHtml } from '../api.js';
import { state } from '../state.js';
import { goToStep } from '../main.js';

export function renderObservability(root) {
  root.innerHTML = `
    <h2 class="step-header">🔍 System Observability</h2>
    <p class="step-description">Real-time system health, delivery metrics, and operational readiness overview.</p>

    <div class="form-row form-row-2" style="align-items:flex-end;">
      <div class="form-group">
        <label for="obs-user-id">User ID Filter</label>
        <input type="text" id="obs-user-id" value="${escapeHtml(state.userId || '')}" placeholder="Filter by user ID" />
      </div>
      <div class="form-group" style="display:flex;align-items:center;gap:0.5rem;padding-bottom:0.5rem;">
        <input type="checkbox" id="obs-show-all" />
        <label for="obs-show-all" style="margin:0;">Show all</label>
        <button class="btn btn-primary btn-sm" id="obs-refresh-btn" style="margin-left:auto;">Refresh</button>
      </div>
    </div>

    <div id="obs-content">
      <div class="loading-overlay" style="position:relative;min-height:120px;"><div class="spinner"></div></div>
    </div>
  `;

  root.querySelector('#obs-refresh-btn').addEventListener('click', loadSnapshot);
  root.querySelector('#obs-show-all').addEventListener('change', loadSnapshot);

  async function loadSnapshot() {
    const contentEl = root.querySelector('#obs-content');
    const showAll = root.querySelector('#obs-show-all').checked;
    const userId = showAll ? '' : root.querySelector('#obs-user-id').value.trim();
    const url = '/api/observability/snapshot' + (userId ? '?user_id=' + encodeURIComponent(userId) : '');

    contentEl.innerHTML = '<div class="loading-overlay" style="position:relative;min-height:120px;"><div class="spinner"></div></div>';

    try {
      const data = await getJSON(url);

      const msgs = data.total_messages ?? data.messages ?? 0;
      const replyRate = data.reply_rate ?? 0;
      const delivery = data.delivery_rate ?? 0;
      const voiceInteractions = data.voice_interactions ?? 0;
      const highRiskAlerts = data.high_risk_alerts ?? 0;

      // Demo readiness
      const readiness = data.demo_readiness || {};
      const scorePercent = readiness.score_percent ?? 0;
      const checks = readiness.checks || [];

      // Operational alerts
      const opAlerts = data.operational_alerts || data.alerts || [];

      // Channel breakdown & intents
      const channelBreakdown = data.channel_breakdown || {};
      const intentBreakdown = data.intent_breakdown || data.inbound_intents || {};

      // Risk & reminder breakdowns
      const riskBreakdown = data.risk_breakdown || {};
      const reminderTypes = data.reminder_types || {};

      // Recent events
      const events = (data.recent_events || data.events || []).slice(-20).reverse();

      contentEl.innerHTML = `
        <!-- Metrics -->
        <div class="metrics-row">
          <div class="metric-card">
            <div class="metric-value">${msgs}</div>
            <div class="metric-label">Messages</div>
          </div>
          <div class="metric-card">
            <div class="metric-value">${replyRate}%</div>
            <div class="metric-label">Reply Rate</div>
          </div>
          <div class="metric-card">
            <div class="metric-value">${delivery}%</div>
            <div class="metric-label">Delivery</div>
          </div>
          <div class="metric-card">
            <div class="metric-value">${voiceInteractions}</div>
            <div class="metric-label">Voice Interactions</div>
          </div>
          <div class="metric-card${highRiskAlerts > 0 ? ' danger' : ''}">
            <div class="metric-value">${highRiskAlerts}</div>
            <div class="metric-label">High Risk Alerts</div>
          </div>
        </div>

        <!-- Demo Readiness -->
        <div class="section-card">
          <h3>Demo Readiness</h3>
          <div class="progress-bar">
            <div class="progress-fill" style="width:${scorePercent}%;">${scorePercent}%</div>
          </div>
          ${checks.length > 0 ? `
            <div style="margin-top:1rem;">
              ${checks.map(c => {
                const ready = c.ready ?? c.passed ?? c.status === 'ready';
                const badge = ready ? '<span class="badge badge-success">Ready</span>' : '<span class="badge badge-danger">Missing</span>';
                return `<div style="display:flex;justify-content:space-between;align-items:center;padding:0.4rem 0;border-bottom:1px solid rgba(255,255,255,0.06);">
                  <span>${escapeHtml(c.name || c.check || '—')}</span>${badge}
                </div>`;
              }).join('')}
            </div>
          ` : ''}
        </div>

        <!-- Operational Alerts -->
        ${opAlerts.length > 0 ? `
          <div class="section-card">
            <h3>⚠️ Operational Alerts</h3>
            ${opAlerts.map(a => {
              const priority = a.priority || a.level || 'medium';
              const cls = priority === 'high' ? 'alert-danger' : 'alert-warning';
              return `<div class="alert ${cls}">${escapeHtml(a.message || a.text || JSON.stringify(a))}</div>`;
            }).join('')}
          </div>
        ` : ''}

        <!-- Charts -->
        <div class="form-row form-row-2">
          <div class="chart-container" id="obs-channel-chart"></div>
          <div class="chart-container" id="obs-intent-chart"></div>
        </div>

        <!-- Breakdown Tables -->
        <div class="form-row form-row-2">
          <div class="section-card">
            <h3>Risk Breakdown</h3>
            ${renderBreakdownTable(riskBreakdown)}
          </div>
          <div class="section-card">
            <h3>Reminder Types</h3>
            ${renderBreakdownTable(reminderTypes)}
          </div>
        </div>

        <!-- Recent Events -->
        <div class="section-card">
          <h3>Recent Events</h3>
          ${renderEventsTable(events)}
        </div>
      `;

      // Plotly charts
      if (typeof Plotly !== 'undefined') {
        // Messages by Channel
        const channelKeys = Object.keys(channelBreakdown);
        if (channelKeys.length > 0) {
          Plotly.newPlot(contentEl.querySelector('#obs-channel-chart'), [{
            x: channelKeys,
            y: channelKeys.map(k => channelBreakdown[k]),
            type: 'bar',
            marker: { color: '#2dd4a8', line: { width: 0 } }
          }], {
            title: { text: 'Messages by Channel', font: { color: '#94a3b8' } },
            xaxis: { color: '#94a3b8', gridcolor: 'rgba(255,255,255,0.06)' },
            yaxis: { title: 'Count', color: '#94a3b8', gridcolor: 'rgba(255,255,255,0.06)' },
            plot_bgcolor: 'transparent',
            paper_bgcolor: 'transparent',
            font: { color: '#94a3b8' },
            margin: { t: 40, r: 20, b: 50, l: 50 }
          }, { responsive: true, displayModeBar: false });
        }

        // Inbound Intents
        const intentKeys = Object.keys(intentBreakdown);
        if (intentKeys.length > 0) {
          Plotly.newPlot(contentEl.querySelector('#obs-intent-chart'), [{
            x: intentKeys,
            y: intentKeys.map(k => intentBreakdown[k]),
            type: 'bar',
            marker: { color: '#a78bfa', line: { width: 0 } }
          }], {
            title: { text: 'Inbound Intents', font: { color: '#94a3b8' } },
            xaxis: { color: '#94a3b8', gridcolor: 'rgba(255,255,255,0.06)', tickangle: -30 },
            yaxis: { title: 'Count', color: '#94a3b8', gridcolor: 'rgba(255,255,255,0.06)' },
            plot_bgcolor: 'transparent',
            paper_bgcolor: 'transparent',
            font: { color: '#94a3b8' },
            margin: { t: 40, r: 20, b: 70, l: 50 }
          }, { responsive: true, displayModeBar: false });
        }
      }
    } catch (err) {
      contentEl.innerHTML = `<div class="alert alert-danger">❌ Failed to load observability data: ${escapeHtml(err.message)}</div>`;
    }
  }

  function renderBreakdownTable(obj) {
    const entries = Object.entries(obj || {});
    if (entries.length === 0) return '<div class="alert alert-info">No data available.</div>';
    return `
      <table class="data-table">
        <thead><tr><th>Category</th><th>Count</th></tr></thead>
        <tbody>
          ${entries.map(([k, v]) => `<tr><td>${escapeHtml(k)}</td><td>${v}</td></tr>`).join('')}
        </tbody>
      </table>
    `;
  }

  function renderEventsTable(events) {
    if (events.length === 0) return '<div class="alert alert-info">No recent events.</div>';
    return `
      <table class="data-table">
        <thead><tr><th>Time</th><th>Channel</th><th>Direction</th><th>Status</th><th>Intent</th><th>Risk</th><th>Content</th></tr></thead>
        <tbody>
          ${events.map(e => `
            <tr>
              <td>${escapeHtml(e.timestamp || e.time || '—')}</td>
              <td>${escapeHtml(e.channel || '—')}</td>
              <td>${escapeHtml(e.direction || '—')}</td>
              <td>${escapeHtml(e.status || '—')}</td>
              <td>${escapeHtml(e.intent || '—')}</td>
              <td><span class="badge ${e.risk_level === 'high' ? 'badge-danger' : e.risk_level === 'medium' ? 'badge-warning' : 'badge-success'}">${escapeHtml(e.risk_level || '—')}</span></td>
              <td>${escapeHtml((e.content || e.message || '').substring(0, 80))}</td>
            </tr>
          `).join('')}
        </tbody>
      </table>
    `;
  }

  // Auto-load
  loadSnapshot();
}
