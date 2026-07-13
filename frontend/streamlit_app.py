"""
frontend/streamlit_app.py
Multi-step Streamlit UI for the AI Dietitian application.
Run with: streamlit run frontend/streamlit_app.py
"""
from __future__ import annotations

import io
import json
import os
import sys
import importlib
from html import escape
from typing import Any
from collections import defaultdict
from pathlib import Path

import plotly.graph_objects as go
import pandas as pd
import requests
import streamlit as st
import streamlit.components.v1 as components
from fpdf import FPDF

def _load_mic_recorder():
    try:
        module = importlib.import_module("streamlit_mic_recorder")
        return getattr(module, "mic_recorder"), ""
    except Exception as exc:
        return None, str(exc)


mic_recorder, MIC_IMPORT_ERROR = _load_mic_recorder()

# â”€â”€ MUST be the very first Streamlit command â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
st.set_page_config(
    page_title="AI Dietitian - Powered by Groq",
    page_icon="ðŸ¥—",
    layout="wide",
    initial_sidebar_state="expanded",
)



# â”€â”€ Configuration â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

DISCLAIMER = (
    "âš ï¸ **Medical Disclaimer:** This AI dietitian is an informational assistant "
    "and is **not** a substitute for professional medical advice, diagnosis, or treatment. "
    "Always consult a qualified healthcare provider before making dietary changes."
)

