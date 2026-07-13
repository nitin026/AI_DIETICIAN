import { postJSON, escapeHtml } from '../api.js';
import { state } from '../state.js';
import { goToStep } from '../main.js';

export function renderInsights(root) {
  root.innerHTML = `
    <h2 class="step-header">📊 AI Health Insights</h2>
    <p class="step-description">AI-powered analysis of your nutritional profile, adherence patterns, and personalised recommendations.</p>
    <div class="loading-overlay" id="insights-loading">
      <div class="spinner"></div>
      <p>Generating insights…</p>
    </div>
    <div id="insights-content" style="display:none;"></div>
  `;

  loadInsights();

  async function loadInsights() {
    const loadingEl = root.querySelector('#insights-loading');
    const contentEl = root.querySelector('#insights-content');

    try {
      const payload = {
        user_id: state.userId,
        health_profile: state.healthProfile || {},
        preference_profile: state.preferenceProfile || {},
        daily_targets: state.nutrientResponse?.daily_targets || {}
      };
      const data = await postJSON('/analytics', payload);
      state.analyticsResponse = data;

      loadingEl.style.display = 'none';
      contentEl.style.display = 'block';

      const healthScore = data.health_score ?? data.summary?.health_score ?? '—';
      const adherenceRisk = data.adherence_risk ?? data.summary?.adherence_risk ?? 'unknown';
      const riskBadge = adherenceRisk === 'low' ? 'badge-success'
        : adherenceRisk === 'medium' ? 'badge-warning'
        : adherenceRisk === 'high' ? 'badge-danger' : 'badge-info';

      const insights = data.insights || data.recommendations || [];
      const nutrientAdequacy = data.nutrient_adequacy || data.nutrient_compliance || {};

      // Sort nutrients by score descending and take top 10
      const nutrientEntries = Object.entries(nutrientAdequacy)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 10);

      let insightsHtml = '';
      if (Array.isArray(insights) && insights.length > 0) {
        insightsHtml = insights.map(i => {
          const text = typeof i === 'string' ? i : (i.message || i.text || JSON.stringify(i));
          return `<div class="alert alert-info">${escapeHtml(text)}</div>`;
        }).join('');
      } else {
        insightsHtml = '<div class="alert alert-info">No insights available yet. Continue logging your meals and adherence to receive AI-powered recommendations.</div>';
      }

      contentEl.innerHTML = `
        <div class="metrics-row">
          <div class="metric-card">
            <div class="metric-value primary">${healthScore}<span style="font-size:0.5em;opacity:0.7">/100</span></div>
            <div class="metric-label">Health Score</div>
          </div>
          <div class="metric-card">
            <div class="metric-value"><span class="badge ${riskBadge}">${escapeHtml(String(adherenceRisk))}</span></div>
            <div class="metric-label">Adherence Risk</div>
          </div>
        </div>

        <div class="section-card">
          <h3>💡 Personalised Insights</h3>
          ${insightsHtml}
        </div>

        <div class="section-card">
          <h3>Nutrient Compliance</h3>
          <div class="chart-container" id="insights-nutrient-chart"></div>
        </div>
      `;

      // Plotly nutrient compliance chart
      if (nutrientEntries.length > 0 && typeof Plotly !== 'undefined') {
        const names = nutrientEntries.map(e => e[0].replace(/_/g, ' '));
        const scores = nutrientEntries.map(e => typeof e[1] === 'number' ? e[1] : 0);

        Plotly.newPlot(root.querySelector('#insights-nutrient-chart'), [{
          x: names,
          y: scores,
          type: 'bar',
          marker: {
            color: '#2dd4a8',
            line: { width: 0 }
          },
          hovertemplate: '%{x}<br>Score: %{y}<extra></extra>'
        }], {
          title: { text: 'Nutrient Compliance (Top 10)', font: { color: '#94a3b8' } },
          xaxis: { color: '#94a3b8', gridcolor: 'rgba(255,255,255,0.06)', tickangle: -30 },
          yaxis: { title: 'Score', color: '#94a3b8', gridcolor: 'rgba(255,255,255,0.06)' },
          plot_bgcolor: 'transparent',
          paper_bgcolor: 'transparent',
          font: { color: '#94a3b8' },
          margin: { t: 40, r: 20, b: 80, l: 50 }
        }, { responsive: true, displayModeBar: false });
      }
    } catch (err) {
      loadingEl.style.display = 'none';
      contentEl.style.display = 'block';
      contentEl.innerHTML = `<div class="alert alert-danger">❌ Failed to load insights: ${escapeHtml(err.message)}</div>`;
    }
  }
}
