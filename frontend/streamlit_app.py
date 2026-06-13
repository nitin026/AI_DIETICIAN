"""
frontend/streamlit_app.py
Multi-step Streamlit UI for the AI Dietitian application.
Run with: streamlit run frontend/streamlit_app.py
"""
from __future__ import annotations

import io
import json
import os
from html import escape
from typing import Any
from collections import defaultdict

import plotly.graph_objects as go
import requests
import streamlit as st
from fpdf import FPDF

# ── MUST be the very first Streamlit command ──────────────────────────────────
st.set_page_config(
    page_title="AI Dietitian - Powered by Groq",
    page_icon="🥗",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Configuration ─────────────────────────────────────────────────────────────
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

DISCLAIMER = (
    "⚠️ **Medical Disclaimer:** This AI dietitian is an informational assistant "
    "and is **not** a substitute for professional medical advice, diagnosis, or treatment. "
    "Always consult a qualified healthcare provider before making dietary changes."
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .stApp {background:#0f1419; color:#eef4f0;}
    .main-header {font-size:2.2rem; font-weight:700; color:#76d275;}
    .sub-header  {font-size:1.1rem; color:#b8c7bd;}
    .metric-card {background:#16211c; border:1px solid #26362e; border-radius:8px; padding:1rem; text-align:center;}
    .disclaimer  {background:#221b12; border-left:4px solid #fb8c00; padding:0.8rem 1rem;
                  border-radius:4px; font-size:0.88rem;}
    .meal-card   {background:#151d18; border:1px solid #26362e; border-radius:8px;
                  padding:1rem; margin-bottom:0.6rem;}
    .grocery-badge {display:inline-block; background:#17311f; color:#a5d6a7;
                    border-radius:12px; padding:2px 10px; font-size:0.82rem; margin:2px;}
    .chip {display:inline-block; background:#1d2a23; color:#d7f5df; border:1px solid #31543b;
           border-radius:18px; padding:0.35rem 0.75rem; margin:0.2rem; font-size:0.86rem;}
    .micro-grid {display:grid; grid-template-columns:repeat(auto-fit,minmax(180px,1fr)); gap:0.7rem; margin:0.8rem 0 1rem;}
    .micro-card {background:#141b20; border:1px solid #29343d; border-radius:8px; padding:0.85rem 0.95rem;}
    .micro-card .label {color:#aebbc3; font-size:0.78rem; margin-bottom:0.25rem;}
    .micro-card .value {color:#f4fbf7; font-size:1.25rem; font-weight:700; line-height:1.2;}
    .micro-card .hint {color:#8fa29a; font-size:0.76rem; margin-top:0.35rem;}
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
        "meal_plan_attempted": False,
        "grocery_response": None,
        "validation_response": None,
        "user_id": "demo-user",
        "chat_messages": [],
        "analytics_response": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()


# ── Sidebar Navigation ────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🥗 AI Dietitian")
    st.markdown("*Powered by Groq Llama 3.3 + ICMR-NIN 2024*")
    st.caption(f"🔗 Backend: {BACKEND_URL}")
    st.divider()
    step_labels = {
        1: "📋 Health Profile",
        2: "🥦 Preferences & Pantry",
        3: "🔬 Nutrient Analysis",
        4: "🍽️ Meal Plan",
        5: "🛒 Grocery List",
        6: "AI Coach Chat",
        7: "Adherence Calendar",
        8: "Health Insights",
    }
    for step, label in step_labels.items():
        if st.session_state.step == step:
            st.markdown(f"**→ {label}**")
        else:
            if st.button(label, key=f"nav_{step}", use_container_width=True):
                st.session_state.step = step
                st.rerun()
    st.divider()
    st.markdown(f'<div class="disclaimer">{DISCLAIMER}</div>', unsafe_allow_html=True)


# ── Helper: API calls ─────────────────────────────────────────────────────────
def api_post(endpoint: str, payload: dict) -> dict | None:
    try:
        timeout = 600 if endpoint == "/generate-meal-plan" else 180
        resp = requests.post(f"{BACKEND_URL}{endpoint}", json=payload, timeout=timeout)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.ConnectionError:
        st.error(f"❌ Cannot connect to backend at {BACKEND_URL}. Is the FastAPI server running?")
    except requests.exceptions.Timeout:
        st.error("⏱️ Request timed out. The LLM may be slow – please try again.")
    except requests.exceptions.HTTPError as e:
        try:
            detail = e.response.json().get("detail", "The request could not be completed.")
        except Exception:
            detail = "The request could not be completed."
        if not isinstance(detail, str):
            detail = "Please complete the earlier profile steps and try again."
        st.error(f"Meal plan generation could not be completed: {detail}")
    except Exception as e:
        st.error(f"Unexpected error: {e}")
    return None


def api_get(endpoint: str) -> dict | None:
    try:
        resp = requests.get(f"{BACKEND_URL}{endpoint}", timeout=60)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        st.error(f"API error: {e}")
    return None


MICRONUTRIENT_LABELS = {
    "sodium_mg": "Sodium",
    "potassium_mg": "Potassium",
    "iron_mg": "Iron",
    "calcium_mg": "Calcium",
    "vitamin_d_iu": "Vitamin D",
    "b12_mcg": "Vitamin B12",
    "vitamin_a_mcg": "Vitamin A",
    "vitamin_b1_mg": "Vitamin B1",
    "vitamin_b2_mg": "Vitamin B2",
    "vitamin_b3_mg": "Vitamin B3",
    "vitamin_b5_mg": "Vitamin B5",
    "vitamin_b6_mg": "Vitamin B6",
    "vitamin_b7_mcg": "Biotin",
    "vitamin_b9_mcg": "Folate",
    "vitamin_b12_mcg": "Vitamin B12",
    "vitamin_c_mg": "Vitamin C",
    "vitamin_e_mg": "Vitamin E",
    "vitamin_k_mcg": "Vitamin K",
    "magnesium_mg": "Magnesium",
    "zinc_mg": "Zinc",
    "selenium_mcg": "Selenium",
    "copper_mg": "Copper",
    "phosphorus_mg": "Phosphorus",
    "iodine_mcg": "Iodine",
    "chloride_mg": "Chloride",
    "manganese_mg": "Manganese",
    "chromium_mcg": "Chromium",
    "molybdenum_mcg": "Molybdenum",
    "choline_mg": "Choline",
    "omega_3_g": "Omega-3",
    "omega_6_g": "Omega-6",
    "glycemic_load": "Glycemic Load",
    "glycemic_index": "Glycemic Index",
}

MICRONUTRIENT_GROUPS = {
    "Vitamins": [
        "vitamin_a_mcg",
        "vitamin_b1_mg",
        "vitamin_b2_mg",
        "vitamin_b3_mg",
        "vitamin_b5_mg",
        "vitamin_b6_mg",
        "vitamin_b7_mcg",
        "vitamin_b9_mcg",
        "vitamin_b12_mcg",
        "vitamin_c_mg",
        "vitamin_d_iu",
        "vitamin_e_mg",
        "vitamin_k_mcg",
    ],
    "Minerals": [
        "calcium_mg",
        "iron_mg",
        "magnesium_mg",
        "zinc_mg",
        "selenium_mcg",
        "copper_mg",
        "phosphorus_mg",
        "iodine_mcg",
        "manganese_mg",
        "chromium_mcg",
        "molybdenum_mcg",
    ],
    "Electrolytes": [
        "sodium_mg",
        "potassium_mg",
        "chloride_mg",
    ],
    "Metabolic Targets": [
        "choline_mg",
        "omega_3_g",
        "omega_6_g",
        "glycemic_load",
        "glycemic_index",
    ],
}

MICRONUTRIENT_DISPLAY_ORDER = [
    key
    for group_keys in MICRONUTRIENT_GROUPS.values()
    for key in group_keys
]

MICRONUTRIENT_UNITS = {
    "mg": "mg",
    "mcg": "mcg",
    "iu": "IU",
    "g": "g",
    "index": "",
    "load": "",
}


def _nutrient_label(key: str) -> str:
    return MICRONUTRIENT_LABELS.get(key, key.replace("_", " ").title())


def _nutrient_unit(key: str) -> str:
    suffix = key.rsplit("_", 1)[-1]
    return MICRONUTRIENT_UNITS.get(suffix, "")


def _format_nutrient_value(key: str, value: Any) -> str:
    if not isinstance(value, (int, float)):
        return str(value)
    unit = _nutrient_unit(key)
    number = f"{value:.0f}" if abs(value) >= 10 else f"{value:.1f}".rstrip("0").rstrip(".")
    return f"{number} {unit}".strip()


def _micro_rows(keys: list[str], micros: dict[str, Any], adequacy: dict[str, Any]) -> list[dict[str, str]]:
    rows = []
    for key in keys:
        value = micros.get(key)
        if value in (None, "", 0):
            continue
        detail = adequacy.get(key, {})
        foods = detail.get("food_sources") or []
        rows.append(
            {
                "Nutrient": _nutrient_label(key),
                "Target": _format_nutrient_value(key, value),
                "Focus foods": ", ".join(foods[:4]) if foods else "-",
            }
        )
    return rows


def _micro_cards(rows: list[dict[str, str]]) -> None:
    cards = []
    for row in rows:
        cards.append(
            "<div class=\"micro-card\">"
            f"<div class=\"label\">{escape(row['Nutrient'])}</div>"
            f"<div class=\"value\">{escape(row['Target'])}</div>"
            f"<div class=\"hint\">{escape(row['Focus foods'])}</div>"
            "</div>"
        )
    st.markdown(f"<div class=\"micro-grid\">{''.join(cards)}</div>", unsafe_allow_html=True)


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
        st.session_state.nutrient_response = None
        st.session_state.meal_plan_response = None
        st.session_state.meal_plan_attempted = False
        st.session_state.grocery_response = None
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
            regional_choice = st.selectbox(
                "Regional Cuisine",
                ["North Indian", "South Indian", "Bengali", "Gujarati", "Maharashtrian",
                 "Rajasthani", "Punjabi", "Andhra", "Kerala", "Tamil Nadu", "Other Indian regional cuisine"],
            )
            regional_custom = st.text_input(
                "Indian Regional Cuisine",
                placeholder="e.g. Goan, Assamese, Konkani, Kashmiri",
                disabled=regional_choice != "Other Indian regional cuisine",
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
        st.session_state.meal_plan_response = None
        st.session_state.meal_plan_attempted = False
        st.session_state.grocery_response = None
        st.session_state.preference_profile = {
            "likes": [i.strip() for i in likes.split(",") if i.strip()],
            "dislikes": [i.strip() for i in dislikes.split(",") if i.strip()],
            "dietary_preference": dietary,
            "allergies": [i.strip() for i in allergies.split(",") if i.strip()],
            "pantry_ingredients": [i.strip() for i in pantry_raw.split(",") if i.strip()],
            "budget": budget,
            "cooking_skill": skill,
            "regional_cuisine": regional_custom.strip() or regional_choice,
        }
        st.session_state.step = 3
        st.rerun()


# ── Step 3: Nutrient Analysis ─────────────────────────────────────────────────
def step3_nutrients():
    st.markdown('<p class="main-header">🔬 Step 3 — Nutrient Analysis</p>', unsafe_allow_html=True)

    if st.session_state.nutrient_response is not None:
        if st.button("Refresh nutrient analysis", use_container_width=True):
            st.session_state.nutrient_response = None
            st.rerun()

    if st.session_state.nutrient_response is None:
        with st.spinner("🤖 Analysing your health profile via ICMR-NIN guidelines …"):
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

    adequacy = resp.get("nutrient_adequacy", {}).get("nutrients", {})
    micros = {
        k: v
        for k, v in targets.items()
        if k not in ("calories", "protein_g", "carbs_g", "fat_g", "fiber_g", "water_ml")
        and k != "b12_mcg"
        and v
    }
    if micros:
        st.subheader("🧪 Disease-Specific Micronutrients")
        st.caption("Personalized vitamin, mineral, electrolyte, fatty acid, and metabolic targets based on your profile.")

        priority_keys = [
            "sodium_mg",
            "potassium_mg",
            "iron_mg",
            "calcium_mg",
            "vitamin_d_iu",
            "vitamin_b12_mcg",
            "glycemic_load",
        ]
        priority_rows = _micro_rows(priority_keys, micros, adequacy)[:6]
        if priority_rows:
            _micro_cards(priority_rows)

        tabs = st.tabs(list(MICRONUTRIENT_GROUPS.keys()) + ["All Targets"])
        for tab, (group_name, group_keys) in zip(tabs[:-1], MICRONUTRIENT_GROUPS.items()):
            with tab:
                rows = _micro_rows(group_keys, micros, adequacy)
                if rows:
                    _micro_cards(rows)
                    st.dataframe(rows, use_container_width=True, hide_index=True)
                else:
                    st.info(f"No {group_name.lower()} targets were returned for this profile.")

        ordered_keys = [key for key in MICRONUTRIENT_DISPLAY_ORDER if key in micros]
        ordered_keys.extend(key for key in micros if key not in ordered_keys)
        all_rows = _micro_rows(ordered_keys, micros, adequacy)
        with tabs[-1]:
            st.dataframe(all_rows, use_container_width=True, hide_index=True)
    if adequacy:
        st.subheader("Micronutrient Adequacy Radar")
        top_items = [
            (key, adequacy[key])
            for key in MICRONUTRIENT_DISPLAY_ORDER
            if key in adequacy and key in micros
        ][:12]
        fig = go.Figure(go.Scatterpolar(
            r=[item.get("score", 0) for _, item in top_items],
            theta=[_nutrient_label(name) for name, _ in top_items],
            fill="toself",
            line_color="#76d275",
        ))
        fig.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
            height=360,
            showlegend=False,
            paper_bgcolor="#0f1419",
            plot_bgcolor="#0f1419",
            font_color="#eef4f0",
        )
        st.plotly_chart(fig, use_container_width=True)

    if resp.get("deficiency_risks"):
        with st.expander("Nutrient Gap Alerts"):
            for risk in resp["deficiency_risks"]:
                st.warning(risk)

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
            st.session_state.meal_plan_attempted = False
            st.session_state.step = 4
            st.rerun()


# ── Step 4: Meal Plan ─────────────────────────────────────────────────────────
def step4_meal_plan():
    st.markdown('<p class="main-header">🍽️ Step 4 — 7-Day Indian Meal Plan</p>', unsafe_allow_html=True)

    if not st.session_state.health_profile or not st.session_state.preference_profile or not st.session_state.nutrient_response:
        st.warning("Complete Health Profile, Preferences & Pantry, and Nutrient Analysis before generating a meal plan.")
        if st.button("← Back"):
            st.session_state.step = 3
            st.rerun()
        return

    if st.session_state.meal_plan_response is None and not st.session_state.meal_plan_attempted:
        st.session_state.meal_plan_attempted = True
        with st.spinner("👨‍🍳 Generating your personalised 7-day meal plan …"):
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
        if st.button("Retry meal plan generation", type="primary"):
            st.session_state.meal_plan_attempted = False
            st.rerun()
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
                st.metric("Fiber", f"{meal.get('fiber_g', 0):.1f}g")
            st.caption(
                f"{meal.get('preparation_time_minutes', 0)} min | "
                f"{meal.get('difficulty', 'n/a').title()} | "
                f"Estimated cost: INR {meal.get('estimated_cost_inr', 0):.0f}"
            )
            if meal.get("youtube_url"):
                st.markdown(f"[▶️ Watch Recipe Tutorial]({meal['youtube_url']})")
            with st.form(f"feedback_{selected_day}_{meal_key}"):
                f1, f2, f3 = st.columns(3)
                rating = f1.slider("Rating", 1, 5, 4, key=f"rating_{selected_day}_{meal_key}")
                liked = f2.selectbox("Preference", ["liked", "neutral", "disliked"], key=f"liked_{selected_day}_{meal_key}")
                digestion = f3.selectbox("Digestion", ["comfortable", "heavy", "acidic", "bloated"], key=f"digestion_{selected_day}_{meal_key}")
                notes = st.text_input("Meal notes", key=f"notes_{selected_day}_{meal_key}")
                if st.form_submit_button("Save feedback"):
                    payload = {
                        "user_id": st.session_state.user_id,
                        "date": selected_day,
                        "day": selected_day,
                        "meal_type": meal_key,
                        "meal_name": meal.get("name", ""),
                        "rating": rating,
                        "liked": True if liked == "liked" else False if liked == "disliked" else None,
                        "digestion": digestion,
                        "notes": notes,
                    }
                    if api_post("/feedback", payload):
                        st.success("Feedback saved. Future recommendations will down-rank poor fits.")

    totals = day_data.get("daily_totals", {})
    if totals:
        st.subheader("📈 Daily Nutrition Summary")
        targets = (st.session_state.nutrient_response or {}).get("daily_targets", {})
        st.metric("Calories", f"{totals.get('calories', 0):.0f} kcal")
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

    if st.button("Open AI Coach for swaps or explanations", use_container_width=True):
        st.session_state.step = 6
        st.rerun()

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


def _assistant_payload(message: str) -> dict:
    return {
        "user_id": st.session_state.user_id,
        "message": message,
        "health_profile": st.session_state.health_profile or None,
        "preference_profile": st.session_state.preference_profile or None,
        "daily_targets": (st.session_state.nutrient_response or {}).get("daily_targets"),
        "meal_plan": st.session_state.meal_plan_response,
        "grocery_list": st.session_state.grocery_response,
    }


def step6_chatbot():
    st.markdown('<p class="main-header">AI Nutrition Coach</p>', unsafe_allow_html=True)
    st.caption("Personalized to your profile, meal plan, groceries, feedback, and adherence history.")
    st.markdown(f'<div class="disclaimer">{DISCLAIMER}</div>', unsafe_allow_html=True)

    prompts = [
        "Replace paneer with a cheaper protein source",
        "Make tomorrow breakfast high protein",
        "Reduce sodium in my diet",
        "Add more iron-rich foods",
        "Give me a 1500 calorie version",
        "Explain why this meal fits me",
    ]
    st.markdown("".join([f'<span class="chip">{p}</span>' for p in prompts]), unsafe_allow_html=True)
    quick_cols = st.columns(3)
    for idx, prompt in enumerate(prompts[:3]):
        if quick_cols[idx].button(prompt, use_container_width=True):
            st.session_state.chat_input_seed = prompt

    for msg in st.session_state.chat_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    seeded = st.session_state.pop("chat_input_seed", "")
    user_text = st.chat_input("Ask for swaps, meal timing, deficiency fixes, budget changes, or health-safe guidance")
    message = user_text or seeded
    if message:
        st.session_state.chat_messages.append({"role": "user", "content": message})
        with st.chat_message("user"):
            st.markdown(message)
        with st.chat_message("assistant"):
            with st.spinner("Thinking with your nutrition context..."):
                response = api_post("/chat", _assistant_payload(message))
            answer = (response or {}).get("answer", "I could not generate a response right now.")
            st.markdown(answer)
        st.session_state.chat_messages.append({"role": "assistant", "content": answer})


def step7_adherence_calendar():
    st.markdown('<p class="main-header">Adherence Calendar</p>', unsafe_allow_html=True)
    today = st.date_input("Date")
    meal_type = st.selectbox("Meal", ["breakfast", "mid_morning_snack", "lunch", "evening_snack", "dinner"])
    status = st.radio("Status", ["completed", "partial", "skipped"], horizontal=True)
    c1, c2, c3 = st.columns(3)
    water_ml = c1.number_input("Water ml", min_value=0, value=2000, step=250)
    sleep_hours = c2.number_input("Sleep hours", min_value=0.0, max_value=16.0, value=7.0, step=0.5)
    weight_kg = c3.number_input("Weight kg", min_value=0.0, value=float(st.session_state.health_profile.get("weight_kg", 70)))
    c4, c5 = st.columns(2)
    mood = c4.selectbox("Mood", ["low", "okay", "good", "great"], index=2)
    digestion = c5.selectbox("Digestion", ["comfortable", "heavy", "acidic", "bloated"])
    notes = st.text_input("Notes")

    if st.button("Save adherence log", type="primary"):
        payload = {
            "user_id": st.session_state.user_id,
            "date": str(today),
            "meal_type": meal_type,
            "status": status,
            "water_ml": water_ml,
            "sleep_hours": sleep_hours,
            "weight_kg": weight_kg,
            "mood": mood,
            "digestion": digestion,
            "notes": notes,
        }
        if api_post("/adherence", payload):
            st.success("Adherence saved.")

    data = api_get(f"/adherence/{st.session_state.user_id}") or {}
    summary = data.get("summary", {})
    s1, s2, s3 = st.columns(3)
    s1.metric("Average adherence", f"{summary.get('average_score', 0)}%")
    s2.metric("Current streak", summary.get("current_streak", 0))
    s3.metric("Skipped meals", summary.get("skipped_meals", 0))
    daily = summary.get("daily_scores", [])
    if daily:
        fig = go.Figure(go.Bar(x=[d["date"] for d in daily], y=[d["score"] for d in daily], marker_color="#76d275"))
        fig.update_layout(height=300, title="Daily Adherence Score", paper_bgcolor="#0f1419", plot_bgcolor="#0f1419", font_color="#eef4f0")
        st.plotly_chart(fig, use_container_width=True)


def step8_insights():
    st.markdown('<p class="main-header">AI Health Insights Dashboard</p>', unsafe_allow_html=True)
    payload = {
        "user_id": st.session_state.user_id,
        "health_profile": st.session_state.health_profile or None,
        "preference_profile": st.session_state.preference_profile or None,
        "daily_targets": (st.session_state.nutrient_response or {}).get("daily_targets"),
    }
    response = api_post("/analytics", payload) or {}
    i1, i2 = st.columns(2)
    i1.metric("Health score", f"{response.get('health_score', 0)} / 100")
    i2.metric("Adherence risk", response.get("predicted_adherence_risk", "unknown").title())
    for item in response.get("insights", []):
        st.info(item)
    adequacy = response.get("nutrient_adequacy", {}).get("nutrients", {})
    if adequacy:
        names = [k.replace("_", " ").title() for k in list(adequacy.keys())[:10]]
        scores = [v.get("score", 0) for v in list(adequacy.values())[:10]]
        fig = go.Figure(go.Bar(x=names, y=scores, marker_color="#42a5f5"))
        fig.update_layout(height=360, title="Nutrient Compliance", paper_bgcolor="#0f1419", plot_bgcolor="#0f1419", font_color="#eef4f0")
        st.plotly_chart(fig, use_container_width=True)


# ── PDF Generator ─────────────────────────────────────────────────────────────
def _generate_pdf(grocery: dict, meal_plan: dict) -> bytes:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "AI Dietitian - Personalised Plan", ln=True, align="C")
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
        cost = f"  ~Rs.{item['estimated_cost_inr']:.0f}" if item.get("estimated_cost_inr") else ""
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
    6: step6_chatbot,
    7: step7_adherence_calendar,
    8: step8_insights,
}

step_fn = step_map.get(st.session_state.step, step1_health_profile)
step_fn()
