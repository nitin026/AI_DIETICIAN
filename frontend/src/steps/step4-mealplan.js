// src/steps/step4-mealplan.js
import { postJSON, escapeHtml } from '../api.js';
import { state } from '../state.js';
import { goToStep, renderWizardStepper } from '../main.js';

const MEAL_TYPES = [
  { key: 'breakfast', label: '🌅 Breakfast' },
  { key: 'mid_morning_snack', label: '🍎 Mid-Morning Snack' },
  { key: 'lunch', label: '🍛 Lunch' },
  { key: 'evening_snack', label: '☕ Evening Snack' },
  { key: 'dinner', label: '🍲 Dinner' }
];

export function renderMealPlan(root) {
  renderWizardStepper(root, 4);

  const wrapper = document.createElement('div');
  wrapper.innerHTML = `
    <h2 class="step-header">🍽️ 7-Day Indian Meal Plan</h2>
    <p class="step-description">A customised weekly menu based on your health goals, allergies, cuisine preferences, and nutritional targets.</p>

    <div id="mealPlanLoading" class="loading-overlay">
      <div class="spinner"></div> Generating your personalised meal plan... This may take up to 2-3 minutes.
    </div>

    <div id="mealPlanContainer" style="display:none;">
      <!-- Day Selector Row -->
      <div class="btn-group" id="daySelector" style="margin-bottom:1.5rem; justify-content:center; width:100%;"></div>

      <!-- Meal Cards -->
      <div id="mealCardsContainer"></div>

      <!-- Daily Nutrition Summary -->
      <div class="section-card" style="margin-top:2rem;">
        <h3>Daily Nutrition Targets Compliance</h3>
        <div id="nutritionComparisonChart" style="height: 350px;"></div>
      </div>

      <!-- Download Button -->
      <div style="text-align:right; margin:1rem 0;">
        <button class="btn btn-secondary" id="downloadMealPlanBtn">📥 Download Meal Plan (JSON)</button>
      </div>

      <!-- Footer Nav Buttons -->
      <div class="btn-group" style="margin-top:1.5rem;">
        <button class="btn btn-secondary" id="backBtn">← Back</button>
        <button class="btn btn-primary" id="nextBtn">Generate Grocery List →</button>
        <button class="btn btn-secondary" id="coachBtn">💬 Ask AI Coach About Plan</button>
      </div>
    </div>
  `;
  root.appendChild(wrapper);

  document.getElementById('backBtn').addEventListener('click', () => goToStep(3));
  document.getElementById('nextBtn').addEventListener('click', () => goToStep(5));
  document.getElementById('coachBtn').addEventListener('click', () => goToStep(6));

  loadMealPlan();

  async function loadMealPlan() {
    if (state.mealPlanResponse) {
      displayMealPlan(state.mealPlanResponse);
      return;
    }

    document.getElementById('mealPlanLoading').style.display = 'flex';
    document.getElementById('mealPlanContainer').style.display = 'none';

    try {
      const payload = {
        health_profile: state.healthProfile,
        preference_profile: state.preferenceProfile,
        daily_targets: state.nutrientResponse?.daily_targets || null
      };
      const resp = await postJSON('/generate-meal-plan', payload);
      if (!resp) throw new Error('Failed to generate meal plan');
      state.mealPlanResponse = resp;
      displayMealPlan(resp);
    } catch (e) {
      document.getElementById('mealPlanLoading').innerHTML = `
        <div class="alert alert-danger">
          Failed to generate meal plan: ${escapeHtml(e.message)}
          <br><br>
          <button class="btn btn-primary" id="retryBtn">Retry</button>
        </div>
      `;
      document.getElementById('retryBtn').addEventListener('click', loadMealPlan);
    }
  }

  function displayMealPlan(resp) {
    document.getElementById('mealPlanLoading').style.display = 'none';
    document.getElementById('mealPlanContainer').style.display = 'block';

    const week = resp.week || [];
    if (!week.length) {
      document.getElementById('mealCardsContainer').innerHTML = '<div class="alert alert-warning">No plan returned.</div>';
      return;
    }

    let activeDayIdx = 0;

    // Day chips selector
    const daySelector = document.getElementById('daySelector');
    daySelector.innerHTML = '';
    week.forEach((dayData, idx) => {
      const btn = document.createElement('button');
      btn.className = `btn ${idx === activeDayIdx ? 'btn-primary' : 'btn-secondary'}`;
      btn.textContent = dayData.day || `Day ${idx + 1}`;
      btn.addEventListener('click', () => {
        activeDayIdx = idx;
        daySelector.querySelectorAll('button').forEach((b, bIdx) => {
          b.className = `btn ${bIdx === activeDayIdx ? 'btn-primary' : 'btn-secondary'}`;
        });
        renderDay(week[activeDayIdx]);
      });
      daySelector.appendChild(btn);
    });

    // Download button handler
    document.getElementById('downloadMealPlanBtn').addEventListener('click', () => {
      const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(resp, null, 2));
      const downloadAnchor = document.createElement('a');
      downloadAnchor.setAttribute("href", dataStr);
      downloadAnchor.setAttribute("download", "meal_plan.json");
      document.body.appendChild(downloadAnchor);
      downloadAnchor.click();
      downloadAnchor.remove();
    });

    renderDay(week[activeDayIdx]);
  }

  function renderDay(dayData) {
    const cardsContainer = document.getElementById('mealCardsContainer');
    cardsContainer.innerHTML = '';

    MEAL_TYPES.forEach(mealType => {
      const meal = dayData[mealType.key];
      if (!meal) return;

      const card = document.createElement('div');
      card.className = 'section-card';
      
      const ingredientsHTML = (meal.ingredients || [])
        .map(i => `<span class="chip" style="font-size:0.8rem;">${escapeHtml(i)}</span>`).join('');
      
      const stepsHTML = (meal.recipe_steps || [])
        .map(s => `<li>${escapeHtml(s)}</li>`).join('');

      card.innerHTML = `
        <div style="display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid var(--border-subtle); padding-bottom:0.8rem; margin-bottom:1rem;">
          <h3 style="margin:0; font-size:1.25rem;">${mealType.label} — ${escapeHtml(meal.name || 'Suggested meal')}</h3>
          <span class="badge badge-info">${meal.difficulty || 'Easy'}</span>
        </div>

        <div class="form-row form-row-2">
          <!-- Left Info: Recipe & Ingredients -->
          <div>
            <p style="font-weight:600; margin-bottom:0.3rem;">📋 Ingredients:</p>
            <div style="margin-bottom:1rem;">${ingredientsHTML}</div>
            
            ${stepsHTML ? `
              <p style="font-weight:600; margin-bottom:0.3rem;">🍳 Recipe Steps:</p>
              <ol style="padding-left:1.2rem; font-size:0.9rem; color:var(--text-secondary); margin-bottom:1rem;">${stepsHTML}</ol>
            ` : ''}

            <p style="font-size:0.85rem; color:var(--text-muted);">
              ⏱️ Preparation Time: ${meal.preparation_time_minutes || 15} mins | 💰 Cost: ₹${meal.estimated_cost_inr || '-'}
            </p>
            ${meal.youtube_url ? `
              <a href="${escapeHtml(meal.youtube_url)}" target="_blank" class="btn btn-secondary btn-sm" style="margin-top:0.5rem; display:inline-flex;">🎥 Video Recipe</a>
            ` : ''}
          </div>

          <!-- Right Info: Macro values -->
          <div>
            <p style="font-weight:600; margin-bottom:0.5rem; text-align:center;">📊 Nutrition (g):</p>
            <div class="metrics-row" style="grid-template-columns: 1fr 1fr; gap:0.5rem;">
              <div class="metric-card primary" style="padding:0.6rem;">
                <div class="metric-value" style="font-size:1.2rem;">${meal.calories || 0}</div>
                <div class="metric-label" style="font-size:0.65rem;">Calories</div>
              </div>
              <div class="metric-card success" style="padding:0.6rem;">
                <div class="metric-value" style="font-size:1.2rem;">${meal.protein_g || 0}g</div>
                <div class="metric-label" style="font-size:0.65rem;">Protein</div>
              </div>
              <div class="metric-card warning" style="padding:0.6rem;">
                <div class="metric-value" style="font-size:1.2rem;">${meal.carbs_g || 0}g</div>
                <div class="metric-label" style="font-size:0.65rem;">Carbs</div>
              </div>
              <div class="metric-card danger" style="padding:0.6rem;">
                <div class="metric-value" style="font-size:1.2rem;">${meal.fat_g || 0}g</div>
                <div class="metric-label" style="font-size:0.65rem;">Fat</div>
              </div>
            </div>
          </div>
        </div>

        <!-- Inline feedback form -->
        <div class="expandable" style="margin-top:1.2rem; border-top:1px solid var(--border-subtle); padding-top:0.8rem;">
          <div class="expandable-header" style="padding:0.4rem; background:transparent;">
            <span style="font-size:0.85rem; color:var(--text-secondary);">⭐ Rate this meal suggestion</span>
            <span>▼</span>
          </div>
          <div class="expandable-body" style="padding: 0.8rem 0 0 0;">
            <div class="form-row form-row-3">
              <div class="form-group">
                <label>Rating (1-5)</label>
                <select class="rating-select">
                  <option value="5">⭐⭐⭐⭐⭐ Excellent</option>
                  <option value="4">⭐⭐⭐⭐ Good</option>
                  <option value="3" selected>⭐⭐⭐ Average</option>
                  <option value="2">⭐⭐ Fair</option>
                  <option value="1">⭐ Poor</option>
                </select>
              </div>
              <div class="form-group">
                <label>Preference</label>
                <select class="liked-select">
                  <option value="liked" selected>Liked</option>
                  <option value="neutral">Neutral</option>
                  <option value="disliked">Disliked</option>
                </select>
              </div>
              <div class="form-group">
                <label>Digestion Status</label>
                <select class="digestion-select">
                  <option value="comfortable" selected>Comfortable</option>
                  <option value="heavy">Heavy</option>
                  <option value="acidic">Acidic</option>
                  <option value="bloated">Bloated</option>
                </select>
              </div>
            </div>
            <div class="form-group">
              <label>Feedback Notes</label>
              <input type="text" class="notes-input" placeholder="What did you like or change?..." />
            </div>
            <button class="btn btn-secondary btn-sm submit-feedback-btn">Submit Rating</button>
            <div class="feedback-status" style="margin-top:0.4rem;"></div>
          </div>
        </div>
      `;

      // Accordion handler
      card.querySelector('.expandable-header').addEventListener('click', () => {
        card.querySelector('.expandable').classList.toggle('open');
      });

      // Feedback submission
      card.querySelector('.submit-feedback-btn').addEventListener('click', async () => {
        const rating = Number(card.querySelector('.rating-select').value);
        const likedVal = card.querySelector('.liked-select').value;
        const digestion = card.querySelector('.digestion-select').value;
        const notes = card.querySelector('.notes-input').value;

        const payload = {
          user_id: state.userId,
          date: new Date().toISOString().split('T')[0],
          day: dayData.day,
          meal_type: mealType.key,
          meal_name: meal.name,
          rating,
          liked: likedVal === 'liked',
          digestion,
          notes
        };

        const statusDiv = card.querySelector('.feedback-status');
        statusDiv.innerHTML = '<span style="color:var(--text-muted);">Saving feedback...</span>';

        try {
          const res = await postJSON('/feedback', payload);
          if (res && res.saved) {
            statusDiv.innerHTML = '<span class="text-success">✔ Feedback saved successfully!</span>';
            setTimeout(() => { statusDiv.innerHTML = ''; }, 3000);
          } else {
            throw new Error('Save failed');
          }
        } catch (e) {
          statusDiv.innerHTML = `<span class="text-danger">❌ Failed to save: ${escapeHtml(e.message)}</span>`;
        }
      });

      cardsContainer.appendChild(card);
    });

    // Comparison Chart (Actual vs Target)
    const targets = state.nutrientResponse?.daily_targets || {};
    const totals = dayData.daily_totals || {};

    const categories = ['Calories (kcal)', 'Protein (g)', 'Carbs (g)', 'Fat (g)', 'Fiber (g)'];
    const targetValues = [
      targets.calories || 2000,
      targets.protein_g || 60,
      targets.carbs_g || 250,
      targets.fat_g || 65,
      targets.fiber_g || 30
    ];
    const actualValues = [
      totals.calories || 0,
      totals.protein_g || 0,
      totals.carbs_g || 0,
      totals.fat_g || 0,
      totals.fiber_g || 0
    ];

    Plotly.newPlot('nutritionComparisonChart', [
      {
        x: categories,
        y: targetValues,
        name: 'Target Targets',
        type: 'bar',
        marker: { color: 'rgba(255,255,255,0.08)', line: { color: '#94a3b8', width: 1 } }
      },
      {
        x: categories,
        y: actualValues,
        name: 'Actual in Plan',
        type: 'bar',
        marker: { color: '#2dd4a8' }
      }
    ], {
      barmode: 'group',
      paper_bgcolor: 'transparent',
      plot_bgcolor: 'transparent',
      font: { color: '#94a3b8', family: 'Inter' },
      xaxis: { gridcolor: 'rgba(255,255,255,0.03)' },
      yaxis: { gridcolor: 'rgba(255,255,255,0.06)' },
      margin: { t: 30, b: 40, l: 40, r: 20 },
      legend: { orientation: 'h', y: 1.1 }
    });
  }
}