# â”€â”€ Custom CSS â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Sora:wght@400;600;700;800&family=JetBrains+Mono:wght@400;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    h1, h2, h3, .main-header, .coach-title {
        font-family: 'Sora', sans-serif !important;
        font-weight: 700 !important;
    }

    code, pre {
        font-family: 'JetBrains Mono', monospace !important;
    }

    .stApp {
        background: #0f1117 !important;
        color: #f9fafb !important;
    }

    /* Sleek Sidebar Navigation styling */
    section[data-testid="stSidebar"] {
        background-color: #0a0b0e !important;
        border-right: 1px solid rgba(50, 61, 254, 0.15) !important;
    }

    section[data-testid="stSidebar"] hr {
        border-color: rgba(50, 61, 254, 0.15) !important;
    }

    /* Navigation buttons in sidebar */
    div[data-testid="stSidebar"] button {
        background: rgba(255, 255, 255, 0.02) !important;
        color: #94a3b8 !important;
        border: 1px solid rgba(255, 255, 255, 0.05) !important;
        border-radius: 8px !important;
        padding: 0.5rem 1rem !important;
        text-align: left !important;
        justify-content: flex-start !important;
        transition: all 0.3s ease !important;
    }

    div[data-testid="stSidebar"] button:hover {
        background: rgba(50, 61, 254, 0.1) !important;
        color: #cd3ef9 !important;
        border-color: rgba(205, 62, 249, 0.3) !important;
        transform: translateX(2px);
    }

    /* Active step indicators */
    .sidebar-active-step {
        background: linear-gradient(90deg, rgba(50, 61, 254, 0.15) 0%, rgba(205, 62, 249, 0.05) 100%) !important;
        border-left: 4px solid #323dfe !important;
        color: #cd3ef9 !important;
        font-weight: 700 !important;
        padding: 0.6rem 1rem !important;
        border-radius: 4px !important;
        margin: 4px 0 !important;
    }

    /* Stepper Styling */
    .stepper-container {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 2rem;
        background: rgba(15, 17, 23, 0.4);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 12px;
        padding: 1.2rem 2rem;
    }
    .step-item {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 0.5rem;
        z-index: 2;
    }
    .step-icon {
        width: 32px;
        height: 32px;
        border-radius: 50%;
        background: rgba(255, 255, 255, 0.05);
        border: 2px solid rgba(255, 255, 255, 0.1);
        color: #94a3b8;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 0.9rem;
        font-weight: 800;
        transition: all 0.3s ease;
    }
    .step-label {
        font-size: 0.8rem;
        font-weight: 500;
        color: #64748b;
        transition: all 0.3s ease;
    }
    .step-item.active .step-icon {
        background: linear-gradient(135deg, #323dfe 0%, #cd3ef9 100%);
        border-color: #323dfe;
        color: #ffffff;
        box-shadow: 0 0 15px rgba(50, 61, 254, 0.4);
    }
    .step-item.active .step-label {
        color: #cd3ef9;
        font-weight: 700;
    }
    .step-item.done .step-icon {
        background: rgba(50, 61, 254, 0.15);
        border-color: rgba(205, 62, 249, 0.4);
        color: #cd3ef9;
    }
    .step-item.done .step-label {
        color: #323dfe;
    }
    .step-line {
        flex-grow: 1;
        height: 2px;
        background: rgba(255, 255, 255, 0.08);
        margin: 0 1rem;
        margin-bottom: 1.5rem;
        z-index: 1;
    }
    .step-line.filled {
        background: linear-gradient(90deg, #323dfe, #cd3ef9) !important;
    }

    /* Calorie Scanner Card */
    .calorie-scanner-card {
        background: rgba(15, 17, 23, 0.6);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(50, 61, 254, 0.25);
        border-radius: 14px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
    }
    .scanner-header {
        font-size: 1.1rem;
        font-weight: 700;
        color: #cd3ef9;
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .scanner-dish-name {
        font-size: 1.6rem;
        font-weight: 800;
        color: #ffffff;
        margin-bottom: 1rem;
    }
    .scanner-metrics-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 0.8rem;
        margin-bottom: 1.2rem;
    }
    .scanner-metric-item {
        background: rgba(255, 255, 255, 0.02);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 10px;
        padding: 0.8rem;
        text-align: center;
    }
    .scanner-metric-item.calorie {
        border-color: rgba(50, 61, 254, 0.3);
        background: rgba(50, 61, 254, 0.03);
    }
    .scanner-metric-item .value {
        font-size: 1.2rem;
        font-weight: 700;
        color: #ffffff;
    }
    .scanner-metric-item.calorie .value {
        color: #323dfe;
    }
    .scanner-metric-item .label {
        font-size: 0.75rem;
        color: #94a3b8;
        margin-top: 0.25rem;
    }
    .scanner-assessment {
        background: rgba(255, 255, 255, 0.03);
        border-radius: 10px;
        padding: 1rem;
        font-size: 0.9rem;
        line-height: 1.5;
        color: #cbd5e1;
        margin-bottom: 1rem;
        border-left: 4px solid #cd3ef9;
    }
    .scanner-footer {
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-size: 0.8rem;
        color: #64748b;
    }

    /* Core UI typography & cards */
    .main-header {
        font-size: 2.5rem;
        font-weight: 800;
        background: linear-gradient(90deg, #323dfe, #cd3ef9);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
        letter-spacing: -0.02em;
    }

    .sub-header {
        font-size: 1.15rem;
        color: #94a3b8;
        font-weight: 400;
        margin-bottom: 1.5rem;
    }

    .metric-card {
        background: rgba(15, 17, 23, 0.5) !important;
        backdrop-filter: blur(12px) !important;
        border: 1px solid rgba(50, 61, 254, 0.15) !important;
        border-radius: 16px !important;
        padding: 1.5rem !important;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.25) !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    }

    .metric-card:hover {
        transform: translateY(-4px) !important;
        border-color: rgba(205, 62, 249, 0.3) !important;
        box-shadow: 0 15px 35px rgba(50, 61, 254, 0.1) !important;
    }

    .meal-card {
        background: rgba(15, 17, 23, 0.6) !important;
        backdrop-filter: blur(8px) !important;
        border: 1px solid rgba(255, 255, 255, 0.05) !important;
        border-radius: 16px !important;
        padding: 1.5rem !important;
        margin-bottom: 1rem !important;
        transition: all 0.3s ease !important;
    }

    .meal-card:hover {
        background: rgba(15, 17, 23, 0.8) !important;
        border-color: rgba(205, 62, 249, 0.25) !important;
        box-shadow: 0 8px 24px rgba(50, 61, 254, 0.05) !important;
    }

    .chip {
        display: inline-block;
        background: rgba(50, 61, 254, 0.08);
        color: #cd3ef9;
        border: 1px solid rgba(205, 62, 249, 0.2);
        border-radius: 20px;
        padding: 0.4rem 0.9rem;
        margin: 0.25rem;
        font-size: 0.85rem;
        font-weight: 500;
        transition: all 0.2s ease;
        cursor: pointer;
    }
    .chip:hover {
        background: rgba(50, 61, 254, 0.15);
        transform: scale(1.03);
    }

    .grocery-badge {
        display: inline-block;
        background: rgba(15, 17, 23, 0.7) !important;
        color: #e2e8f0 !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 12px !important;
        padding: 8px 16px !important;
        font-size: 0.9rem !important;
        margin: 4px !important;
        backdrop-filter: blur(8px) !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1) !important;
        transition: all 0.2s ease !important;
    }
    .grocery-badge:hover {
        border-color: rgba(205, 62, 249, 0.3) !important;
        background: rgba(50, 61, 254, 0.05) !important;
    }

    .micro-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 1rem;
        margin: 1.5rem 0;
    }

    .micro-card {
        background: rgba(15, 17, 23, 0.4) !important;
        backdrop-filter: blur(10px) !important;
        border: 1px solid rgba(255, 255, 255, 0.06) !important;
        border-radius: 12px !important;
        padding: 1.2rem !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    }
    .micro-card:hover {
        transform: scale(1.03) !important;
        border-color: rgba(205, 62, 249, 0.25) !important;
        box-shadow: 0 10px 25px rgba(50, 61, 254, 0.06) !important;
    }
    .micro-card .label {
        color: #94a3b8 !important;
        font-size: 0.8rem !important;
        font-weight: 500 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.05em !important;
    }
    .micro-card .value {
        color: #ffffff !important;
        font-size: 1.5rem !important;
        font-weight: 800 !important;
        margin: 0.4rem 0 !important;
    }
    .micro-card .hint {
        color: #64748b !important;
        font-size: 0.78rem !important;
    }

    .coach-hero {
        background: linear-gradient(135deg, rgba(50, 61, 254, 0.1) 0%, rgba(15, 17, 23, 0.8) 100%) !important;
        backdrop-filter: blur(12px) !important;
        border: 1px solid rgba(205, 62, 249, 0.2) !important;
        border-radius: 16px !important;
        padding: 1.8rem !important;
        margin-bottom: 1.5rem !important;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2) !important;
    }

    .coach-title {
        font-size: 2rem !important;
        font-weight: 800 !important;
        color: #ffffff !important;
        margin: 0 !important;
        letter-spacing: -0.01em !important;
    }

    .coach-subtitle {
        color: #94a3b8 !important;
        margin-top: 0.4rem !important;
        font-size: 1rem !important;
    }

    /* Inputs, textareas, sliders */
    .stTextInput input, .stNumberInput input, .stSelectbox select, .stTextArea textarea {
        background-color: rgba(15, 17, 23, 0.6) !important;
        border: 1px solid rgba(255,255,255,0.08) !important;
        color: #ffffff !important;
        border-radius: 10px !important;
        padding: 0.6rem !important;
        transition: all 0.2s ease !important;
    }

    .stTextInput input:focus, .stNumberInput input:focus, .stSelectbox select:focus, .stTextArea textarea:focus {
        border-color: rgba(205, 62, 249, 0.5) !important;
        box-shadow: 0 0 10px rgba(205, 62, 249, 0.15) !important;
    }

    /* Chat bubbles */
    .stChatMessage[data-testid="stChatMessage"] {
        background: rgba(15, 17, 23, 0.4) !important;
        border: 1px solid rgba(255, 255, 255, 0.04) !important;
        border-radius: 16px !important;
        padding: 1.2rem !important;
        margin-bottom: 1rem !important;
    }

    .stChatMessage[data-testid="stChatMessage"]:has([data-testid="chatAvatar-user"]) {
        background: rgba(50, 61, 254, 0.05) !important;
        border: 1px solid rgba(50, 61, 254, 0.15) !important;
    }

    /* Floating TTS speak controls style */
    .tts-controls-panel {
        display: flex;
        gap: 0.5rem;
        align-items: center;
        background: rgba(15, 17, 23, 0.6);
        border: 1px solid rgba(255,255,255,0.05);
        border-radius: 20px;
        padding: 0.4rem 1rem;
        margin-top: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)


