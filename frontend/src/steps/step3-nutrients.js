// src/steps/step3-nutrients.js
import { postJSON, escapeHtml } from '../api.js';
import { state } from '../state.js';
import { goToStep, renderWizardStepper } from '../main.js';

const GROUPS = {
  Vitamins: [
    "vitamin_a_mcg", "vitamin_b1_mg", "vitamin_b2_mg", "vitamin_b3_mg",
    "vitamin_b5_mg", "vitamin_b6_mg", "vitamin_b7_mcg", "vitamin_b9_mcg",
    "vitamin_b12_mcg", "vitamin_c_mg", "vitamin_d_iu", "vitamin_e_mg", "vitamin_k_mcg"
  ],
  Minerals: [
    "calcium_mg", "iron_mg", "magnesium_mg", "zinc_mg", "selenium_mcg",
    "copper_mg", "phosphorus_mg", "iodine_mcg", "manganese_mg",
    "chromium_mcg", "molybdenum_mcg"
  ],
  Electrolytes: [
    "sodium_mg", "potassium_mg", "chloride_mg"
  ],
  "Metabolic Targets": [
    "choline_mg", "omega_3_g", "omega_6_g", "glycemic_load", "glycemic_index"
  ]
};

const LABELS = {
  sodium_mg: "Sodium", potassium_mg: "Potassium", iron_mg: "Iron", calcium_mg: "Calcium",
  vitamin_d_iu: "Vitamin D", vitamin_a_mcg: "Vitamin A", vitamin_b1_mg: "Vitamin B1",
  vitamin_b2_mg: "Vitamin B2", vitamin_b3_mg: "Vitamin B3", vitamin_b5_mg: "Vitamin B5",
  vitamin_b6_mg: "Vitamin B6", vitamin_b7_mcg: "Biotin", vitamin_b9_mcg: "Folate",
  vitamin_b12_mcg: "Vitamin B12", vitamin_c_mg: "Vitamin C", vitamin_e_mg: "Vitamin E",
  vitamin_k_mcg: "Vitamin K", magnesium_mg: "Magnesium", zinc_mg: "Zinc",
  selenium_mcg: "Selenium", copper_mg: "Copper", phosphorus_mg: "Phosphorus",
  iodine_mcg: "Iodine", chloride_mg: "Chloride", manganese_mg: "Manganese",
  chromium_mcg: "Chromium", molybdenum_mcg: "Molybdenum", choline_mg: "Choline",
  omega_3_g: "Omega-3", omega_6_g: "Omega-6", glycemic_load: "Glycemic Load",
  glycemic_index: "Glycemic Index"
};

function formatValue(key, val) {
  if (val === null || val === undefined) return '-';
  const num = Number(val);
  if (isNaN(num)) return val;
  const suffix = key.split('_').pop();
  const unit = suffix === 'mcg' ? 'mcg' : suffix === 'mg' ? 'mg' : suffix === 'ml' ? 'ml' : suffix === 'g' ? 'g' : suffix === 'iu' ? 'IU' : '';
  return `${num.toFixed(num < 10 ? 1 : 0)} ${unit}`.trim();
}

