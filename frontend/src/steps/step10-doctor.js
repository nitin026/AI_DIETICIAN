import { getJSON, escapeHtml } from '../api.js';
import { state } from '../state.js';
import { goToStep } from '../main.js';

export function renderDoctor(root) {
  root.innerHTML = `
    <h2 class="step-header">👨‍⚕️ Doctor Dashboard</h2>
    <p class="step-description">Comprehensive patient overview with risk alerts, adherence tracking, and communication history.</p>

    <div class="form-group" style="display:flex;gap:1rem;align-items:flex-end;flex-wrap:wrap;">
      <div style="flex:1;min-width:200px;">
        <label for="doc-user-id">Patient ID</label>
        <input type="text" id="doc-user-id" value="${escapeHtml(state.userId || '')}" placeholder="Enter patient ID" />
      </div>
      <button class="btn btn-primary" id="doc-load-btn">Load Patient</button>
    </div>

    <div id="doc-content"></div>
  `;

  root.querySelector('#doc-load-btn').addEventListener('click', loadPatient);

  async function loadPatient() {
    const userId = root.querySelector('#doc-user-id').value.trim();
    const contentEl = root.querySelector('#doc-content');
    if (!userId) {
      contentEl.innerHTML = '<div class="alert alert-warning">Please enter a patient ID.</div>';
      return;
    }

    contentEl.innerHTML = '<div class="loading-overlay" style="position:relative;min-height:120px;"><div class="spinner"></div></div>';

    try {
      const data = await getJSON('/api/clinic/patient/' + encodeURIComponent(userId));

      const riskLevel = data.risk_level || 'unknown';
      const riskBadgeClass = riskLevel === 'high' ? 'badge-danger'
        : riskLevel === 'medium' ? 'badge-warning' : 'badge-success';
      const messages = data.communication_count ?? data.messages ?? 0;
      const skipped = data.skipped_logs ?? 0;
      const highRiskAlerts = data.high_risk_alerts ?? 0;
      const suggestedAction = data.suggested_action || data.recommendation || '';
      const alerts = data.alerts || [];
      const adherenceSummary = data.adherence_summary || {};
      const avgAdherence = adherenceSummary.average_adherence ?? 0;
      const streak = adherenceSummary.current_streak ?? 0;
      const completed = adherenceSummary.completed_meals ?? 0;
      const dailyScores = adherenceSummary.daily_scores || [];
      const commTimeline = data.communication_timeline || data.communications || [];
      const adherenceLogs = data.adherence_logs || [];

      contentEl.innerHTML = `
        <!-- Risk & Summary Metrics -->
        <div class="metrics-row">
          <div class="metric-card">
            <div class="metric-value"><span class="badge ${riskBadgeClass}">${escapeHtml(riskLevel)}</span></div>
            <div class="metric-label">Risk Level</div>
          </div>
          <div class="metric-card">
            <div class="metric-value">${messages}</div>
            <div class="metric-label">Messages</div>
          </div>
          <div class="metric-card">
            <div class="metric-value">${skipped}</div>
            <div class="metric-label">Skipped Logs</div>
          </div>
          <div class="metric-card${highRiskAlerts > 0 ? ' danger' : ''}">
            <div class="metric-value">${highRiskAlerts}</div>
            <div class="metric-label">High-Risk Alerts</div>
          </div>
        </div>

        ${suggestedAction ? `<div class="alert alert-info"><strong>Suggested Action:</strong> ${escapeHtml(suggestedAction)}</div>` : ''}

        <!-- Alerts -->
        ${alerts.length > 0 ? `
          <div class="section-card">
            <h3>⚠️ Alerts</h3>
            ${alerts.map(a => {
              const priority = a.priority || a.level || 'medium';
              const cls = priority === 'high' ? 'alert-danger' : 'alert-warning';
              return `<div class="alert ${cls}">${escapeHtml(a.message || a.text || JSON.stringify(a))}</div>`;
            }).join('')}
          </div>
        ` : ''}

        <!-- Adherence Metrics -->
        <div class="metrics-row">
          <div class="metric-card">
            <div class="metric-value">${avgAdherence}%</div>
            <div class="metric-label">Average Adherence</div>
          </div>
          <div class="metric-card">
            <div class="metric-value">${streak}</div>
            <div class="metric-label">Current Streak</div>
          </div>
          <div class="metric-card">
            <div class="metric-value">${completed}</div>
            <div class="metric-label">Completed Meals</div>
          </div>
        </div>

        <!-- Adherence Chart -->
        <div class="section-card">
          <h3>Adherence Score Trend</h3>
          <div class="chart-container" id="doc-adherence-chart"></div>
        </div>

        <!-- Tabs -->
        <div class="section-card">
          <div class="tab-bar">
            <button class="tab-btn active" data-tab="doc-tab-comm">Communication Timeline</button>
            <button class="tab-btn" data-tab="doc-tab-logs">Adherence Logs</button>
          </div>
          <div class="tab-content" id="doc-tab-comm">
            ${renderCommTable(commTimeline)}
          </div>
          <div class="tab-content" id="doc-tab-logs" style="display:none;">
            ${renderLogsTable(adherenceLogs)}
          </div>
        </div>
      `;

      // Tab switching
      contentEl.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
          contentEl.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
          btn.classList.add('active');
          contentEl.querySelectorAll('.tab-content').forEach(tc => tc.style.display = 'none');
          contentEl.querySelector('#' + btn.dataset.tab).style.display = 'block';
        });
      });

      // Plotly adherence chart
      if (dailyScores.length > 0 && typeof Plotly !== 'undefined') {
        const dates = dailyScores.map(s => s.date || s.day);
        const scores = dailyScores.map(s => s.score ?? s.value ?? 0);
        const colors = scores.map(s => s >= 80 ? '#2dd4a8' : s >= 50 ? '#a78bfa' : '#f87171');

        Plotly.newPlot(contentEl.querySelector('#doc-adherence-chart'), [{
          x: dates,
          y: scores,
          type: 'bar',
          marker: { color: colors, line: { width: 0 } },
          hovertemplate: '%{x}<br>Score: %{y}%<extra></extra>'
        }], {
          title: { text: 'Adherence Score Trend', font: { color: '#94a3b8' } },
          xaxis: { title: 'Date', color: '#94a3b8', gridcolor: 'rgba(255,255,255,0.06)' },
          yaxis: { title: 'Score (%)', color: '#94a3b8', gridcolor: 'rgba(255,255,255,0.06)', range: [0, 100] },
          plot_bgcolor: 'transparent',
          paper_bgcolor: 'transparent',
          font: { color: '#94a3b8' },
          margin: { t: 40, r: 20, b: 50, l: 50 }
        }, { responsive: true, displayModeBar: false });
      }
    } catch (err) {
      contentEl.innerHTML = `<div class="alert alert-danger">❌ Failed to load patient: ${escapeHtml(err.message)}</div>`;
    }
  }

  function renderCommTable(events) {
    if (!events || events.length === 0) {
      return '<div class="alert alert-info">No communication history.</div>';
    }
    return `
      <table class="data-table">
        <thead><tr><th>Time</th><th>Channel</th><th>Direction</th><th>Intent</th><th>Risk</th><th>Content</th></tr></thead>
        <tbody>
          ${events.map(e => `
            <tr>
              <td>${escapeHtml(e.timestamp || e.time || '—')}</td>
              <td>${escapeHtml(e.channel || '—')}</td>
              <td>${escapeHtml(e.direction || '—')}</td>
              <td>${escapeHtml(e.intent || '—')}</td>
              <td><span class="badge ${e.risk_level === 'high' ? 'badge-danger' : e.risk_level === 'medium' ? 'badge-warning' : 'badge-success'}">${escapeHtml(e.risk_level || '—')}</span></td>
              <td>${escapeHtml((e.content || e.message || '').substring(0, 100))}</td>
            </tr>
          `).join('')}
        </tbody>
      </table>
    `;
  }

  function renderLogsTable(logs) {
    if (!logs || logs.length === 0) {
      return '<div class="alert alert-info">No adherence logs.</div>';
    }
    return `
      <table class="data-table">
        <thead><tr><th>Date</th><th>Meal</th><th>Status</th><th>Notes</th></tr></thead>
        <tbody>
          ${logs.map(l => `
            <tr>
              <td>${escapeHtml(l.date || '—')}</td>
              <td>${escapeHtml(l.meal_type || l.meal || '—')}</td>
              <td>${escapeHtml(l.status || '—')}</td>
              <td>${escapeHtml((l.notes || '').substring(0, 80))}</td>
            </tr>
          `).join('')}
        </tbody>
      </table>
    `;
  }
}