def render_wizard_stepper(current_step: int):
    if current_step > 5:
        return
    steps = [
        (1, "Profile"),
        (2, "Preferences"),
        (3, "Nutrients"),
        (4, "Meal Plan"),
        (5, "Grocery")
    ]
    html_code = '<div class="stepper-container">'
    for i, (step_num, step_name) in enumerate(steps):
        is_active = step_num == current_step
        is_done = step_num < current_step

        class_name = "step-item"
        if is_active:
            class_name += " active"
        elif is_done:
            class_name += " done"

        icon = "âœ“" if is_done else str(step_num)

        html_code += f"""
        <div class="{class_name}">
            <div class="step-icon">{icon}</div>
            <div class="step-label">{step_name}</div>
        </div>
        """
        if i < len(steps) - 1:
            line_class = "step-line filled" if step_num < current_step else "step-line"
            html_code += f'<div class="{line_class}"></div>'

    html_code += '</div>'
    st.markdown(html_code, unsafe_allow_html=True)


# â”€â”€ Session state defaults â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
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
        "report_response": None,
        "inferred_conditions": [],
        "tts_enabled": False,
        "coach_language_code": "",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()


# ——— Sidebar Navigation ————————————————————————————————————————————————————
with st.sidebar:
    st.markdown("## 📞 AI Dietitian Portal")
    st.markdown("*Clinical RAG & Programmable Reminders (Plivo-inspired)*")
    st.caption(f"⚙️ Backend API: {BACKEND_URL}")
    st.divider()
    step_labels = {
        1: "📝 Health Profile",
        2: "🥑 Preferences & Pantry",
        3: "🔬 Nutrient Analysis",
        4: "🍽️ Meal Plan",
        5: "🛒 Grocery List",
        6: "AI Coach Chat",
        7: "Adherence Calendar",
        8: "Health Insights",
        9: "Communications",
        10: "Doctor Dashboard",
        11: "Observability",
    }
    for step, label in step_labels.items():
        if st.session_state.step == step:
            st.markdown(f'<div class="sidebar-active-step">{label}</div>', unsafe_allow_html=True)
        else:
            if st.button(label, key=f"nav_{step}", use_container_width=True):
                st.session_state.step = step
                st.rerun()
    st.markdown(f'<div class="disclaimer">{DISCLAIMER}</div>', unsafe_allow_html=True)


# â”€â”€ Helper: API calls â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
def api_post(endpoint: str, payload: dict) -> dict | None:
    try:
        timeout = 600 if endpoint == "/generate-meal-plan" else 180
        resp = requests.post(f"{BACKEND_URL}{endpoint}", json=payload, timeout=timeout)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.ConnectionError:
        st.error(f"âŒ Cannot connect to backend at {BACKEND_URL}. Is the FastAPI server running?")
    except requests.exceptions.Timeout:
        st.error("â±ï¸ Request timed out. The LLM may be slow â€“ please try again.")
    except requests.exceptions.HTTPError as e:
        status_code = getattr(e.response, "status_code", None)
        if status_code == 429:
            st.error(
                "The hosted AI provider is rate-limited right now. I added a backend fallback meal plan path; "
                "please click Retry once. If this keeps happening, switch meal planning to Gemini or wait a few minutes."
            )
            return None
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


def api_upload(endpoint: str, file_obj, field_name: str = "file") -> dict | None:
    try:
        files = {
            field_name: (
                file_obj.name,
                file_obj.getvalue(),
                getattr(file_obj, "type", None) or "application/octet-stream",
            )
        }
        resp = requests.post(f"{BACKEND_URL}{endpoint}", files=files, timeout=180)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.ConnectionError:
        st.error(f"Cannot connect to backend at {BACKEND_URL}. Is the FastAPI server running?")
    except requests.exceptions.HTTPError as e:
        try:
            detail = e.response.json().get("detail", "The upload could not be completed.")
        except Exception:
            detail = "The upload could not be completed."
        st.error(str(detail))
    except Exception as e:
        st.error(f"Upload error: {e}")
    return None


def api_upload_bytes(
    endpoint: str,
    content: bytes,
    filename: str,
    content_type: str,
    field_name: str = "file",
    data: dict | None = None,
) -> dict | None:
    try:
        files = {field_name: (filename, content, content_type)}
        resp = requests.post(f"{BACKEND_URL}{endpoint}", files=files, data=data or {}, timeout=180)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        st.error(f"Audio upload error: {e}")
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


# â”€â”€ Step 1: Health Profile â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
def step1_health_profile():
    st.markdown('<p class="main-header">ðŸ“‹ Step 1 â€” Health Profile</p>', unsafe_allow_html=True)
    st.markdown("Tell us about yourself so we can compute your personalised nutrient needs.")

    uploaded_report = st.file_uploader("Upload lab report (PDF, PNG, JPG)", type=["pdf", "png", "jpg", "jpeg"])
    if uploaded_report and st.button("Extract biomarkers from report", use_container_width=True):
        with st.spinner("Extracting biomarkers and clinical flags..."):
            report_response = api_upload("/api/upload-report", uploaded_report)
        if report_response:
            st.session_state.report_response = report_response
            st.session_state.inferred_conditions = report_response.get("inferred_conditions", [])
            st.success("Report parsed. Review the extracted values below.")

    report_response = st.session_state.get("report_response")
    if report_response:
        biomarkers = report_response.get("biomarkers", {})
        statuses = report_response.get("statuses", {})
        rows = [
            {"Biomarker": key.replace("_", " ").title(), "Value": value, "Status": statuses.get(key, "missing")}
            for key, value in biomarkers.items()
            if value is not None
        ]
        if rows:
            df = pd.DataFrame(rows)
            styled = df.style.apply(
                lambda row: [
                    "background-color: #3b1f1f; color: #ffd6d6" if row["Status"] in {"high", "low"} else ""
                    for _ in row
                ],
                axis=1,
            )
            st.dataframe(styled, use_container_width=True, hide_index=True)
        inferred = report_response.get("inferred_conditions", [])
        if inferred:
            st.info("Inferred from report: " + ", ".join(inferred))

    disease_options = [
        "Type-2 Diabetes",
        "Prediabetes",
        "Hypertension",
        "High Cholesterol",
        "High Triglycerides",
        "Hypothyroidism",
        "Anemia",
        "Chronic Kidney Disease",
        "Vitamin D Deficiency",
        "Vitamin B12 Deficiency",
        "Obesity",
        "Underweight",
    ]
    inferred_defaults = [
        disease for disease in st.session_state.get("inferred_conditions", [])
        if disease in disease_options
    ]

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
            bmr_equation_label = st.radio(
                "BMR Equation",
                ["Mifflin-St Jeor", "ICMR-NIN (WHO/FAO/UNU)"],
                horizontal=False,
            )
        with col3:
            selected_diseases = st.multiselect("Health Profile", disease_options, default=inferred_defaults)
            other_diseases = st.text_area("Other Conditions", placeholder="e.g. PCOS, fatty liver", height=50)
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

        submitted = st.form_submit_button("âœ… Save & Continue â†’", use_container_width=True)

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
            "diseases": selected_diseases + [d.strip() for d in other_diseases.split(",") if d.strip()],
            "medications": [m.strip() for m in medications.split(",") if m.strip()],
            "addictions": {"smoking": smoking, "alcohol": alcohol, "tobacco": tobacco},
            "bmr_equation": (
                "icmr_nin_who_fao_unu"
                if bmr_equation_label == "ICMR-NIN (WHO/FAO/UNU)"
                else "mifflin_st_jeor"
            ),
            "lab_report": st.session_state.get("report_response"),
        }
        bmi = weight / (height / 100) ** 2
        st.success(f"âœ… Profile saved! BMI = **{bmi:.1f}**")
        st.session_state.step = 2
        st.rerun()


