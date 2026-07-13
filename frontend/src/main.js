/**
 * AI Dietitian — Main Orchestrator
 * Manages sidebar navigation and step rendering.
 */

import { state } from './state.js';
import { renderProfile } from './steps/step1-profile.js';
import { renderPreferences } from './steps/step2-preferences.js';
import { renderNutrients } from './steps/step3-nutrients.js';
import { renderMealPlan } from './steps/step4-mealplan.js';
import { renderGrocery } from './steps/step5-grocery.js';
import { renderChat } from './steps/step6-chat.js';
import { renderAdherence } from './steps/step7-adherence.js';
import { renderInsights } from './steps/step8-insights.js';
import { renderCommunications } from './steps/step9-communications.js';
import { renderDoctor } from './steps/step10-doctor.js';
import { renderObservability } from './steps/step11-observability.js';

/* ── Step definitions ─────────────────────────────────────────── */

const STEPS = [
  { id: 1,  label: '📝 Health Profile',       render: renderProfile },
  { id: 2,  label: '🥑 Preferences & Pantry', render: renderPreferences },
  { id: 3,  label: '🔬 Nutrient Analysis',    render: renderNutrients },
  { id: 4,  label: '🍽️ Meal Plan',            render: renderMealPlan },
  { id: 5,  label: '🛒 Grocery List',         render: renderGrocery },
  { id: 6,  label: '💬 AI Coach Chat',        render: renderChat },
  { id: 7,  label: '📅 Adherence Calendar',   render: renderAdherence },
  { id: 8,  label: '📊 Health Insights',      render: renderInsights },
  { id: 9,  label: '📞 Communications',       render: renderCommunications },
  { id: 10, label: '👨‍⚕️ Doctor Dashboard',    render: renderDoctor },
  { id: 11, label: '🔍 Observability',        render: renderObservability },
];

/* ── Sidebar ──────────────────────────────────────────────────── */

function initSidebar() {
  const nav = document.getElementById('sidebarNav');
  if (!nav) return;
  nav.innerHTML = '';

  for (const step of STEPS) {
    const btn = document.createElement('button');
    btn.textContent = step.label;
    btn.className = step.id === state.step ? 'active' : '';
    btn.addEventListener('click', () => goToStep(step.id));
    nav.appendChild(btn);
  }
}

/* ── Navigation ───────────────────────────────────────────────── */

export function goToStep(id) {
  state.step = id;
  initSidebar();
  renderCurrentStep();
}

function renderCurrentStep() {
  const root = document.getElementById('contentArea');
  if (!root) return;
  root.innerHTML = '';

  const stepDef = STEPS.find((s) => s.id === state.step);
  if (stepDef && typeof stepDef.render === 'function') {
    stepDef.render(root);
  } else {
    root.innerHTML = '<p style="color:var(--text-muted)">Step not found.</p>';
  }
}

/* ── Wizard Stepper (steps 1-5) ───────────────────────────────── */

const WIZARD_LABELS = ['Profile', 'Preferences', 'Nutrients', 'Meal Plan', 'Grocery'];

export function renderWizardStepper(root, current) {
  const container = document.createElement('div');
  container.className = 'stepper-container';

  for (let i = 0; i < WIZARD_LABELS.length; i++) {
    const stepNum = i + 1;

    // Step item
    const item = document.createElement('div');
    item.className = 'step-item';
    if (stepNum === current) item.classList.add('active');
    else if (stepNum < current) item.classList.add('done');

    const icon = document.createElement('div');
    icon.className = 'step-icon';
    icon.textContent = stepNum < current ? '✓' : stepNum;

    const label = document.createElement('div');
    label.className = 'step-label';
    label.textContent = WIZARD_LABELS[i];

    item.appendChild(icon);
    item.appendChild(label);
    container.appendChild(item);

    // Connecting line (except after last)
    if (i < WIZARD_LABELS.length - 1) {
      const line = document.createElement('div');
      line.className = 'step-line';
      if (stepNum < current) line.classList.add('filled');
      container.appendChild(line);
    }
  }

  root.appendChild(container);
}

/* ── Init ─────────────────────────────────────────────────────── */

initSidebar();
renderCurrentStep();