export function renderNutrients(root) {
  renderWizardStepper(root, 3);

  const wrapper = document.createElement('div');
  wrapper.innerHTML = `
    <h2 class="step-header">🔬 Nutrient Analysis</h2>
    <p class="step-description">Personalised micronutrient and macronutrient targets computed dynamically.</p>
    
    <div id="nutrientsLoading" class="loading-overlay">
      <div class="spinner"></div> Calculating clinical targets...
    </div>
    
    <div id="nutrientsContainer" style="display:none;">
      <!-- Macro metrics -->
      <div class="metrics-row" id="macroMetrics"></div>

      <!-- Secondary metrics -->
      <div class="metrics-row" id="secondaryMetrics"></div>

      <!-- Charts Row -->
      <div class="form-row form-row-2">
        <div class="chart-container">
          <h4>🔥 Calorie Distribution</h4>
          <div id="caloriePieChart" style="height: 300px;"></div>
        </div>
        <div class="chart-container">
          <h4>📊 Nutrient Adequacy Index</h4>
          <div id="adequacyRadarChart" style="height: 300px;"></div>
        </div>
      </div>

      <!-- Micro Tabs Section -->
      <div class="section-card">
        <h3>🎯 Priority Micronutrients &amp; Targets</h3>
        <div class="tab-bar" id="microTabBar"></div>
        <div id="microTabContents"></div>
      </div>

      <!-- Expandable Alerts -->
      <div id="alertExpandables"></div>

      <!-- Footer Buttons -->
      <div class="btn-group" style="margin-top:1.5rem;">
        <button class="btn btn-secondary" id="backBtn">← Back</button>
        <button class="btn btn-secondary" id="refreshBtn">🔄 Refresh Analysis</button>
        <button class="btn btn-primary" id="generateMealPlanBtn">Generate 7-Day Meal Plan →</button>
      </div>
    </div>
  `;
  root.appendChild(wrapper);

  document.getElementById('backBtn').addEventListener('click', () => goToStep(2));
  document.getElementById('refreshBtn').addEventListener('click', loadNutrients);
  document.getElementById('generateMealPlanBtn').addEventListener('click', () => goToStep(4));

  loadNutrients();

  async function loadNutrients() {
    document.getElementById('nutrientsLoading').style.display = 'flex';
    document.getElementById('nutrientsContainer').style.display = 'none';

    try {
      const resp = await postJSON('/predict-nutrients', { health_profile: state.healthProfile });
      if (!resp) throw new Error('No response from backend');
      state.nutrientResponse = resp;
      displayNutrients(resp);
    } catch (e) {
      document.getElementById('nutrientsLoading').innerHTML = `
        <div class="alert alert-danger">
          Failed to calculate nutrients: ${escapeHtml(e.message)}
          <br><br>
          <button class="btn btn-primary" id="retryBtn">Retry</button>
        </div>
      `;
      document.getElementById('retryBtn').addEventListener('click', loadNutrients);
    }
  }

  function displayNutrients(resp) {
    document.getElementById('nutrientsLoading').style.display = 'none';
    document.getElementById('nutrientsContainer').style.display = 'block';

    const targets = resp.daily_targets || {};
    
    // Macro Metrics
    document.getElementById('macroMetrics').innerHTML = `
      <div class="metric-card primary">
        <div class="metric-value">${targets.calories || 2000}</div>
        <div class="metric-label">Calories (kcal)</div>
      </div>
      <div class="metric-card success">
        <div class="metric-value">${targets.protein_g || 60}g</div>
        <div class="metric-label">Protein</div>
      </div>
      <div class="metric-card warning">
        <div class="metric-value">${targets.carbs_g || 250}g</div>
        <div class="metric-label">Carbs</div>
      </div>
      <div class="metric-card danger">
        <div class="metric-value">${targets.fat_g || 65}g</div>
        <div class="metric-label">Fat</div>
      </div>
    `;

    // Secondary Metrics
    document.getElementById('secondaryMetrics').innerHTML = `
      <div class="metric-card">
        <div class="metric-value">${targets.fiber_g || 30}g</div>
        <div class="metric-label">Fiber</div>
      </div>
      <div class="metric-card">
        <div class="metric-value">${(targets.water_ml || 2500) / 1000}L</div>
        <div class="metric-label">Water Target</div>
      </div>
      <div class="metric-card">
        <div class="metric-value">${resp.bmr ? resp.bmr.toFixed(0) : '-'}</div>
        <div class="metric-label">BMR (kcal)</div>
      </div>
    `;

    // Calorie Pie Chart
    const proteinCal = (targets.protein_g || 60) * 4;
    const carbsCal = (targets.carbs_g || 250) * 4;
    const fatCal = (targets.fat_g || 65) * 9;
    
    Plotly.newPlot('caloriePieChart', [{
      values: [proteinCal, carbsCal, fatCal],
      labels: ['Protein', 'Carbs', 'Fat'],
      type: 'pie',
      marker: { colors: ['#2dd4a8', '#a78bfa', '#f472b6'] },
      textinfo: 'percent+label',
      hole: 0.4
    }], {
      paper_bgcolor: 'transparent',
      plot_bgcolor: 'transparent',
      font: { color: '#94a3b8', family: 'Sora' },
      margin: { t: 20, b: 20, l: 20, r: 20 },
      showlegend: false
    });

    // Radar Chart (Nutrient Adequacy)
    const adequacy = resp.nutrient_adequacy || {};
    const radarLabels = [];
    const radarValues = [];
    
    Object.entries(adequacy).slice(0, 12).forEach(([k, info]) => {
      radarLabels.push(LABELS[k] || k);
      radarValues.push(info.score !== undefined ? info.score : 80); // Fallback score
    });

    if (radarLabels.length > 0) {
      Plotly.newPlot('adequacyRadarChart', [{
        type: 'scatterpolar',
        r: radarValues,
        theta: radarLabels,
        fill: 'toself',
        fillcolor: 'rgba(45, 212, 168, 0.2)',
        line: { color: '#2dd4a8' }
      }], {
        polar: {
          radialaxis: { visible: true, range: [0, 100], gridcolor: 'rgba(255,255,255,0.06)' },
          angularaxis: { gridcolor: 'rgba(255,255,255,0.06)' },
          bgcolor: 'transparent'
        },
        paper_bgcolor: 'transparent',
        font: { color: '#94a3b8', family: 'Inter', size: 10 },
        margin: { t: 40, b: 20, l: 40, r: 40 }
      });
    }

    // Tabs logic for Priority Micronutrients
    const tabNames = Object.keys(GROUPS);
    const tabBar = document.getElementById('microTabBar');
    const tabContents = document.getElementById('microTabContents');
    
    tabBar.innerHTML = '';
    tabContents.innerHTML = '';

    tabNames.forEach((groupName, idx) => {
      const btn = document.createElement('button');
      btn.className = `tab-btn ${idx === 0 ? 'active' : ''}`;
      btn.textContent = groupName;
      btn.addEventListener('click', () => {
        tabBar.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
        tabContents.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
        btn.classList.add('active');
        document.getElementById(`tab-content-${groupName.replace(/\s+/g, '')}`).classList.add('active');
      });
      tabBar.appendChild(btn);

      // Tab Content wrapper
      const contentDiv = document.createElement('div');
      contentDiv.className = `tab-content ${idx === 0 ? 'active' : ''}`;
      contentDiv.id = `tab-content-${groupName.replace(/\s+/g, '')}`;

      const microGrid = document.createElement('div');
      microGrid.className = 'micro-grid';

      GROUPS[groupName].forEach(k => {
        const val = targets[k];
        if (val !== undefined && val !== null) {
          const card = document.createElement('div');
          card.className = 'micro-card';
          
          const adequacyInfo = adequacy[k] || {};
          const foodSources = adequacyInfo.food_sources || [];
          const foodLabel = foodSources.length ? foodSources.slice(0, 3).join(', ') : 'Suggested foods';

          card.innerHTML = `
            <div class="label">${LABELS[k] || k.replace('_', ' ')}</div>
            <div class="value">${formatValue(k, val)}</div>
            <div class="hint">${escapeHtml(foodLabel)}</div>
          `;
          microGrid.appendChild(card);
        }
      });

      contentDiv.appendChild(microGrid);
      tabContents.appendChild(contentDiv);
    });

    // Alert sections
    const alertDiv = document.getElementById('alertExpandables');
    alertDiv.innerHTML = '';

    // Alerts details helper
    const alertsToRender = [
      { key: 'deficiency_risks', title: '⚠️ Nutrient Gap & Deficiency Risks', class: 'alert-warning' },
      { key: 'disease_notes', title: '💡 Disease Adjustments Applied', class: 'alert-info' },
      { key: 'medication_interactions', title: '💊 Medication Interaction Warnings', class: 'alert-danger' },
      { key: 'icmr_references', title: '📚 ICMR-NIN Guideline References', class: 'alert-info' }
    ];

    alertsToRender.forEach(a => {
      const items = resp[a.key] || [];
      if (items.length > 0) {
        const expandable = document.createElement('div');
        expandable.className = 'expandable';
        expandable.innerHTML = `
          <div class="expandable-header">
            <span>${a.title} (${items.length})</span>
            <span>▼</span>
          </div>
          <div class="expandable-body">
            ${items.map(item => `<div class="alert ${a.class}">${escapeHtml(item)}</div>`).join('')}
          </div>
        `;
        
        expandable.querySelector('.expandable-header').addEventListener('click', () => {
          expandable.classList.toggle('open');
        });
        alertDiv.appendChild(expandable);
      }
    });
  }
}