# â”€â”€ Step 2: Preferences & Pantry â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
def step2_preferences():
    st.markdown('<p class="main-header">ðŸ¥¦ Step 2 â€” Preferences & Pantry</p>', unsafe_allow_html=True)

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
            "ðŸ§º Pantry Ingredients (comma-separated)",
            placeholder="e.g. rice, dal, onion, tomato, ginger, garlic, oil, turmeric",
            height=80,
        )

        col_back, col_next = st.columns(2)
        with col_back:
            back = st.form_submit_button("â† Back", use_container_width=True)
        with col_next:
            submitted = st.form_submit_button("âœ… Save & Analyse Nutrients â†’", use_container_width=True)

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


# â”€â”€ Step 3: Nutrient Analysis â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
def step3_nutrients():
    st.markdown('<p class="main-header">ðŸ”¬ Step 3 â€” Nutrient Analysis</p>', unsafe_allow_html=True)

    if st.session_state.nutrient_response is not None:
        if st.button("Refresh nutrient analysis", use_container_width=True):
            st.session_state.nutrient_response = None
            st.rerun()

    if st.session_state.nutrient_response is None:
        with st.spinner("ðŸ¤– Analysing your health profile via ICMR-NIN guidelines â€¦"):
            payload = {"health_profile": st.session_state.health_profile}
            response = api_post("/predict-nutrients", payload)
            if response:
                st.session_state.nutrient_response = response

    resp = st.session_state.nutrient_response
    if resp is None:
        if st.button("â† Back"):
            st.session_state.step = 2
            st.rerun()
        return

    targets = resp.get("daily_targets", {})

    st.subheader("ðŸ“Š Your Daily Nutrient Targets")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("ðŸ”¥ Calories", f"{targets.get('calories', 0):.0f} kcal")
    c2.metric("ðŸ’ª Protein", f"{targets.get('protein_g', 0):.1f} g")
    c3.metric("ðŸŒ¾ Carbs", f"{targets.get('carbs_g', 0):.1f} g")
    c4.metric("ðŸ«’ Fat", f"{targets.get('fat_g', 0):.1f} g")

    c5, c6, c7 = st.columns(3)
    c5.metric("ðŸŒ¿ Fiber", f"{targets.get('fiber_g', 0):.1f} g")
    c6.metric("ðŸ’§ Water", f"{targets.get('water_ml', 0):.0f} ml")
    c7.metric("ðŸ“‰ BMR", f"{resp.get('bmr', 0):.0f} kcal")

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
        st.subheader("ðŸ§ª Disease-Specific Micronutrients")
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
            line_color="#323dfe",
        ))
        fig.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
            height=360,
            showlegend=False,
            paper_bgcolor="#0f1117",
            plot_bgcolor="#0f1117",
            font_color="#f9fafb",
        )
        st.plotly_chart(fig, use_container_width=True)

    if resp.get("deficiency_risks"):
        with st.expander("Nutrient Gap Alerts"):
            for risk in resp["deficiency_risks"]:
                st.warning(risk)

    if resp.get("disease_notes"):
        with st.expander("ðŸ¥ Disease Adjustments Applied"):
            for note in resp["disease_notes"]:
                st.markdown(f"- {note}")

    if resp.get("medication_interactions"):
        with st.expander("ðŸ’Š Medication Interaction Warnings"):
            for note in resp["medication_interactions"]:
                st.warning(note)

    if resp.get("icmr_references"):
        with st.expander("ðŸ“š ICMR-NIN Guideline References"):
            for ref in resp["icmr_references"]:
                st.caption(ref)

    col_back, col_next = st.columns(2)
    with col_back:
        if st.button("â† Back"):
            st.session_state.step = 2
            st.rerun()
    with col_next:
        if st.button("ðŸ½ï¸ Generate 7-Day Meal Plan â†’", use_container_width=True, type="primary"):
            st.session_state.meal_plan_attempted = False
            st.session_state.step = 4
            st.rerun()


# â”€â”€ Step 4: Meal Plan â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
def step4_meal_plan():
    st.markdown('<p class="main-header">ðŸ½ï¸ Step 4 â€” 7-Day Indian Meal Plan</p>', unsafe_allow_html=True)

    if not st.session_state.health_profile or not st.session_state.preference_profile or not st.session_state.nutrient_response:
        st.warning("Complete Health Profile, Preferences & Pantry, and Nutrient Analysis before generating a meal plan.")
        if st.button("â† Back"):
            st.session_state.step = 3
            st.rerun()
        return

    if st.session_state.meal_plan_response is None and not st.session_state.meal_plan_attempted:
        st.session_state.meal_plan_attempted = True
        with st.spinner("ðŸ‘¨â€ðŸ³ Generating your personalised 7-day meal plan â€¦"):
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
        if st.button("â† Back"):
            st.session_state.step = 3
            st.rerun()
        return

    week = plan.get("week", [])
    day_names = [d["day"] for d in week]
    selected_day = st.selectbox("ðŸ“… Select Day", day_names)
    day_data = next((d for d in week if d["day"] == selected_day), {})

    MEAL_ICONS = {
        "breakfast": "ðŸŒ…",
        "mid_morning_snack": "ðŸŽ",
        "lunch": "â˜€ï¸",
        "evening_snack": "ðŸµ",
        "dinner": "ðŸŒ™",
    }

    for meal_key, icon in MEAL_ICONS.items():
        meal = day_data.get(meal_key, {})
        if not meal:
            continue
        meal_label = meal_key.replace("_", " ").title()
        with st.expander(f"{icon} **{meal_label}** â€” {meal.get('name', '')}  ({meal.get('calories', 0):.0f} kcal)"):
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
                st.markdown(f"[â–¶ï¸ Watch Recipe Tutorial]({meal['youtube_url']})")
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
        st.subheader("ðŸ“ˆ Daily Nutrition Summary")
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
        if st.button("â† Back"):
            st.session_state.step = 3
            st.rerun()
    with col_next:
        if st.button("ðŸ›’ Generate Grocery List â†’", use_container_width=True, type="primary"):
            st.session_state.step = 5
            st.rerun()

    if st.button("Open AI Coach for swaps or explanations", use_container_width=True):
        st.session_state.step = 6
        st.rerun()

    meal_json = json.dumps(plan, indent=2)
    st.download_button("â¬‡ï¸ Download Meal Plan (JSON)", meal_json, "meal_plan.json", "application/json")


