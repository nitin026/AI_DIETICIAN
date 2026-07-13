import { postJSON, getJSON, escapeHtml } from '../api.js';
import { state } from '../state.js';
import { goToStep } from '../main.js';

export function renderAdherence(root) {
  const today = new Date().toISOString().slice(0, 10);
  const defaultWeight = state.healthProfile?.weight_kg || '';

  root.innerHTML = `
    <h2 class="step-header">📅 Adherence Calendar</h2>
    <p class="step-description">Track your daily meals, hydration, sleep, and wellness to stay on course with your nutrition plan.</p>

    <div class="section-card">
      <h3>Log Today's Entry</h3>
      <div class="form-row form-row-3">
        <div class="form-group">
          <label for="adh-date">Date</label>
          <input type="date" id="adh-date" value="${today}" />
        </div>
        <div class="form-group">
          <label for="adh-meal-type">Meal Type</label>
          <select id="adh-meal-type">
            <option value="breakfast">Breakfast</option>
            <option value="mid_morning_snack">Mid-Morning Snack</option>
            <option value="lunch">Lunch</option>
            <option value="evening_snack">Evening Snack</option>
            <option value="dinner">Dinner</option>
          </select>
        </div>
        <div class="form-group">
          <label for="adh-status">Status</label>
          <select id="adh-status">
            <option value="completed">Completed</option>
            <option value="partial">Partial</option>
            <option value="skipped">Skipped</option>
          </select>
        </div>
      </div>

      <div class="form-row form-row-3">
        <div class="form-group">
          <label for="adh-water">Water (ml)</label>
          <input type="number" id="adh-water" value="2000" step="250" min="0" />
        </div>
        <div class="form-group">
          <label for="adh-sleep">Sleep (hours)</label>
          <input type="number" id="adh-sleep" value="7" step="0.5" min="0" max="16" />
        </div>
        <div class="form-group">
          <label for="adh-weight">Weight (kg)</label>
          <input type="number" id="adh-weight" value="${defaultWeight}" step="0.1" min="0" />
        </div>
      </div>

      <div class="form-row form-row-2">
        <div class="form-group">
          <label for="adh-mood">Mood</label>
          <select id="adh-mood">
            <option value="low">Low</option>
            <option value="okay">Okay</option>
            <option value="good" selected>Good</option>
            <option value="great">Great</option>
          </select>
        </div>
        <div class="form-group">
          <label for="adh-digestion">Digestion</label>
          <select id="adh-digestion">
            <option value="comfortable">Comfortable</option>
            <option value="heavy">Heavy</option>
            <option value="acidic">Acidic</option>
            <option value="bloated">Bloated</option>
          </select>
        </div>
      </div>

      <div class="form-group">
        <label for="adh-notes">Notes</label>
        <textarea id="adh-notes" rows="3" placeholder="Any observations…"></textarea>
      </div>

      <button class="btn btn-primary" id="adh-save-btn">Save adherence log</button>
      <div id="adh-save-msg" style="margin-top:0.75rem;"></div>
    </div>

    <div class="section-card" id="adh-history-section">
      <h3>History</h3>
      <div id="adh-metrics" class="metrics-row"></div>
      <div class="chart-container" id="adh-chart"></div>
    </div>
  `;

  // Save handler
  root.querySelector('#adh-save-btn').addEventListener('click', async () => {
    const btn = root.querySelector('#adh-save-btn');
    const msgEl = root.querySelector('#adh-save-msg');
    btn.disabled = true;
    btn.textContent = 'Saving…';
    msgEl.innerHTML = '';

    try {
      const payload = {
        user_id: state.userId,
        date: root.querySelector('#adh-date').value,
        meal_type: root.querySelector('#adh-meal-type').value,
        status: root.querySelector('#adh-status').value,
        water_ml: Number(root.querySelector('#adh-water').value),
        sleep_hours: Number(root.querySelector('#adh-sleep').value),
        weight_kg: Number(root.querySelector('#adh-weight').value),
        mood: root.querySelector('#adh-mood').value,
        digestion: root.querySelector('#adh-digestion').value,
        notes: root.querySelector('#adh-notes').value
      };
      await postJSON('/adherence', payload);
      msgEl.innerHTML = '<div class="alert alert-success">✅ Adherence log saved successfully!</div>';
      loadHistory();
    } catch (err) {
      msgEl.innerHTML = `<div class="alert alert-danger">❌ ${escapeHtml(err.message)}</div>`;
    } finally {
      btn.disabled = false;
      btn.textContent = 'Save adherence log';
    }
  });

  // Load history
  async function loadHistory() {
    const metricsEl = root.querySelector('#adh-metrics');
    const chartEl = root.querySelector('#adh-chart');
    try {
      const data = await getJSON('/adherence/' + state.userId);
      const logs = data.logs || data.adherence_logs || data || [];
      const summary = data.summary || {};

      const totalLogs = Array.isArray(logs) ? logs.length : 0;
      const completed = Array.isArray(logs) ? logs.filter(l => l.status === 'completed').length : 0;
      const skipped = Array.isArray(logs) ? logs.filter(l => l.status === 'skipped').length : 0;
      const avgAdherence = summary.average_adherence ?? (totalLogs > 0 ? Math.round((completed / totalLogs) * 100) : 0);
      const streak = summary.current_streak ?? 0;

      metricsEl.innerHTML = `
        <div class="metric-card">
          <div class="metric-value">${avgAdherence}%</div>
          <div class="metric-label">Average Adherence</div>
        </div>
        <div class="metric-card">
          <div class="metric-value">${streak}</div>
          <div class="metric-label">Current Streak</div>
        </div>
        <div class="metric-card">
          <div class="metric-value">${skipped}</div>
          <div class="metric-label">Skipped Meals</div>
        </div>
      `;

      // Plotly chart
      if (Array.isArray(logs) && logs.length > 0 && typeof Plotly !== 'undefined') {
        const dailyScores = {};
        logs.forEach(l => {
          const d = l.date || '';
          const score = l.status === 'completed' ? 100 : l.status === 'partial' ? 50 : 0;
          if (!dailyScores[d]) dailyScores[d] = [];
          dailyScores[d].push(score);
        });
        const dates = Object.keys(dailyScores).sort();
        const scores = dates.map(d => {
          const arr = dailyScores[d];
          return Math.round(arr.reduce((a, b) => a + b, 0) / arr.length);
        });
        const colors = scores.map(s => s >= 80 ? '#2dd4a8' : s >= 50 ? '#a78bfa' : '#f87171');

        Plotly.newPlot(chartEl, [{
          x: dates,
          y: scores,
          type: 'bar',
          marker: { color: colors, line: { width: 0 } },
          hovertemplate: '%{x}<br>Score: %{y}%<extra></extra>'
        }], {
          title: { text: 'Daily Adherence Scores', font: { color: '#94a3b8' } },
          xaxis: { title: 'Date', color: '#94a3b8', gridcolor: 'rgba(255,255,255,0.06)' },
          yaxis: { title: 'Score (%)', color: '#94a3b8', gridcolor: 'rgba(255,255,255,0.06)', range: [0, 100] },
          plot_bgcolor: 'transparent',
          paper_bgcolor: 'transparent',
          font: { color: '#94a3b8' },
          margin: { t: 40, r: 20, b: 50, l: 50 }
        }, { responsive: true, displayModeBar: false });
      }
    } catch (err) {
      metricsEl.innerHTML = `<div class="alert alert-warning">Could not load history: ${escapeHtml(err.message)}</div>`;
    }
  }

  loadHistory();
}
