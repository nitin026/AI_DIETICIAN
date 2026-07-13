// src/steps/step2-preferences.js
import { postJSON, postFile, getJSON, escapeHtml } from '../api.js';
import { state } from '../state.js';
import { goToStep, renderWizardStepper } from '../main.js';

export function renderPreferences(root) {
  renderWizardStepper(root, 2);

  const wrapper = document.createElement('div');
  wrapper.innerHTML = `
    <h2 class="step-header">🥑 Preferences & Pantry</h2>
    <p class="step-description">Tell us your food preferences, dietary limits, and what's in your pantry to tailor your meal plan.</p>

    <div class="section-card">
      <h3>🍽️ Diet & Cuisine</h3>
      
      <div class="form-row form-row-3">
        <div class="form-group">
          <label for="dietaryPreference">Dietary Preference</label>
          <select id="dietaryPreference">
            <option value="vegetarian" ${state.preferenceProfile.dietary_preference === 'vegetarian' ? 'selected' : ''}>Vegetarian</option>
            <option value="eggetarian" ${state.preferenceProfile.dietary_preference === 'eggetarian' ? 'selected' : ''}>Eggetarian</option>
            <option value="non_vegetarian" ${state.preferenceProfile.dietary_preference === 'non_vegetarian' ? 'selected' : ''}>Non-Vegetarian</option>
            <option value="vegan" ${state.preferenceProfile.dietary_preference === 'vegan' ? 'selected' : ''}>Vegan</option>
          </select>
        </div>

        <div class="form-group">
          <label for="regionalCuisine">Regional Cuisine</label>
          <select id="regionalCuisine">
            <option value="North Indian" ${state.preferenceProfile.regional_cuisine === 'North Indian' ? 'selected' : ''}>North Indian</option>
            <option value="South Indian" ${state.preferenceProfile.regional_cuisine === 'South Indian' ? 'selected' : ''}>South Indian</option>
            <option value="Bengali" ${state.preferenceProfile.regional_cuisine === 'Bengali' ? 'selected' : ''}>Bengali</option>
            <option value="Gujarati" ${state.preferenceProfile.regional_cuisine === 'Gujarati' ? 'selected' : ''}>Gujarati</option>
            <option value="Maharashtrian" ${state.preferenceProfile.regional_cuisine === 'Maharashtrian' ? 'selected' : ''}>Maharashtrian</option>
            <option value="Rajasthani" ${state.preferenceProfile.regional_cuisine === 'Rajasthani' ? 'selected' : ''}>Rajasthani</option>
            <option value="Punjabi" ${state.preferenceProfile.regional_cuisine === 'Punjabi' ? 'selected' : ''}>Punjabi</option>
            <option value="Andhra" ${state.preferenceProfile.regional_cuisine === 'Andhra' ? 'selected' : ''}>Andhra</option>
            <option value="Kerala" ${state.preferenceProfile.regional_cuisine === 'Kerala' ? 'selected' : ''}>Kerala</option>
            <option value="Tamil Nadu" ${state.preferenceProfile.regional_cuisine === 'Tamil Nadu' ? 'selected' : ''}>Tamil Nadu</option>
            <option value="Other" ${state.preferenceProfile.regional_cuisine === 'Other' ? 'selected' : ''}>Other Cuisine</option>
          </select>
        </div>

        <div class="form-group">
          <label for="cookingSkill">Cooking Skill</label>
          <select id="cookingSkill">
            <option value="beginner" ${state.preferenceProfile.cooking_skill === 'beginner' ? 'selected' : ''}>Beginner</option>
            <option value="intermediate" ${state.preferenceProfile.cooking_skill === 'intermediate' ? 'selected' : ''}>Intermediate</option>
            <option value="advanced" ${state.preferenceProfile.cooking_skill === 'advanced' ? 'selected' : ''}>Advanced</option>
          </select>
        </div>
      </div>

      <div class="form-row form-row-2">
        <div class="form-group">
          <label for="budgetPreference">Budget Preference</label>
          <select id="budgetPreference">
            <option value="low" ${state.preferenceProfile.budget === 'low' ? 'selected' : ''}>Low (Budget friendly)</option>
            <option value="medium" ${state.preferenceProfile.budget === 'medium' ? 'selected' : ''}>Medium</option>
            <option value="high" ${state.preferenceProfile.budget === 'high' ? 'selected' : ''}>High</option>
          </select>
        </div>

        <div class="form-group" id="customCuisineGroup" style="display:none;">
          <label for="customCuisine">Specify Regional Cuisine</label>
          <input type="text" id="customCuisine" value="${state.preferenceProfile.regional_cuisine && !['North Indian','South Indian','Bengali','Gujarati','Maharashtrian','Rajasthani','Punjabi','Andhra','Kerala','Tamil Nadu','Other'].includes(state.preferenceProfile.regional_cuisine) ? escapeHtml(state.preferenceProfile.regional_cuisine) : ''}" placeholder="e.g. Kashmiri, Goan..." />
        </div>
      </div>
    </div>

    <div class="section-card">
      <h3>😋 Ingredients & Pantry</h3>
      
      <div class="form-row form-row-2">
        <div class="form-group">
          <label for="likes">Ingredients You Like (comma-separated)</label>
          <textarea id="likes" rows="3" placeholder="e.g. Paneer, Oats, Spinach, Apple">${(state.preferenceProfile.likes || []).join(', ')}</textarea>
        </div>
        <div class="form-group">
          <label for="dislikes">Ingredients You Dislike (comma-separated)</label>
          <textarea id="dislikes" rows="3" placeholder="e.g. Karela, Okra">${(state.preferenceProfile.dislikes || []).join(', ')}</textarea>
        </div>
      </div>

      <div class="form-row form-row-2">
        <div class="form-group">
          <label for="allergies">Allergies (comma-separated)</label>
          <textarea id="allergies" rows="3" placeholder="e.g. Peanuts, Gluten, Lactose">${(state.preferenceProfile.allergies || []).join(', ')}</textarea>
        </div>
        <div class="form-group">
          <label for="pantryIngredients">Pantry Ingredients (comma-separated)</label>
          <textarea id="pantryIngredients" rows="3" placeholder="e.g. Rice, Atta, Moong Dal, Mustard Oil">${(state.preferenceProfile.pantry_ingredients || []).join(', ')}</textarea>
        </div>
      </div>

      <div class="btn-group" style="margin-top:1.5rem;">
        <button class="btn btn-secondary" id="backBtn">← Back</button>
        <button class="btn btn-primary" id="savePrefsBtn">Save &amp; Analyse Nutrients →</button>
      </div>
    </div>
  `;
  root.appendChild(wrapper);

  // Custom cuisine toggle
  const regSelect = document.getElementById('regionalCuisine');
  const customGroup = document.getElementById('customCuisineGroup');
  
  function checkCuisineToggle() {
    if (regSelect.value === 'Other') {
      customGroup.style.display = 'block';
    } else {
      customGroup.style.display = 'none';
    }
  }

  regSelect.addEventListener('change', checkCuisineToggle);
  checkCuisineToggle(); // run on load

  // Navigation handlers
  document.getElementById('backBtn').addEventListener('click', () => {
    goToStep(1);
  });

  document.getElementById('savePrefsBtn').addEventListener('click', () => {
    const dietary_preference = document.getElementById('dietaryPreference').value;
    const regionalCuisineVal = regSelect.value;
    const regional_cuisine = regionalCuisineVal === 'Other' 
      ? (document.getElementById('customCuisine').value.trim() || 'Other') 
      : regionalCuisineVal;
    const cooking_skill = document.getElementById('cookingSkill').value;
    const budget = document.getElementById('budgetPreference').value;

    const likes = document.getElementById('likes').value.split(',')
      .map(s => s.trim()).filter(s => s.length > 0);
    const dislikes = document.getElementById('dislikes').value.split(',')
      .map(s => s.trim()).filter(s => s.length > 0);
    const allergies = document.getElementById('allergies').value.split(',')
      .map(s => s.trim()).filter(s => s.length > 0);
    const pantry_ingredients = document.getElementById('pantryIngredients').value.split(',')
      .map(s => s.trim()).filter(s => s.length > 0);

    state.preferenceProfile = {
      likes,
      dislikes,
      dietary_preference,
      allergies,
      pantry_ingredients,
      budget,
      cooking_skill,
      regional_cuisine
    };

    goToStep(3);
  });
}