# â”€â”€ Step 5: Grocery List â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
def step5_grocery():
    st.markdown('<p class="main-header">ðŸ›’ Step 5 â€” Weekly Grocery List</p>', unsafe_allow_html=True)

    if st.session_state.grocery_response is None:
        with st.spinner("ðŸ›’ Building your grocery list â€¦"):
            payload = {
                "meal_plan": st.session_state.meal_plan_response,
                "pantry_ingredients": st.session_state.preference_profile.get("pantry_ingredients", []),
            }
            resp = api_post("/generate-grocery-list", payload)
            if resp:
                st.session_state.grocery_response = resp

    grocery = st.session_state.grocery_response
    if not grocery:
        if st.button("â† Back"):
            st.session_state.step = 4
            st.rerun()
        return

    items = grocery.get("items", [])
    total = grocery.get("total_estimated_cost_inr", 0)
    st.metric("ðŸ§¾ Estimated Weekly Cost", f"â‚¹{total:.0f}")

    by_category: dict[str, list] = defaultdict(list)
    for item in items:
        by_category[item.get("category", "General")].append(item)

    CATEGORY_ICONS = {
        "Grains": "ðŸŒ¾", "Protein": "ðŸ’ª", "Dairy": "ðŸ¥›",
        "Vegetables": "ðŸ¥¦", "Fruits": "ðŸŽ", "Fats & Oils": "ðŸ«’",
        "Nuts & Seeds": "ðŸ¥œ", "Spices": "ðŸŒ¶ï¸", "General": "ðŸ›ï¸",
    }
    for category, cat_items in by_category.items():
        icon = CATEGORY_ICONS.get(category, "ðŸ›ï¸")
        st.subheader(f"{icon} {category}")
        cols = st.columns(3)
        for i, item in enumerate(cat_items):
            with cols[i % 3]:
                cost_str = f"  â‚¹{item['estimated_cost_inr']:.0f}" if item.get("estimated_cost_inr") else ""
                st.markdown(
                    f'<span class="grocery-badge">ðŸ›’ {item["ingredient"]} â€” {item["quantity"]}{cost_str}</span>',
                    unsafe_allow_html=True,
                )

    if grocery.get("notes"):
        with st.expander("ðŸ’¡ Grocery Tips"):
            for note in grocery["notes"]:
                st.info(note)

    if st.button("ðŸ“„ Download as PDF"):
        pdf_bytes = _generate_pdf(grocery, st.session_state.meal_plan_response)
        st.download_button("â¬‡ï¸ Download PDF", pdf_bytes, "dietitian_plan.pdf", "application/pdf")

    st.divider()
    if st.button("â† Back to Meal Plan"):
        st.session_state.step = 4
        st.rerun()
    if st.button("ðŸ”„ Start Over"):
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.rerun()


def _assistant_payload(message: str) -> dict:
    return {
        "user_id": st.session_state.user_id,
        "message": message,
        "preferred_language": st.session_state.get("coach_language_code") or None,
        "health_profile": st.session_state.health_profile or None,
        "preference_profile": st.session_state.preference_profile or None,
        "daily_targets": (st.session_state.nutrient_response or {}).get("daily_targets"),
        "meal_plan": st.session_state.meal_plan_response,
        "grocery_list": st.session_state.grocery_response,
    }


COACH_LANGUAGES = {
    "Auto-detect": "",
    "English": "en",
    "Hindi": "hi",
    "Hinglish": "hinglish",
}

TTS_LANGS = {
    "": "en-IN",
    "en": "en-IN",
    "hi": "hi-IN",
    "hinglish": "en-IN",
}


def _tts_component(text: str = "", lang_code: str = "en", stop: bool = False) -> None:
    safe_text = json.dumps(text or "")
    safe_lang = json.dumps(TTS_LANGS.get(lang_code or "en", "en-IN"))
    should_stop = "true" if stop else "false"
    components.html(
        f"""
        <script>
        function cleanForSpeech(raw) {{
            return String(raw || "")
                .replace(/```[\\s\\S]*?```/g, " ")
                .replace(/`([^`]*)`/g, "$1")
                .replace(/\\*\\*|__|[*_#>~-]/g, " ")
                .replace(/\\[[^\\]]*\\]\\([^)]*\\)/g, function(match) {{
                    const label = match.match(/\\[([^\\]]*)\\]/);
                    return label ? label[1] : " ";
                }})
                .replace(/https?:\\/\\/\\S+/g, " ")
                .replace(/\\s+/g, " ")
                .trim();
        }}
        if ({should_stop}) {{
            window.speechSynthesis.cancel();
        }} else {{
            const text = cleanForSpeech({safe_text});
            if (text) {{
                const speak = () => {{
                    const utterance = new SpeechSynthesisUtterance(text);
                    utterance.lang = {safe_lang};
                    utterance.rate = 0.9;
                    utterance.pitch = 1.0;
                    const voices = window.speechSynthesis.getVoices();
                    const preferred = voices.find(v => v.lang === {safe_lang})
                        || voices.find(v => v.lang === "en-IN")
                        || voices.find(v => v.lang.startsWith({safe_lang}.slice(0, 2)))
                        || voices.find(v => v.lang.startsWith("en"));
                    if (preferred) utterance.voice = preferred;
                    window.speechSynthesis.cancel();
                    window.speechSynthesis.speak(utterance);
                }};
                if (window.speechSynthesis.getVoices().length) {{
                    speak();
                }} else {{
                    window.speechSynthesis.onvoiceschanged = speak;
                }}
            }}
        }}
        </script>
        """,
        height=0,
    )


