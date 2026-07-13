// src/steps/step1-profile.js
import { postJSON, postFile, getJSON, escapeHtml } from '../api.js';
import { state } from '../state.js';
import { goToStep, renderWizardStepper } from '../main.js';

const DISEASE_OPTIONS = [
  'Type-2 Diabetes', 'Prediabetes', 'Hypertension', 'High Cholesterol',
  'High Triglycerides', 'Hypothyroidism', 'Anemia', 'Chronic Kidney Disease',
  'Vitamin D Deficiency', 'Vitamin B12 Deficiency', 'Obesity', 'Underweight'
];

const ADDICTION_OPTIONS = ['never', 'monthly', 'weekly', 'daily'];

export function renderProfile(root) {
  renderWizardStepper(root, 1);

  const wrapper = document.createElement('div');
  wrapper.innerHTML = `
    <h2 class="step-header">📋 Health Profile</h2>
    <p class="step-description">Complete your health profile to receive personalised nutrition recommendations based on Indian dietary guidelines (ICMR/NIN).</p>

    <!-- Lab Report Upload -->
    <div class="section-card">
      <h3>📄 Lab Report Upload</h3>
      <p class="step-description">Upload your recent blood work or health report to auto-extract biomarkers.</p>
      <div class="form-group">
        <label>Select Report File</label>
        <input type="file" id="labReportFile" accept=".pdf,.png,.jpg,.jpeg" />
      </div>
      <button class="btn btn-primary" id="extractBiomarkersBtn">🔬 Extract Biomarkers</button>
      <div id="biomarkerResults"></div>
      <div id="inferredConditions"></div>
    </div>

    <!-- Health Form -->
    <div class="section-card">
      <h3>🏥 Personal Health Information</h3>

      <div class="form-row form-row-3">
        <div class="form-group">
          <label for="profileAge">Age</label>
          <input type="number" id="profileAge" min="5" max="120" value="30" />
        </div>
        <div class="form-group">
          <label for="profileGender">Gender</label>
          <select id="profileGender">
            <option value="male">Male</option>
            <option value="female">Female</option>
            <option value="other">Other</option>
          </select>
        </div>
        <div class="form-group">
          <label for="profileOccupation">Occupation</label>
          <input type="text" id="profileOccupation" value="Software Engineer" />
        </div>
      </div>

      <div class="form-row form-row-3">
        <div class="form-group">
          <label for="profileHeight">Height (cm)</label>
          <input type="number" id="profileHeight" min="50" max="250" step="0.5" value="170" />
        </div>
        <div class="form-group">
          <label for="profileWeight">Weight (kg)</label>
          <input type="number" id="profileWeight" min="10" max="300" step="0.5" value="70" />
        </div>
        <div class="form-group">
          <label for="profileActivity">Activity Level</label>
          <select id="profileActivity">
            <option value="sedentary">Sedentary</option>
            <option value="lightly_active">Lightly Active</option>
            <option value="moderately_active" selected>Moderately Active</option>
            <option value="very_active">Very Active</option>
            <option value="extra_active">Extra Active</option>
          </select>
        </div>
      </div>

      <div class="form-group">
        <label>BMR Equation</label>
        <div class="form-row">
          <label style="display:inline-flex;align-items:center;gap:0.5rem;cursor:pointer;">
            <input type="radio" name="bmrEquation" value="mifflin_st_jeor" checked /> Mifflin-St Jeor
          </label>
          <label style="display:inline-flex;align-items:center;gap:0.5rem;cursor:pointer;">
            <input type="radio" name="bmrEquation" value="icmr_nin_who_fao_unu" /> ICMR / NIN / WHO-FAO-UNU
          </label>
        </div>
      </div>

      <div class="form-row form-row-2">
        <div class="form-group">
          <label>Known Health Conditions</label>
          <div id="diseaseCheckboxes" style="display:grid;grid-template-columns:1fr 1fr;gap:0.4rem;">
            ${DISEASE_OPTIONS.map(d => {
              const checked = (state.inferredConditions || []).some(ic =>
                ic.toLowerCase() === d.toLowerCase()
              ) ? 'checked' : '';
              return `<label style="display:inline-flex;align-items:center;gap:0.4rem;cursor:pointer;font-size:0.9rem;">
                <input type="checkbox" value="${d}" ${checked} /> ${d}
              </label>`;
            }).join('')}
          </div>
        </div>
        <div style="display:flex;flex-direction:column;gap:1rem;">
          <div class="form-group">
            <label for="otherDiseases">Other Conditions</label>
            <textarea id="otherDiseases" rows="2" placeholder="e.g. PCOD, Fatty Liver..."></textarea>
          </div>
          <div class="form-group">
            <label for="medications">Medications (comma-separated)</label>
            <textarea id="medications" rows="2" placeholder="e.g. Metformin, Thyronorm 50mcg..."></textarea>
          </div>
        </div>
      </div>

      <h4 style="margin-top:1rem;">🚬 Lifestyle / Addictions</h4>
      <div class="form-row form-row-3">
        <div class="form-group">
          <label for="profileSmoking">Smoking</label>
          <select id="profileSmoking">
            ${ADDICTION_OPTIONS.map(o => `<option value="${o}">${o.charAt(0).toUpperCase() + o.slice(1)}</option>`).join('')}
          </select>
        </div>
        <div class="form-group">
          <label for="profileAlcohol">Alcohol</label>
          <select id="profileAlcohol">
            ${ADDICTION_OPTIONS.map(o => `<option value="${o}">${o.charAt(0).toUpperCase() + o.slice(1)}</option>`).join('')}
          </select>
        </div>
        <div class="form-group">
          <label for="profileTobacco">Tobacco</label>
          <select id="profileTobacco">
            ${ADDICTION_OPTIONS.map(o => `<option value="${o}">${o.charAt(0).toUpperCase() + o.slice(1)}</option>`).join('')}
          </select>
        </div>
      </div>

      <div id="bmiDisplay" style="margin:1rem 0;"></div>

      <button class="btn btn-primary" id="saveProfileBtn" style="width:100%;">Save &amp; Continue →</button>
    </div>
  `;
  root.appendChild(wrapper);

  // --- Extract Biomarkers ---
  document.getElementById('extractBiomarkersBtn').addEventListener('click', async () => {
    const fileInput = document.getElementById('labReportFile');
    if (!fileInput.files.length) {
      document.getElementById('biomarkerResults').innerHTML =
        '<div class="alert alert-warning">Please select a file first.</div>';
      return;
    }

    const btn = document.getElementById('extractBiomarkersBtn');
    btn.disabled = true;
    btn.textContent = 'Extracting...';

    try {
      const resp = await postFile('/api/upload-report', fileInput.files[0]);
      state.reportResponse = resp;
      state.inferredConditions = resp.inferred_conditions || [];

      // Display biomarkers table
      const biomarkers = resp.biomarkers || resp.extracted_biomarkers || [];
      if (biomarkers.length) {
        let tableHTML = `<table class="data-table">
          <thead><tr><th>Biomarker</th><th>Value</th><th>Status</th></tr></thead><tbody>`;
        biomarkers.forEach(b => {
          const status = (b.status || '').toLowerCase();
          const badgeClass = (status === 'high' || status === 'low') ? 'badge badge-danger' : 'badge badge-success';
          tableHTML += `<tr>
            <td>${escapeHtml(b.name || b.biomarker || '')}</td>
            <td>${escapeHtml(String(b.value || ''))}</td>
            <td><span class="${badgeClass}">${escapeHtml(b.status || 'Normal')}</span></td>
          </tr>`;
        });
        tableHTML += '</tbody></table>';
        document.getElementById('biomarkerResults').innerHTML = tableHTML;
      }

      // Display inferred conditions as chips
      if (state.inferredConditions.length) {
        document.getElementById('inferredConditions').innerHTML =
          '<p style="margin-top:0.8rem;"><strong>Inferred Conditions:</strong></p>' +
          state.inferredConditions.map(c => `<span class="chip">${escapeHtml(c)}</span>`).join(' ');

        // Pre-check matching disease checkboxes
        const checkboxes = document.querySelectorAll('#diseaseCheckboxes input[type="checkbox"]');
        checkboxes.forEach(cb => {
          if (state.inferredConditions.some(ic => ic.toLowerCase() === cb.value.toLowerCase())) {
            cb.checked = true;
          }
        });
      }
    } catch (e) {
      document.getElementById('biomarkerResults').innerHTML =
        `<div class="alert alert-danger">Failed to extract biomarkers: ${escapeHtml(e.message)}</div>`;
    } finally {
      btn.disabled = false;
      btn.textContent = '🔬 Extract Biomarkers';
    }
  });

  // --- Save & Continue ---
  document.getElementById('saveProfileBtn').addEventListener('click', () => {
    const age = +document.getElementById('profileAge').value;
    const gender = document.getElementById('profileGender').value;
    const occupation = document.getElementById('profileOccupation').value;
    const height_cm = +document.getElementById('profileHeight').value;
    const weight_kg = +document.getElementById('profileWeight').value;
    const activity_level = document.getElementById('profileActivity').value;
    const bmr_equation = document.querySelector('input[name="bmrEquation"]:checked')?.value || 'mifflin_st_jeor';

    // Collect diseases
    const checkedDiseases = [];
    document.querySelectorAll('#diseaseCheckboxes input[type="checkbox"]:checked').forEach(cb => {
      checkedDiseases.push(cb.value);
    });
    const otherText = document.getElementById('otherDiseases').value.trim();
    if (otherText) {
      otherText.split(',').forEach(d => {
        const trimmed = d.trim();
        if (trimmed) checkedDiseases.push(trimmed);
      });
    }

    // Medications
    const medsText = document.getElementById('medications').value.trim();
    const medications = medsText ? medsText.split(',').map(m => m.trim()).filter(Boolean) : [];

    // Addictions
    const smoking = document.getElementById('profileSmoking').value;
    const alcohol = document.getElementById('profileAlcohol').value;
    const tobacco = document.getElementById('profileTobacco').value;

    // BMI
    const bmi = weight_kg / Math.pow(height_cm / 100, 2);
    const bmiRounded = Math.round(bmi * 10) / 10;
    let bmiCategory = 'Normal';
    if (bmi < 18.5) bmiCategory = 'Underweight';
    else if (bmi < 25) bmiCategory = 'Normal';
    else if (bmi < 30) bmiCategory = 'Overweight';
    else bmiCategory = 'Obese';

    const badgeType = bmiCategory === 'Normal' ? 'badge-success' :
                      bmiCategory === 'Overweight' ? 'badge-warning' : 'badge-danger';

    document.getElementById('bmiDisplay').innerHTML = `
      <div class="metric-card" style="display:inline-block;">
        <div class="metric-value">${bmiRounded}</div>
        <div class="metric-label">BMI <span class="badge ${badgeType}">${bmiCategory}</span></div>
      </div>
    `;

    state.healthProfile = {
      age,
      gender,
      occupation,
      height_cm,
      weight_kg,
      activity_level,
      bmr_equation,
      diseases: checkedDiseases,
      medications,
      smoking,
      alcohol,
      tobacco,
      bmi: bmiRounded
    };

    goToStep(2);
  });
}
