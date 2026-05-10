"""
frontend/streamlit_app.py
Multi-step Streamlit UI for the AI Dietitian application.
Run with: streamlit run frontend/streamlit_app.py
"""
from __future__ import annotations

import io
import json
from typing import Any

import plotly.graph_objects as go
import requests
import streamlit as st
from fpdf import FPDF

# ── Configuration ─────────────────────────────────────────────────────────────
import os
import streamlit as st
BACKEND_URL = st.secrets.get("BACKEND_URL", os.getenv("BACKEND_URL", "http://localhost:8000"))

DISCLAIMER = (
    "⚠️ **Medical Disclaimer:** This AI dietitian is an informational assistant "
    "and is **not** a substitute for professional medical advice, diagnosis, or treatment. "
    "Always consult a qualified healthcare provider before making dietary changes."
)

st.set_page_config(
    page_title="AI Dietitian – Powered by BioMistral",
    page_icon="🥗",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main-header {font-size:2.2rem; font-weight:700; color:#2e7d32;}
    .sub-header  {font-size:1.1rem; color:#555;}
    .metric-card {background:#f1f8e9; border-radius:10px; padding:1rem; text-align:center;}
    .disclaimer  {background:#fff3e0; border-left:4px solid #fb8c00; padding:0.8rem 1rem;
                  border-radius:4px; font-size:0.88rem;}
    .meal-card   {background:#fafafa; border:1px solid #e0e0e0; border-radius:8px;
                  padding:1rem; margin-bottom:0.6rem;}
    .grocery-badge {display:inline-block; background:#e8f5e9; color:#2e7d32;
                    border-radius:12px; padding:2px 10px; font-size:0.82rem; margin:2px;}
</style>
""", unsafe_allow_html=True)


# ── Session state defaults ────────────────────────────────────────────────────
def init_state():
    defaults = {
        "step": 1,
        "health_profile": {},
        "preference_profile": {},
        "nutrient_response": None,
        "meal_plan_response": None,
        "grocery_response": None,
        "validation_response": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()


# ── Sidebar Navigation ────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🥗 AI Dietitian")
    st.markdown("*Powered by BioMistral + ICMR-NIN 2024*")
    st.divider()
    step_labels = {
        1: "📋 Health Profile",
        2: "🥦 Preferences & Pantry",
        3: "🔬 Nutrient Analysis",
        4: "🍽️ Meal Plan",
        5: "🛒 Grocery List",
    }
    for step, label in step_labels.items():
        if st.session_state.step == step:
            st.markdown(f"**→ {label}**")
        else:
            st.markdown(f"&nbsp;&nbsp; {label}")
    st.divider()
    st.markdown(f'<div class="disclaimer">{DISCLAIMER}</div>', unsafe_allow_html=True)


# ── Helper: API calls ─────────────────────────────────────────────────────────
def api_post(endpoint: str, payload: dict) -> dict | None:
    try:
        resp = requests.post(f"{BACKEND_URL}{endpoint}", json=payload, timeout=180)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.ConnectionError:
        st.error("❌ Cannot connect to backend. Is the FastAPI server running?")
    except requests.exceptions.Timeout:
        st.error("⏱️ Request timed out. The LLM may be slow – please try again.")
    except requests.exceptions.HTTPError as e:
        st.error(f"HTTP {e.response.status_code}: {e.response.text[:300]}")
    except Exception as e:
        st.error(f"Unexpected error: {e}")
    return None


# ── Step 1: Health Profile ────────────────────────────────────────────────────
def step1_health_profile():
    st.markdown('<p class="main-header">📋 Step 1 — Health Profile</p>', unsafe_allow_html=True)
    st.markdown("Tell us about yourself so we can compute your personalised nutrient needs.")

    with st.form("health_form"):
        col1, col2, col3 = st.columns(3)
        with col1:
            age = st.number_input("Age (years)", min_value=5, max_value=120, value=30)
            gender = st.selectbox("Gender", ["male", "female", "other"])
            occupation = st.text_input("Occupation", value="Software Engineer")
        with col2:
            height = st.number_input("Height (cm)", min_value=50.0, max_value=250.0, value=170.0, step=0.5)
            weight = st.number_input("Weight (kg)", min_value=10.0, max_value=300.0, value=70.0, step=0.5)
            activity = st.selectbox(
                "Activity Level",
                ["sedentary", "lightly_active", "moderately_active", "very_active", "extra_active"],
                index=2,
            )
        with col3:
            diseases = st.text_area(
                "Diseases / Medical Conditions",
                placeholder="e.g. type-2 diabetes, hypertension",
                height=80,
            )
            medications = st.text_area(
                "Current Medications",
                placeholder="e.g. metformin 500mg, atenolol 25mg",
                height=80,
            )

        st.subheader("Addiction Frequency")
        c1, c2, c3 = st.columns(3)
        with c1:
            smoking = st.selectbox("Smoking", ["never", "monthly", "weekly", "daily"])
        with c2:
            alcohol = st.selectbox("Alcohol", ["never", "monthly", "weekly", "daily"])
        with c3:
            tobacco = st.selectbox("Tobacco", ["never", "monthly", "weekly", "daily"])

        submitted = st.form_submit_button("✅ Save & Continue →", use_container_width=True)

    if submitted:
        st.session_state.health_profile = {
            "age": int(age),
            "gender": gender,
            "height_cm": float(height),
            "weight_kg": float(weight),
            "occupation": occupation,
            "activity_level": activity,
            "diseases": [d.strip() for d in diseases.split(",") if d.strip()],
            "medications": [m.strip() for m in medications.split(",") if m.strip()],
            "addictions": {"smoking": smoking, "alcohol": alcohol, "tobacco": tobacco},
        }
        bmi = weight / (height / 100) ** 2
        st.success(f"✅ Profile saved! BMI = **{bmi:.1f}**")
        st.session_state.step = 2
        st.rerun()


# ── Step 2: Preferences & Pantry ─────────────────────────────────────────────
def step2_preferences():
    st.markdown('<p class="main-header">🥦 Step 2 — Preferences & Pantry</p>', unsafe_allow_html=True)

    with st.form("pref_form"):
        col1, col2 = st.columns(2)
        with col1:
            dietary = st.selectbox("Dietary Preference", ["vegetarian", "eggetarian", "non_vegetarian", "vegan"])
            regional = st.selectbox(
                "Regional Cuisine",
                ["North Indian", "South Indian", "Bengali", "Gujarati", "Maharashtrian",
                 "Rajasthani", "Punjabi", "Andhra", "Kerala", "Tamil Nadu"],
            )
            skill = st.selectbox("Cooking Skill", ["beginner", "intermediate", "advanced"])
            budget = st.selectbox("Budget Preference", ["low", "medium", "high"])
        with col2:
            likes = st.text_area("Food Likes", placeholder="e.g. dal, rice, chapati, idli", height=80)
            dislikes = st.text_area("Food Dislikes", placeholder="e.g. bitter gourd, okra", height=80)
            allergies = st.text_area("Allergies", placeholder="e.g. peanuts, shellfish", height=50)

        pantry_raw = st.text_area(
            "🧺 Pantry Ingredients (comma-separated)",
            placeholder="e.g. rice, dal, onion, tomato, ginger, garlic, oil, turmeric",
            height=80,
        )

        col_back, col_next = st.columns(2)
        with col_back:
            back = st.form_submit_button("← Back", use_container_width=True)
        with col_next:
            submitted = st.form_submit_button("✅ Save & Analyse Nutrients →", use_container_width=True)

    if back:
        st.session_state.step = 1
        st.rerun()

    if submitted:
        st.session_state.preference_profile = {
            "likes": [i.strip() for i in likes.split(",") if i.strip()],
            "dislikes": [i.strip() for i in dislikes.split(",") if i.strip()],
            "dietary_preference": dietary,
            "allergies": [i.strip() for i in allergies.split(",") if i.strip()],
            "pantry_ingredients": [i.strip() for i in pantry_raw.split(",") if i.strip()],
            "budget": budget,
            "cooking_skill": skill,
            "regional_cuisine": regional,
        }
        st.session_state.step = 3
        st.rerun()


# ── Step 3: Nutrient Analysis ─────────────────────────────────────────────────
def step3_nutrients():
    st.markdown('<p class="main-header">🔬 Step 3 — Nutrient Analysis</p>', unsafe_allow_html=True)

    if st.session_state.nutrient_response is None:
        with st.spinner("🤖 BioMistral is analysing your health profile via ICMR-NIN guidelines …"):
            payload = {"health_profile": st.session_state.health_profile}
            response = api_post("/predict-nutrients", payload)
            if response:
                st.session_state.nutrient_response = response

    resp = st.session_state.nutrient_response
    if resp is None:
        if st.button("← Back"):
            st.session_state.step = 2
            st.rerun()
        return

    targets = resp.get("daily_targets", {})

    # Macro gauges
    st.subheader("📊 Your Daily Nutrient Targets")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("🔥 Calories", f"{targets.get('calories', 0):.0f} kcal")
    c2.metric("💪 Protein", f"{targets.get('protein_g', 0):.1f} g")
    c3.metric("🌾 Carbs", f"{targets.get('carbs_g', 0):.1f} g")
    c4.metric("🫒 Fat", f"{targets.get('fat_g', 0):.1f} g")

    c5, c6, c7 = st.columns(3)
    c5.metric("🌿 Fiber", f"{targets.get('fiber_g', 0):.1f} g")
    c6.metric("💧 Water", f"{targets.get('water_ml', 0):.0f} ml")
    c7.metric("📉 BMR", f"{resp.get('bmr', 0):.0f} kcal")

    # Macro pie chart
    fig = go.Figure(go.Pie(
        labels=["Protein", "Carbohydrates", "Fat"],
        values=[
            targets.get("protein_g", 0) * 4,
            targets.get("carbs_g", 0) * 4,
            targets.get("fat_g", 0) * 9,
        ],
        hole=0.4,
        marker_colors=["#66bb6a", "#42a5f5", "#ffa726"],
    ))
    fig.update_layout(title="Calorie Distribution", height=300, showlegend=True)
    st.plotly_chart(fig, use_container_width=True)

    # Micronutrients
    micros = {k: v for k, v in targets.items()
               if k not in ("calories","protein_g","carbs_g","fat_g","fiber_g","water_ml") and v}
    if micros:
        st.subheader("🧪 Disease-Specific Micronutrients")
        micro_cols = st.columns(len(micros))
        for col, (k, v) in zip(micro_cols, micros.items()):
            col.metric(k.replace("_", " ").title(), str(v))

    # Clinical notes
    if resp.get("disease_notes"):
        with st.expander("🏥 Disease Adjustments Applied"):
            for note in resp["disease_notes"]:
                st.markdown(f"- {note}")

    if resp.get("medication_interactions"):
        with st.expander("💊 Medication Interaction Warnings"):
            for note in resp["medication_interactions"]:
                st.warning(note)

    if resp.get("icmr_references"):
        with st.expander("📚 ICMR-NIN Guideline References"):
            for ref in resp["icmr_references"]:
                st.caption(ref)

    col_back, col_next = st.columns(2)
    with col_back:
        if st.button("← Back"):
            st.session_state.step = 2
            st.rerun()
    with col_next:
        if st.button("🍽️ Generate 7-Day Meal Plan →", use_container_width=True, type="primary"):
            st.session_state.step = 4
            st.rerun()


# ── Step 4: Meal Plan ─────────────────────────────────────────────────────────
def step4_meal_plan():
    st.markdown('<p class="main-header">🍽️ Step 4 — 7-Day Indian Meal Plan</p>', unsafe_allow_html=True)

    if st.session_state.meal_plan_response is None:
        with st.spinner("👨‍🍳 Generating your personalised 7-day meal plan … (this may take 1-2 minutes)"):
            targets = (st.session_state.nutrient_response or {}).get("daily_targets")
            payload = {
                "health_profile": st.session_state.health_profile,
                "preference_profile": st.session_state.preference_profile,
                "daily_targets": targets,
            }
            resp = api_post("/generate-meal-plan", payload)
            if resp:
                st.session_state.meal_plan_response = resp

    plan = st.session_state.meal_plan_response
    if not plan:
        if st.button("← Back"):
            st.session_state.step = 3
            st.rerun()
        return

    week = plan.get("week", [])
    day_names = [d["day"] for d in week]
    selected_day = st.selectbox("📅 Select Day", day_names)
    day_data = next((d for d in week if d["day"] == selected_day), {})

    MEAL_ICONS = {
        "breakfast": "🌅",
        "mid_morning_snack": "🍎",
        "lunch": "☀️",
        "evening_snack": "🍵",
        "dinner": "🌙",
    }

    for meal_key, icon in MEAL_ICONS.items():
        meal = day_data.get(meal_key, {})
        if not meal:
            continue
        meal_label = meal_key.replace("_", " ").title()
        with st.expander(f"{icon} **{meal_label}** — {meal.get('name', '')}  ({meal.get('calories', 0):.0f} kcal)"):
            col1, col2 = st.columns([2, 1])
            with col1:
                st.markdown(f"**Ingredients:** {', '.join(meal.get('ingredients', []))}")
                if meal.get("recipe_steps"):
                    st.markdown("**How to prepare:**")
                    for i, step in enumerate(meal["recipe_steps"], 1):
                        st.markdown(f"{i}. {step}")
            with col2:
                st.metric("Protein", f"{meal.get('protein_g', 0):.1f}g")
                st.metric("Carbs", f"{meal.get('carbs_g', 0):.1f}g")
                st.metric("Fat", f"{meal.get('fat_g', 0):.1f}g")
            if meal.get("youtube_url"):
                st.markdown(f"[▶️ Watch Recipe Tutorial]({meal['youtube_url']})")

    # Daily totals bar chart
    totals = day_data.get("daily_totals", {})
    if totals:
        st.subheader("📈 Daily Nutrition Summary")
        targets = (st.session_state.nutrient_response or {}).get("daily_targets", {})
        macros = ["protein_g", "carbs_g", "fat_g", "fiber_g"]
        labels = ["Protein (g)", "Carbs (g)", "Fat (g)", "Fiber (g)"]
        actual = [totals.get(m, 0) for m in macros]
        target_vals = [targets.get(m, 0) for m in macros]
        fig = go.Figure()
        fig.add_bar(name="Actual", x=labels, y=actual, marker_color="#66bb6a")
        fig.add_bar(name="Target", x=labels, y=target_vals, marker_color="#90a4ae")
        fig.update_layout(barmode="group", height=300, title=f"{selected_day} Macros vs Targets")
        st.plotly_chart(fig, use_container_width=True)

    col_back, col_next = st.columns(2)
    with col_back:
        if st.button("← Back"):
            st.session_state.step = 3
            st.rerun()
    with col_next:
        if st.button("🛒 Generate Grocery List →", use_container_width=True, type="primary"):
            st.session_state.step = 5
            st.rerun()

    # Download meal plan
    meal_json = json.dumps(plan, indent=2)
    st.download_button("⬇️ Download Meal Plan (JSON)", meal_json, "meal_plan.json", "application/json")


# ── Step 5: Grocery List ──────────────────────────────────────────────────────
def step5_grocery():
    st.markdown('<p class="main-header">🛒 Step 5 — Weekly Grocery List</p>', unsafe_allow_html=True)

    if st.session_state.grocery_response is None:
        with st.spinner("🛒 Building your grocery list …"):
            payload = {
                "meal_plan": st.session_state.meal_plan_response,
                "pantry_ingredients": st.session_state.preference_profile.get("pantry_ingredients", []),
            }
            resp = api_post("/generate-grocery-list", payload)
            if resp:
                st.session_state.grocery_response = resp

    grocery = st.session_state.grocery_response
    if not grocery:
        if st.button("← Back"):
            st.session_state.step = 4
            st.rerun()
        return

    items = grocery.get("items", [])
    total = grocery.get("total_estimated_cost_inr", 0)
    st.metric("🧾 Estimated Weekly Cost", f"₹{total:.0f}")

    # Group by category
    from collections import defaultdict
    by_category: dict[str, list] = defaultdict(list)
    for item in items:
        by_category[item.get("category", "General")].append(item)

    CATEGORY_ICONS = {
        "Grains": "🌾", "Protein": "💪", "Dairy": "🥛",
        "Vegetables": "🥦", "Fruits": "🍎", "Fats & Oils": "🫒",
        "Nuts & Seeds": "🥜", "Spices": "🌶️", "General": "🛍️",
    }
    for category, cat_items in by_category.items():
        icon = CATEGORY_ICONS.get(category, "🛍️")
        st.subheader(f"{icon} {category}")
        cols = st.columns(3)
        for i, item in enumerate(cat_items):
            with cols[i % 3]:
                cost_str = f"  ₹{item['estimated_cost_inr']:.0f}" if item.get("estimated_cost_inr") else ""
                st.markdown(
                    f'<span class="grocery-badge">🛒 {item["ingredient"]} — {item["quantity"]}{cost_str}</span>',
                    unsafe_allow_html=True,
                )

    if grocery.get("notes"):
        with st.expander("💡 Grocery Tips"):
            for note in grocery["notes"]:
                st.info(note)

    # PDF download
    if st.button("📄 Download as PDF"):
        pdf_bytes = _generate_pdf(grocery, st.session_state.meal_plan_response)
        st.download_button("⬇️ Download PDF", pdf_bytes, "dietitian_plan.pdf", "application/pdf")

    st.divider()
    if st.button("← Back to Meal Plan"):
        st.session_state.step = 4
        st.rerun()
    if st.button("🔄 Start Over"):
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.rerun()


# ── PDF Generator ─────────────────────────────────────────────────────────────
def _generate_pdf(grocery: dict, meal_plan: dict) -> bytes:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "AI Dietitian – Personalised Plan", ln=True, align="C")
    pdf.set_font("Helvetica", size=9)
    pdf.multi_cell(0, 5, (
        "DISCLAIMER: This AI dietitian is an informational assistant and is NOT a substitute "
        "for professional medical advice, diagnosis, or treatment."
    ))
    pdf.ln(4)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "Weekly Grocery List", ln=True)
    pdf.set_font("Helvetica", size=10)
    for item in grocery.get("items", []):
        cost = f"  ~₹{item['estimated_cost_inr']:.0f}" if item.get("estimated_cost_inr") else ""
        pdf.cell(0, 6, f"  {item['ingredient']}  ({item['quantity']}){cost}", ln=True)
    pdf.ln(4)
    total = grocery.get("total_estimated_cost_inr", 0)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 6, f"Estimated Total: Rs.{total:.0f}", ln=True)
    return bytes(pdf.output())


# ── Router ────────────────────────────────────────────────────────────────────
step_map = {
    1: step1_health_profile,
    2: step2_preferences,
    3: step3_nutrients,
    4: step4_meal_plan,
    5: step5_grocery,
}

step_fn = step_map.get(st.session_state.step, step1_health_profile)
step_fn()