def step6_chatbot():
    st.markdown(
        """
        <div class="coach-hero">
            <p class="coach-title">AI Nutrition Coach</p>
            <div class="coach-subtitle">Ask by text, voice, or image. Grounded in your profile, labs, meals, and ICMR-NIN context.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

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

    st.markdown('<div class="chatgpt-composer">', unsafe_allow_html=True)
    if st.session_state.pop("clear_coach_message_on_next_run", False):
        st.session_state.coach_message_text = ""
    seeded = st.session_state.pop("chat_input_seed", "")
    if seeded and not st.session_state.get("coach_message_text"):
        st.session_state.coach_message_text = seeded

    user_text = st.text_area(
        "Message",
        key="coach_message_text",
        placeholder="Ask for follow-up changes",
        height=88,
        label_visibility="collapsed",
    )

    last_answer = next(
        (msg["content"] for msg in reversed(st.session_state.chat_messages) if msg.get("role") == "assistant"),
        "",
    )
    chat_upload = None
    audio = None
    action_cols = st.columns([0.42, 1.3, 0.78, 0.72, 0.72, 0.52, 0.48])
    with action_cols[0]:
        with st.popover("+", use_container_width=True):
            chat_upload = st.file_uploader(
                "Attach image/PDF",
                type=["png", "jpg", "jpeg", "webp", "pdf"],
                key="coach_image_upload",
            )
    with action_cols[1]:
        language_label = st.selectbox(
            "Language",
            list(COACH_LANGUAGES.keys()),
            index=list(COACH_LANGUAGES.values()).index(st.session_state.get("coach_language_code", ""))
            if st.session_state.get("coach_language_code", "") in COACH_LANGUAGES.values()
            else 0,
            help="Hinglish means Roman script only: Hindi + English medical words.",
            label_visibility="collapsed",
        )
        st.session_state.coach_language_code = COACH_LANGUAGES[language_label]
    with action_cols[2]:
        st.session_state.tts_enabled = st.checkbox("Auto-read", value=st.session_state.get("tts_enabled", False))
    with action_cols[3]:
        if st.button("Read last", use_container_width=True, disabled=not bool(last_answer)):
            _tts_component(last_answer, st.session_state.get("coach_language_code") or "en")
    with action_cols[4]:
        if st.button("Stop read", use_container_width=True):
            _tts_component(stop=True)
    with action_cols[5]:
        if mic_recorder:
            audio = mic_recorder(
                start_prompt="ðŸŽ™",
                stop_prompt="âœ“",
                key="coach_voice_query",
                format="webm",
            )
        else:
            with st.popover("ðŸŽ™", use_container_width=True):
                st.error("Mic dictation is not available in this Streamlit Python environment.")
                st.code(f'"{sys.executable}" -m pip install streamlit-mic-recorder', language="powershell")
                if MIC_IMPORT_ERROR:
                    st.caption(f"Import error: {MIC_IMPORT_ERROR}")
    with action_cols[6]:
        send = st.button("â†‘", use_container_width=True, type="primary")

    if audio and audio.get("bytes") and audio.get("id") != st.session_state.get("last_voice_id"):
        st.session_state.last_voice_id = audio.get("id")
        with st.spinner("Transcribing voice query..."):
            transcript_response = api_upload_bytes(
                "/api/voice/transcribe",
                audio["bytes"],
                "voice-query.webm",
                "audio/webm",
                data=({"source_language": st.session_state.coach_language_code} if st.session_state.coach_language_code else None),
            )
        if transcript_response:
            st.session_state.chat_input_seed = transcript_response.get("transcript") or transcript_response.get("english_text", "")
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    message = user_text.strip() if send else ""
    if message:
        if chat_upload:
            with st.spinner("Reading attached image/PDF..."):
                image_context = api_upload("/api/chat-image", chat_upload)
            if image_context and image_context.get("summary"):
                message = (
                    f"{message}\n\nUploaded image/PDF context:\n"
                    f"{image_context['summary']}"
                )
        st.session_state.chat_messages.append({"role": "user", "content": message})
        with st.chat_message("user"):
            st.markdown(message)
        with st.chat_message("assistant"):
            with st.spinner("Thinking with your nutrition context..."):
                response = api_post("/chat", _assistant_payload(message))
            answer = (response or {}).get("answer", "I could not generate a response right now.")
            st.markdown(answer)
            if st.session_state.get("tts_enabled"):
                response_language = (response or {}).get("detected_language") or st.session_state.coach_language_code or "en"
                _tts_component(answer, response_language)
        st.session_state.chat_messages.append({"role": "assistant", "content": answer})
        st.session_state.clear_coach_message_on_next_run = True
        st.rerun()


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
        fig = go.Figure(go.Bar(x=[d["date"] for d in daily], y=[d["score"] for d in daily], marker_color="#cd3ef9"))
        fig.update_layout(height=300, title="Daily Adherence Score", paper_bgcolor="#0f1117", plot_bgcolor="#0f1117", font_color="#f9fafb")
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
        fig = go.Figure(go.Bar(x=names, y=scores, marker_color="#323dfe"))
        fig.update_layout(height=360, title="Nutrient Compliance", paper_bgcolor="#0f1117", plot_bgcolor="#0f1117", font_color="#f9fafb")
        st.plotly_chart(fig, use_container_width=True)


# â”€â”€ PDF Generator â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def step9_communications():
    st.markdown('<p class="main-header">Clinic Communications</p>', unsafe_allow_html=True)
    st.caption("Mock SMS/WhatsApp/voice workflow for reminders, inbound replies, patient follow-ups, and Plivo-style observability.")

    user_id = st.text_input("Patient ID", value=st.session_state.get("user_id", "demo-user"), key="comm_user_id")
    st.session_state.user_id = user_id

    metrics = api_get(f"/api/communications/metrics?user_id={user_id}") or {}
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Messages", metrics.get("total_messages", 0))
    m2.metric("Outbound", metrics.get("outbound_messages", 0))
    m3.metric("Reply rate", f"{metrics.get('reply_rate_percent', 0)}%")
    m4.metric("High risk", metrics.get("high_risk_count", 0))

    with st.expander("Create automated reminder", expanded=False):
        r1, r2 = st.columns(2)
        with r1:
            reminder_type = st.selectbox("Reminder type", ["meal", "hydration", "supplement", "adherence", "follow_up"], key="auto_reminder_type")
            title = st.text_input("Title", value="Lunch check-in", key="auto_reminder_title")
            schedule = st.text_input("Schedule", value="Daily 13:00", key="auto_reminder_schedule")
            reminder_channel = st.selectbox("Delivery channel", ["in_app", "whatsapp_ready", "sms", "push", "email"], key="auto_reminder_channel")
        with r2:
            patient_name = st.text_input("Patient name", value="there", key="auto_patient_name")
            phone = st.text_input("Phone", value="+91XXXXXXXXXX", key="auto_phone")
            meal_type_meta = st.text_input("Meal type", value="lunch", key="auto_meal_type")
            meal_name_meta = st.text_input("Meal / supplement", value="2 roti + dal + sabzi", key="auto_meal_name")
        if st.button("Save automated reminder", use_container_width=True):
            payload = {
                "user_id": user_id,
                "reminder_type": reminder_type,
                "title": title,
                "schedule": schedule,
                "channel": reminder_channel,
                "enabled": True,
                "metadata": {"name": patient_name, "recipient": phone, "meal_type": meal_type_meta, "meal_name": meal_name_meta, "reminder_type": reminder_type},
            }
            if api_post("/reminders", payload):
                st.success("Reminder saved. Use dispatch to send active reminders through the mock communication layer.")
                st.rerun()

    d1, d2 = st.columns([1, 2])
    with d1:
        if st.button("Dispatch active reminders", type="primary", use_container_width=True):
            response = api_post(f"/reminders/dispatch-active?user_id={user_id}", {})
            if response:
                st.success(f"Dispatched {response.get('dispatched', 0)} active reminders.")
                st.rerun()
    with d2:
        active = (api_get(f"/reminders/active/{user_id}") or {}).get("items", [])
        st.caption(f"Active reminders for this patient: {len(active)}")

    st.divider()
    with st.expander("Voice assistant demo", expanded=False):
        st.caption("Simulate a transcribed phone call. The assistant classifies intent, flags risk, logs the call, and produces a safe response.")
        v1, v2 = st.columns([2, 1])
        with v1:
            voice_transcript = st.text_area("Transcript", value="Mujhe lunch ke liye roti dal ka option chahiye", height=90, key="voice_assistant_transcript")
        with v2:
            caller = st.text_input("Caller", value="+91XXXXXXXXXX", key="voice_assistant_caller")
            detected_lang = st.selectbox("Language hint", ["", "en", "hi", "hinglish"], key="voice_assistant_lang")
        if st.button("Run voice assistant", use_container_width=True):
            payload = {"user_id": user_id, "transcript": voice_transcript, "caller": caller, "detected_language": detected_lang or None}
            response = api_post("/api/voice/assistant", payload)
            if response:
                a1, a2, a3 = st.columns(3)
                a1.metric("Intent", response.get("intent", "unknown"))
                a2.metric("Risk", response.get("risk_level", "low"))
                a3.metric("Human review", "Yes" if response.get("requires_human_review") else "No")
                st.success(response.get("answer", ""))
                st.rerun()

    st.divider()
    left, right = st.columns(2)
    with left:
        st.subheader("Send reminder")
        channel = st.selectbox("Channel", ["sms", "whatsapp", "voice", "in_app"], key="comm_channel")
        message_type = st.selectbox("Message type", ["meal_reminder", "hydration", "supplement", "adherence", "follow_up", "freeform"], key="comm_type")
        recipient = st.text_input("Phone / recipient", value="+91XXXXXXXXXX", key="comm_recipient")
        default_message = "Hi, your planned meal is due. Reply 1 if completed, 2 if skipped, 3 for an alternative."
        content = st.text_area("Message", value=default_message, height=110, key="comm_content")
        if st.button("Send mock reminder", type="primary", use_container_width=True):
            payload = {"user_id": user_id, "channel": channel, "recipient": recipient, "message_type": message_type, "content": content, "metadata": {"source": "streamlit_demo", "interview_alignment": "plivo"}}
            response = api_post("/api/communications/send-reminder", payload)
            if response:
                st.success("Mock reminder sent and logged.")
                st.rerun()

    with right:
        st.subheader("Simulate patient reply")
        inbound_channel = st.selectbox("Reply channel", ["sms", "whatsapp", "voice", "in_app"], key="inbound_channel")
        sender = st.text_input("Sender", value="+91XXXXXXXXXX", key="inbound_sender")
        reply = st.text_area("Reply", value="1", height=110, key="inbound_reply")
        st.caption("Try: 1, 2, 3, 'doctor call', or 'severe dizziness'.")
        if st.button("Receive mock reply", use_container_width=True):
            payload = {"user_id": user_id, "channel": inbound_channel, "sender": sender, "content": reply, "metadata": {"source": "streamlit_demo"}}
            response = api_post("/api/communications/inbound-reply", payload)
            if response:
                st.info(f"Intent: {response.get('intent')} | Risk: {response.get('risk_level')}")
                st.write(response.get("recommended_action"))
                st.rerun()

    st.divider()
    st.subheader("Communication timeline")
    history = (api_get(f"/api/communications/history/{user_id}") or {}).get("items", [])
    if not history:
        st.info("No communication records yet. Send a reminder or simulate a reply.")
        return

    rows = []
    for item in reversed(history[-25:]):
        rows.append({"time": item.get("created_at"), "channel": item.get("channel"), "direction": item.get("direction"), "type": item.get("message_type"), "status": item.get("status"), "intent": item.get("intent") or "-", "risk": item.get("risk_level"), "content": item.get("content")})
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    high_risk = metrics.get("latest_high_risk", [])
    if high_risk:
        st.warning("Latest high-risk replies need doctor review.")
        for item in high_risk:
            st.write(f"{item.get('created_at')} - {item.get('content')}")

def step10_doctor_dashboard():
    st.markdown('<p class="main-header">Doctor Dashboard</p>', unsafe_allow_html=True)
    st.caption("Clinician-facing view of patient communication, adherence, risk alerts, and suggested follow-up actions.")

    user_id = st.text_input("Patient ID", value=st.session_state.get("user_id", "demo-user"), key="doctor_user_id")
    dashboard = api_get(f"/api/clinic/patient/{user_id}") or {}
    if not dashboard:
        st.info("No dashboard data available yet. Use Clinic Communications to send reminders and simulate replies.")
        return

    c1, c2, c3, c4 = st.columns(4)
    counts = dashboard.get("counts", {})
    c1.metric("Risk", str(dashboard.get("risk_level", "low")).title())
    c2.metric("Messages", counts.get("communications", 0))
    c3.metric("Skipped logs", counts.get("skipped_adherence_logs", 0))
    c4.metric("High-risk alerts", counts.get("high_risk_alerts", 0))

    st.subheader("Suggested next action")
    st.info(dashboard.get("suggested_action", "Continue routine follow-up."))

    alerts = dashboard.get("alerts", [])
    if alerts:
        st.subheader("Alerts")
        for alert in alerts:
            if alert.get("priority") == "high":
                st.error(f"{alert.get('title')}: {alert.get('detail')}")
            else:
                st.warning(f"{alert.get('title')}: {alert.get('detail')}")

    st.divider()
    a1, a2, a3 = st.columns(3)
    adherence = dashboard.get("adherence_summary", {})
    a1.metric("Average adherence", f"{adherence.get('average_score', 0)}%")
    a2.metric("Current streak", adherence.get("current_streak", 0))
    a3.metric("Completed meals", adherence.get("completed_meals", 0))

    daily = adherence.get("daily_scores", [])
    if daily:
        fig = go.Figure(go.Bar(x=[d["date"] for d in daily], y=[d["score"] for d in daily], marker_color="#323dfe"))
        fig.update_layout(height=280, title="Adherence Score Trend", paper_bgcolor="#0f1117", plot_bgcolor="#0f1117", font_color="#f9fafb")
        st.plotly_chart(fig, use_container_width=True)

    st.divider()
    t1, t2 = st.tabs(["Communication timeline", "Adherence logs"])
    with t1:
        timeline = list(reversed(dashboard.get("timeline", [])[-25:]))
        if timeline:
            rows = [{
                "time": item.get("created_at"),
                "channel": item.get("channel"),
                "direction": item.get("direction"),
                "intent": item.get("intent") or "-",
                "risk": item.get("risk_level"),
                "content": item.get("content"),
            } for item in timeline]
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        else:
            st.info("No communications logged yet.")
    with t2:
        latest = list(reversed(dashboard.get("latest_adherence", [])[-20:]))
        if latest:
            rows = [{
                "date": item.get("date"),
                "meal": item.get("meal_type"),
                "status": item.get("status"),
                "notes": item.get("notes"),
            } for item in latest]
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        else:
            st.info("No adherence logs yet.")

def step11_observability():
    st.markdown('<p class="main-header">Observability</p>', unsafe_allow_html=True)
    st.caption("Operational view for communication reliability, patient replies, risk signals, and demo readiness.")

    user_id_filter = st.text_input("Patient ID filter", value=st.session_state.get("user_id", "demo-user"), key="obs_user_id")
    scope_all = st.checkbox("Show all users", value=False, key="obs_all_users")
    endpoint = "/api/observability/snapshot" if scope_all else f"/api/observability/snapshot?user_id={user_id_filter}"
    snapshot = api_get(endpoint) or {}
    kpis = snapshot.get("kpis", {})

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Messages", kpis.get("total_messages", 0))
    c2.metric("Reply rate", f"{kpis.get('reply_rate_percent', 0)}%")
    c3.metric("Delivery", f"{kpis.get('delivery_success_percent', 0)}%")
    c4.metric("Voice", kpis.get("voice_interactions", 0))
    c5.metric("High risk", kpis.get("high_risk_alerts", 0))

    readiness = snapshot.get("demo_readiness", {})
    st.subheader("Demo readiness")
    st.progress(int(readiness.get("score_percent", 0)))
    checks = readiness.get("checks", {})
    if checks:
        cols = st.columns(len(checks))
        for idx, (name, ok) in enumerate(checks.items()):
            cols[idx].metric(name.replace("_", " ").title(), "Ready" if ok else "Missing")

    alerts = snapshot.get("alerts", [])
    if alerts:
        st.subheader("Operational alerts")
        for alert in alerts:
            if alert.get("priority") == "high":
                st.error(alert.get("message"))
            else:
                st.warning(alert.get("message"))

    st.divider()
    breakdowns = snapshot.get("breakdowns", {})
    b1, b2 = st.columns(2)
    with b1:
        by_channel = breakdowns.get("by_channel", {})
        if by_channel:
            fig = go.Figure(go.Bar(x=list(by_channel.keys()), y=list(by_channel.values()), marker_color="#323dfe"))
            fig.update_layout(height=280, title="Messages by Channel", paper_bgcolor="#0f1117", plot_bgcolor="#0f1117", font_color="#f9fafb")
            st.plotly_chart(fig, use_container_width=True)
    with b2:
        by_intent = breakdowns.get("by_intent", {})
        if by_intent:
            fig = go.Figure(go.Bar(x=list(by_intent.keys()), y=list(by_intent.values()), marker_color="#cd3ef9"))
            fig.update_layout(height=280, title="Inbound Intents", paper_bgcolor="#0f1117", plot_bgcolor="#0f1117", font_color="#f9fafb")
            st.plotly_chart(fig, use_container_width=True)

    r1, r2 = st.columns(2)
    with r1:
        by_risk = breakdowns.get("by_risk", {})
        if by_risk:
            st.subheader("Risk breakdown")
            st.dataframe(pd.DataFrame([{"risk": k, "count": v} for k, v in by_risk.items()]), use_container_width=True, hide_index=True)
    with r2:
        reminders = breakdowns.get("reminders_by_type", {})
        if reminders:
            st.subheader("Reminder types")
            st.dataframe(pd.DataFrame([{"type": k, "count": v} for k, v in reminders.items()]), use_container_width=True, hide_index=True)

    st.divider()
    st.subheader("Recent events")
    events = list(reversed(snapshot.get("recent_events", [])[-20:]))
    if events:
        rows = [{
            "time": item.get("created_at"),
            "channel": item.get("channel"),
            "direction": item.get("direction"),
            "status": item.get("status"),
            "intent": item.get("intent") or "-",
            "risk": item.get("risk_level"),
            "content": item.get("content"),
        } for item in events]
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    else:
        st.info("No operational events yet. Use Clinic Communications to create demo traffic.")
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


# â”€â”€ Router â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
step_map = {
    1: step1_health_profile,
    2: step2_preferences,
    3: step3_nutrients,
    4: step4_meal_plan,
    5: step5_grocery,
    6: step6_chatbot,
    7: step7_adherence_calendar,
    8: step8_insights,
    9: step9_communications,
    10: step10_doctor_dashboard,
    11: step11_observability,
}

step_fn = step_map.get(st.session_state.step, step1_health_profile)
step_fn()

