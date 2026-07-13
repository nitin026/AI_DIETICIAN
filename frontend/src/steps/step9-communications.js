import { postJSON, getJSON, escapeHtml } from '../api.js';
import { state } from '../state.js';
import { goToStep } from '../main.js';

export function renderCommunications(root) {
  root.innerHTML = `
    <h2 class="step-header">📞 Clinic Communications</h2>
    <p class="step-description">Manage patient communications, automated reminders, and voice assistant interactions.</p>

    <div class="form-group">
      <label for="comm-user-id">Patient ID</label>
      <input type="text" id="comm-user-id" value="${escapeHtml(state.userId || '')}" placeholder="Enter patient ID" />
    </div>

    <!-- KPI Metrics -->
    <div class="metrics-row" id="comm-kpi"></div>

    <!-- Create Reminder -->
    <div class="section-card expandable">
      <h3>Create Automated Reminder ▾</h3>
      <div class="expandable-content">
        <div class="form-row form-row-2">
          <div class="form-group">
            <label for="rem-type">Reminder Type</label>
            <select id="rem-type">
              <option value="meal">Meal</option>
              <option value="hydration">Hydration</option>
              <option value="supplement">Supplement</option>
              <option value="adherence">Adherence</option>
              <option value="follow_up">Follow-up</option>
            </select>
          </div>
          <div class="form-group">
            <label for="rem-title">Title</label>
            <input type="text" id="rem-title" placeholder="Reminder title" />
          </div>
        </div>
        <div class="form-row form-row-2">
          <div class="form-group">
            <label for="rem-schedule">Schedule</label>
            <input type="text" id="rem-schedule" placeholder="e.g. daily at 8:00 AM" />
          </div>
          <div class="form-group">
            <label for="rem-channel">Channel</label>
            <select id="rem-channel">
              <option value="in_app">In-App</option>
              <option value="whatsapp_ready">WhatsApp Ready</option>
              <option value="sms">SMS</option>
              <option value="push">Push</option>
              <option value="email">Email</option>
            </select>
          </div>
        </div>
        <div class="form-row form-row-2">
          <div class="form-group">
            <label for="rem-patient-name">Patient Name</label>
            <input type="text" id="rem-patient-name" placeholder="Patient name" />
          </div>
          <div class="form-group">
            <label for="rem-phone">Phone</label>
            <input type="text" id="rem-phone" placeholder="Phone number" />
          </div>
        </div>
        <div class="form-row form-row-2">
          <div class="form-group">
            <label for="rem-meal-type">Meal Type</label>
            <input type="text" id="rem-meal-type" placeholder="e.g. breakfast" />
          </div>
          <div class="form-group">
            <label for="rem-meal-name">Meal Name</label>
            <input type="text" id="rem-meal-name" placeholder="e.g. Oatmeal Bowl" />
          </div>
        </div>
        <button class="btn btn-primary" id="rem-save-btn">Save reminder</button>
        <div id="rem-save-msg" style="margin-top:0.75rem;"></div>
      </div>
    </div>

    <!-- Dispatch Reminders -->
    <div class="section-card">
      <h3>Dispatch Reminders</h3>
      <div style="display:flex;align-items:center;gap:1rem;flex-wrap:wrap;">
        <button class="btn btn-primary" id="dispatch-btn">Dispatch active reminders</button>
        <span id="dispatch-count"></span>
      </div>
      <div id="dispatch-msg" style="margin-top:0.75rem;"></div>
    </div>

    <!-- Voice Assistant Demo -->
    <div class="section-card expandable">
      <h3>Voice Assistant Demo ▾</h3>
      <div class="expandable-content">
        <div class="form-group">
          <label for="voice-transcript">Transcript</label>
          <textarea id="voice-transcript" rows="3" placeholder="Paste or type voice transcript…"></textarea>
        </div>
        <div class="form-row form-row-2">
          <div class="form-group">
            <label for="voice-caller">Caller</label>
            <input type="text" id="voice-caller" placeholder="Caller name or ID" />
          </div>
          <div class="form-group">
            <label for="voice-lang">Detected Language</label>
            <select id="voice-lang">
              <option value="">Auto</option>
              <option value="en">English</option>
              <option value="hi">Hindi</option>
              <option value="hinglish">Hinglish</option>
            </select>
          </div>
        </div>
        <button class="btn btn-primary" id="voice-run-btn">Run voice assistant</button>
        <div id="voice-result" style="margin-top:0.75rem;"></div>
      </div>
    </div>

    <!-- Send & Receive -->
    <div class="form-row form-row-2">
      <div class="section-card">
        <h3>Send Reminder</h3>
        <div class="form-group">
          <label for="send-channel">Channel</label>
          <select id="send-channel">
            <option value="sms">SMS</option>
            <option value="whatsapp">WhatsApp</option>
            <option value="voice">Voice</option>
            <option value="in_app">In-App</option>
          </select>
        </div>
        <div class="form-group">
          <label for="send-msg-type">Message Type</label>
          <select id="send-msg-type">
            <option value="meal_reminder">Meal Reminder</option>
            <option value="hydration">Hydration</option>
            <option value="supplement">Supplement</option>
            <option value="adherence">Adherence</option>
            <option value="follow_up">Follow-up</option>
            <option value="freeform">Freeform</option>
          </select>
        </div>
        <div class="form-group">
          <label for="send-recipient">Recipient</label>
          <input type="text" id="send-recipient" placeholder="Phone or ID" />
        </div>
        <div class="form-group">
          <label for="send-content">Content</label>
          <textarea id="send-content" rows="3" placeholder="Message content…"></textarea>
        </div>
        <button class="btn btn-primary" id="send-btn">Send</button>
        <div id="send-msg" style="margin-top:0.75rem;"></div>
      </div>

      <div class="section-card">
        <h3>Simulate Reply</h3>
        <div class="form-group">
          <label for="reply-channel">Channel</label>
          <select id="reply-channel">
            <option value="sms">SMS</option>
            <option value="whatsapp">WhatsApp</option>
            <option value="voice">Voice</option>
            <option value="in_app">In-App</option>
          </select>
        </div>
        <div class="form-group">
          <label for="reply-sender">Sender</label>
          <input type="text" id="reply-sender" placeholder="Sender ID" />
        </div>
        <div class="form-group">
          <label for="reply-text">Reply</label>
          <textarea id="reply-text" rows="3" placeholder="Simulated reply…"></textarea>
        </div>
        <button class="btn btn-secondary" id="reply-btn">Receive reply</button>
        <div id="reply-result" style="margin-top:0.75rem;"></div>
      </div>
    </div>

    <!-- Communication Timeline -->
    <div class="section-card">
      <h3>Communication Timeline</h3>
      <div id="comm-timeline"></div>
    </div>
  `;

  const getUserId = () => root.querySelector('#comm-user-id').value.trim() || state.userId;

  // Expandable toggle
  root.querySelectorAll('.expandable > h3').forEach(h3 => {
    h3.style.cursor = 'pointer';
    const content = h3.nextElementSibling;
    content.style.display = 'none';
    h3.addEventListener('click', () => {
      const open = content.style.display !== 'none';
      content.style.display = open ? 'none' : 'block';
      h3.textContent = h3.textContent.replace(/[▾▸]/, open ? '▸' : '▾');
    });
  });

  // KPI load
  async function loadKPI() {
    const userId = getUserId();
    const el = root.querySelector('#comm-kpi');
    try {
      const data = await getJSON('/api/communications/metrics?user_id=' + encodeURIComponent(userId));
      const total = data.total_messages ?? 0;
      const outbound = data.outbound ?? 0;
      const replyRate = data.reply_rate ?? 0;
      const highRisk = data.high_risk_count ?? 0;
      el.innerHTML = `
        <div class="metric-card">
          <div class="metric-value">${total}</div>
          <div class="metric-label">Total Messages</div>
        </div>
        <div class="metric-card">
          <div class="metric-value">${outbound}</div>
          <div class="metric-label">Outbound</div>
        </div>
        <div class="metric-card">
          <div class="metric-value">${replyRate}%</div>
          <div class="metric-label">Reply Rate</div>
        </div>
        <div class="metric-card${highRisk > 0 ? ' danger' : ''}">
          <div class="metric-value">${highRisk}</div>
          <div class="metric-label">High Risk</div>
        </div>
      `;
    } catch (err) {
      el.innerHTML = `<div class="alert alert-warning">Could not load metrics: ${escapeHtml(err.message)}</div>`;
    }
  }

  // Save reminder
  root.querySelector('#rem-save-btn').addEventListener('click', async () => {
    const btn = root.querySelector('#rem-save-btn');
    const msgEl = root.querySelector('#rem-save-msg');
    btn.disabled = true;
    try {
      const payload = {
        user_id: getUserId(),
        reminder_type: root.querySelector('#rem-type').value,
        title: root.querySelector('#rem-title').value,
        schedule: root.querySelector('#rem-schedule').value,
        channel: root.querySelector('#rem-channel').value,
        patient_name: root.querySelector('#rem-patient-name').value,
        phone: root.querySelector('#rem-phone').value,
        meal_type: root.querySelector('#rem-meal-type').value,
        meal_name: root.querySelector('#rem-meal-name').value
      };
      await postJSON('/reminders', payload);
      msgEl.innerHTML = '<div class="alert alert-success">✅ Reminder saved!</div>';
      loadActiveCount();
    } catch (err) {
      msgEl.innerHTML = `<div class="alert alert-danger">❌ ${escapeHtml(err.message)}</div>`;
    } finally {
      btn.disabled = false;
    }
  });

  // Dispatch
  root.querySelector('#dispatch-btn').addEventListener('click', async () => {
    const btn = root.querySelector('#dispatch-btn');
    const msgEl = root.querySelector('#dispatch-msg');
    btn.disabled = true;
    try {
      const userId = getUserId();
      const data = await postJSON('/reminders/dispatch-active?user_id=' + encodeURIComponent(userId), {});
      msgEl.innerHTML = `<div class="alert alert-success">✅ Dispatched ${data.dispatched ?? 'all'} reminders</div>`;
      loadActiveCount();
    } catch (err) {
      msgEl.innerHTML = `<div class="alert alert-danger">❌ ${escapeHtml(err.message)}</div>`;
    } finally {
      btn.disabled = false;
    }
  });

  async function loadActiveCount() {
    const userId = getUserId();
    try {
      const data = await getJSON('/reminders/active/' + encodeURIComponent(userId));
      const count = Array.isArray(data) ? data.length : (data.count ?? 0);
      root.querySelector('#dispatch-count').textContent = `${count} active reminder(s)`;
    } catch { root.querySelector('#dispatch-count').textContent = ''; }
  }

  // Voice assistant
  root.querySelector('#voice-run-btn').addEventListener('click', async () => {
    const btn = root.querySelector('#voice-run-btn');
    const resEl = root.querySelector('#voice-result');
    btn.disabled = true;
    try {
      const payload = {
        user_id: getUserId(),
        transcript: root.querySelector('#voice-transcript').value,
        caller: root.querySelector('#voice-caller').value,
        detected_language: root.querySelector('#voice-lang').value
      };
      const data = await postJSON('/api/voice/assistant', payload);
      const intentBadge = `<span class="badge badge-info">${escapeHtml(data.intent || '—')}</span>`;
      const riskBadge = data.risk_level === 'high'
        ? `<span class="badge badge-danger">${escapeHtml(data.risk_level)}</span>`
        : `<span class="badge badge-success">${escapeHtml(data.risk_level || '—')}</span>`;
      const reviewBadge = data.human_review
        ? '<span class="badge badge-warning">Yes</span>'
        : '<span class="badge badge-success">No</span>';
      resEl.innerHTML = `
        <p><strong>Intent:</strong> ${intentBadge} &nbsp; <strong>Risk:</strong> ${riskBadge} &nbsp; <strong>Human Review:</strong> ${reviewBadge}</p>
        <div class="alert alert-info">${escapeHtml(data.answer || data.response || '—')}</div>
      `;
    } catch (err) {
      resEl.innerHTML = `<div class="alert alert-danger">❌ ${escapeHtml(err.message)}</div>`;
    } finally {
      btn.disabled = false;
    }
  });

  // Send reminder
  root.querySelector('#send-btn').addEventListener('click', async () => {
    const btn = root.querySelector('#send-btn');
    const msgEl = root.querySelector('#send-msg');
    btn.disabled = true;
    try {
      const payload = {
        user_id: getUserId(),
        channel: root.querySelector('#send-channel').value,
        message_type: root.querySelector('#send-msg-type').value,
        recipient: root.querySelector('#send-recipient').value,
        content: root.querySelector('#send-content').value
      };
      await postJSON('/api/communications/send-reminder', payload);
      msgEl.innerHTML = '<div class="alert alert-success">✅ Sent!</div>';
      loadKPI();
      loadTimeline();
    } catch (err) {
      msgEl.innerHTML = `<div class="alert alert-danger">❌ ${escapeHtml(err.message)}</div>`;
    } finally {
      btn.disabled = false;
    }
  });

  // Simulate reply
  root.querySelector('#reply-btn').addEventListener('click', async () => {
    const btn = root.querySelector('#reply-btn');
    const resEl = root.querySelector('#reply-result');
    btn.disabled = true;
    try {
      const payload = {
        user_id: getUserId(),
        channel: root.querySelector('#reply-channel').value,
        sender: root.querySelector('#reply-sender').value,
        reply: root.querySelector('#reply-text').value
      };
      const data = await postJSON('/api/communications/inbound-reply', payload);
      resEl.innerHTML = `
        <p>
          <strong>Intent:</strong> <span class="badge badge-info">${escapeHtml(data.intent || '—')}</span>
          &nbsp;<strong>Risk:</strong> <span class="badge ${data.risk_level === 'high' ? 'badge-danger' : 'badge-success'}">${escapeHtml(data.risk_level || '—')}</span>
        </p>
        <div class="alert alert-info"><strong>Recommended:</strong> ${escapeHtml(data.recommended_action || '—')}</div>
      `;
      loadTimeline();
    } catch (err) {
      resEl.innerHTML = `<div class="alert alert-danger">❌ ${escapeHtml(err.message)}</div>`;
    } finally {
      btn.disabled = false;
    }
  });

  // Timeline
  async function loadTimeline() {
    const el = root.querySelector('#comm-timeline');
    const userId = getUserId();
    try {
      const data = await getJSON('/api/communications/history/' + encodeURIComponent(userId));
      const events = (data.events || data.history || data || []).slice(-25).reverse();
      if (events.length === 0) {
        el.innerHTML = '<div class="alert alert-info">No communications yet.</div>';
        return;
      }
      el.innerHTML = `
        <table class="data-table">
          <thead>
            <tr><th>Time</th><th>Channel</th><th>Direction</th><th>Type</th><th>Status</th><th>Intent</th><th>Risk</th><th>Content</th></tr>
          </thead>
          <tbody>
            ${events.map(e => `
              <tr>
                <td>${escapeHtml(e.timestamp || e.time || '—')}</td>
                <td>${escapeHtml(e.channel || '—')}</td>
                <td>${escapeHtml(e.direction || '—')}</td>
                <td>${escapeHtml(e.type || e.message_type || '—')}</td>
                <td>${escapeHtml(e.status || '—')}</td>
                <td>${escapeHtml(e.intent || '—')}</td>
                <td><span class="badge ${e.risk_level === 'high' ? 'badge-danger' : e.risk_level === 'medium' ? 'badge-warning' : 'badge-success'}">${escapeHtml(e.risk_level || '—')}</span></td>
                <td>${escapeHtml((e.content || e.message || '').substring(0, 80))}</td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      `;
    } catch (err) {
      el.innerHTML = `<div class="alert alert-warning">Could not load timeline: ${escapeHtml(err.message)}</div>`;
    }
  }

  // Initial loads
  loadKPI();
  loadActiveCount();
  loadTimeline();
}
