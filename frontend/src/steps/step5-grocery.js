// src/steps/step5-grocery.js
import { postJSON, escapeHtml } from '../api.js';
import { state } from '../state.js';
import { goToStep, renderWizardStepper } from '../main.js';

const CATEGORY_ICONS = {
  Grains: '🌾',
  Protein: '🍗',
  Dairy: '🥛',
  Vegetables: '🥦',
  Fruits: '🍎',
  'Fats & Oils': '🫗',
  'Nuts & Seeds': '🥜',
  Spices: '🌶️',
  General: '🛒'
};

export function renderGrocery(root) {
  renderWizardStepper(root, 5);

  const wrapper = document.createElement('div');
  wrapper.innerHTML = `
    <h2 class="step-header">🛒 Weekly Grocery List</h2>
    <p class="step-description">A consolidated shopping list grouped by categories, estimated based on your 7-day meal plan.</p>

    <div id="groceryLoading" class="loading-overlay">
      <div class="spinner"></div> Consolidating grocery list...
    </div>

    <div id="groceryContainer" style="display:none;">
      <!-- Total Cost Metric -->
      <div class="metrics-row" style="margin-bottom:1.5rem;">
        <div class="metric-card primary">
          <div class="metric-value" id="groceryTotalCost">₹-</div>
          <div class="metric-label">Total Estimated Weekly Cost</div>
        </div>
      </div>

      <!-- Categories Container -->
      <div id="groceryCategories"></div>

      <!-- Expandable Tips -->
      <div id="groceryTipsContainer"></div>

      <!-- PDF / Download anchor -->
      <div style="text-align:right; margin:1rem 0;">
        <button class="btn btn-secondary" id="downloadGroceryTxtBtn">📥 Download Shopping List (TXT)</button>
      </div>

      <!-- Footer Buttons -->
      <div class="btn-group" style="margin-top:1.5rem;">
        <button class="btn btn-secondary" id="backBtn">← Back to Meal Plan</button>
        <button class="btn btn-danger" id="startOverBtn">🔄 Start Over</button>
      </div>
    </div>
  `;
  root.appendChild(wrapper);

  document.getElementById('backBtn').addEventListener('click', () => goToStep(4));
  document.getElementById('startOverBtn').addEventListener('click', () => {
    // Reset wizard states
    state.step = 1;
    state.reportResponse = null;
    state.inferredConditions = [];
    state.healthProfile = {};
    state.preferenceProfile = {};
    state.nutrientResponse = null;
    state.mealPlanResponse = null;
    state.groceryResponse = null;
    goToStep(1);
  });

  loadGrocery();

  async function loadGrocery() {
    if (state.groceryResponse) {
      displayGrocery(state.groceryResponse);
      return;
    }

    document.getElementById('groceryLoading').style.display = 'flex';
    document.getElementById('groceryContainer').style.display = 'none';

    try {
      const payload = {
        meal_plan: state.mealPlanResponse,
        pantry_ingredients: state.preferenceProfile.pantry_ingredients || []
      };
      // Endpoint is prefix /generate-grocery-list + path /generate-grocery-list
      const resp = await postJSON('/generate-grocery-list', payload);
      if (!resp) throw new Error('Failed to generate grocery list');
      state.groceryResponse = resp;
      displayGrocery(resp);
    } catch (e) {
      document.getElementById('groceryLoading').innerHTML = `
        <div class="alert alert-danger">
          Failed to generate grocery list: ${escapeHtml(e.message)}
          <br><br>
          <button class="btn btn-primary" id="retryBtn">Retry</button>
        </div>
      `;
      document.getElementById('retryBtn').addEventListener('click', loadGrocery);
    }
  }

  function displayGrocery(resp) {
    document.getElementById('groceryLoading').style.display = 'none';
    document.getElementById('groceryContainer').style.display = 'block';

    const cost = resp.total_estimated_cost_inr || resp.total_cost || 0;
    document.getElementById('groceryTotalCost').textContent = `₹${cost.toFixed(0)}`;

    const items = resp.items || [];
    const categoriesDiv = document.getElementById('groceryCategories');
    categoriesDiv.innerHTML = '';

    // Group items by category
    const grouped = {};
    items.forEach(item => {
      const cat = item.category || 'General';
      if (!grouped[cat]) grouped[cat] = [];
      grouped[cat].push(item);
    });

    if (items.length === 0) {
      categoriesDiv.innerHTML = '<div class="alert alert-warning">No items generated.</div>';
      return;
    }

    // Render category cards
    Object.entries(grouped).forEach(([cat, list]) => {
      const card = document.createElement('div');
      card.className = 'section-card';
      
      const icon = CATEGORY_ICONS[cat] || CATEGORY_ICONS.General;
      
      const listHTML = list.map(item => `
        <span class="grocery-badge">
          <strong>${escapeHtml(item.ingredient)}</strong>: ${escapeHtml(item.quantity || 'As needed')} 
          ${item.estimated_cost_inr ? `<span style="opacity:0.6; font-size:0.8rem; margin-left:0.2rem;">(₹${item.estimated_cost_inr})</span>` : ''}
        </span>
      `).join('');

      card.innerHTML = `
        <h3 style="margin-bottom:1rem; font-size:1.1rem; border-bottom:1px solid var(--border-subtle); padding-bottom:0.4rem;">
          ${icon} ${escapeHtml(cat)} (${list.length})
        </h3>
        <div class="grocery-grid">${listHTML}</div>
      `;
      categoriesDiv.appendChild(card);
    });

    // Render notes/tips
    const notes = resp.notes || [];
    const tipsContainer = document.getElementById('groceryTipsContainer');
    tipsContainer.innerHTML = '';
    if (notes.length > 0) {
      const exp = document.createElement('div');
      exp.className = 'expandable';
      exp.innerHTML = `
        <div class="expandable-header">
          <span>💡 Smart Grocery Tips</span>
          <span>▼</span>
        </div>
        <div class="expandable-body">
          <ul style="padding-left:1.2rem; color:var(--text-secondary); line-height:1.6;">
            ${notes.map(n => `<li>${escapeHtml(n)}</li>`).join('')}
          </ul>
        </div>
      `;
      exp.querySelector('.expandable-header').addEventListener('click', () => {
        exp.classList.toggle('open');
      });
      tipsContainer.appendChild(exp);
    }

    // Download Shopping List (TXT)
    document.getElementById('downloadGroceryTxtBtn').addEventListener('click', () => {
      let txtContent = `AI DIETITIAN - WEEKLY GROCERY LIST\n`;
      txtContent += `==================================\n`;
      txtContent += `Total Estimated Cost: Rs. ${cost.toFixed(0)}\n\n`;
      
      Object.entries(grouped).forEach(([cat, list]) => {
        txtContent += `${cat.toUpperCase()}\n`;
        txtContent += `------------------\n`;
        list.forEach(item => {
          txtContent += `- [ ] ${item.ingredient}: ${item.quantity || 'As needed'}`;
          if (item.estimated_cost_inr) txtContent += ` (Rs. ${item.estimated_cost_inr})`;
          txtContent += `\n`;
        });
        txtContent += `\n`;
      });

      if (notes.length > 0) {
        txtContent += `SMART TIPS\n`;
        txtContent += `----------\n`;
        notes.forEach(n => {
          txtContent += `* ${n}\n`;
        });
      }

      const blob = new Blob([txtContent], { type: 'text/plain;charset=utf-8' });
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement('a');
      anchor.setAttribute('href', url);
      anchor.setAttribute('download', 'grocery_list.txt');
      document.body.appendChild(anchor);
      anchor.click();
      anchor.remove();
      URL.revokeObjectURL(url);
    });
  }
}
