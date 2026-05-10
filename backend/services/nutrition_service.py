"""
services/nutrition_service.py
Pure-Python nutrient calculation logic (Mifflin-St Jeor).
No LLM dependency – used as a deterministic baseline.
"""
from __future__ import annotations

from backend.models.request_models import HealthProfile
from backend.utils.helpers import calculate_bmr, calculate_tdee


# ── Disease-aware macro adjustments ──────────────────────────────────────────
DISEASE_ADJUSTMENTS: dict[str, dict] = {
    "type-2 diabetes": {"carbs_pct": 0.40, "fiber_g_add": 10, "sodium_mg_limit": 2000},
    "type-1 diabetes": {"carbs_pct": 0.40, "fiber_g_add": 10},
    "hypertension": {"sodium_mg_limit": 1500, "potassium_mg_min": 3500},
    "chronic kidney disease": {"protein_pct": 0.10, "potassium_mg_limit": 2000, "sodium_mg_limit": 1500},
    "hypothyroidism": {"calories_deficit": 200},
    "hyperthyroidism": {"calories_surplus": 300},
    "obesity": {"calories_deficit": 500},
    "underweight": {"calories_surplus": 500},
    "anaemia": {"iron_mg_min": 27, "b12_mcg_min": 2.4},
    "osteoporosis": {"calcium_mg_min": 1200, "vitamin_d_iu_min": 2000},
}

# ── Medication micronutrient interactions ─────────────────────────────────────
MEDICATION_INTERACTIONS: dict[str, dict] = {
    "metformin": {"b12_mcg_min": 2.4, "note": "Metformin reduces B12 absorption; supplement recommended."},
    "warfarin": {"note": "Limit high-Vitamin K foods (spinach, kale). Consistent intake preferred."},
    "statins": {"note": "Avoid grapefruit; CoQ10 depletion possible."},
    "lisinopril": {"potassium_mg_limit": 3500, "note": "ACE inhibitors can raise potassium levels."},
    "levothyroxine": {"note": "Take on empty stomach; avoid calcium/iron supplements within 4 hours."},
}


def compute_baseline_nutrients(profile: HealthProfile) -> dict:
    """
    Calculate TDEE-based macro targets and apply disease / medication adjustments.
    Returns a flat dict ready for JSON serialisation.
    """
    bmr = calculate_bmr(profile.weight_kg, profile.height_cm, profile.age, profile.gender)
    tdee = calculate_tdee(bmr, profile.activity_level)

    # Default macro split (ICMR-NIN reference: 55-60% carbs, 15-20% protein, 20-25% fat)
    carbs_pct = 0.57
    protein_pct = 0.17
    fat_pct = 0.26

    calories = tdee
    disease_notes = []
    medication_notes = []
    micronutrients = {}

    # ── Disease adjustments ───────────────────────────────────────
    diseases_lower = [d.lower() for d in profile.diseases]
    for disease, adj in DISEASE_ADJUSTMENTS.items():
        if any(disease in d for d in diseases_lower):
            if "carbs_pct" in adj:
                carbs_pct = adj["carbs_pct"]
                protein_pct = 0.20
                fat_pct = 1 - carbs_pct - protein_pct
            if "protein_pct" in adj:
                protein_pct = adj["protein_pct"]
            if "calories_deficit" in adj:
                calories -= adj["calories_deficit"]
            if "calories_surplus" in adj:
                calories += adj["calories_surplus"]
            for key in ("fiber_g_add", "sodium_mg_limit", "potassium_mg_min",
                        "potassium_mg_limit", "iron_mg_min", "b12_mcg_min",
                        "calcium_mg_min", "vitamin_d_iu_min"):
                if key in adj:
                    micronutrients[key] = adj[key]
            disease_notes.append(f"Adjustments applied for {disease}.")

    # ── Medication adjustments ────────────────────────────────────
    meds_lower = [m.lower() for m in profile.medications]
    for med, adj in MEDICATION_INTERACTIONS.items():
        if any(med in m for m in meds_lower):
            for key in ("b12_mcg_min", "potassium_mg_limit"):
                if key in adj:
                    micronutrients[key] = adj[key]
            medication_notes.append(adj.get("note", f"Note for {med}."))

    # ── Addiction adjustments ─────────────────────────────────────
    if profile.addictions.smoking != "never":
        micronutrients["vitamin_c_mg_min"] = 110  # smokers need extra Vit C

    protein_g = round((calories * protein_pct) / 4, 1)
    carbs_g = round((calories * carbs_pct) / 4, 1)
    fat_g = round((calories * fat_pct) / 9, 1)
    fiber_g = round(14 + micronutrients.pop("fiber_g_add", 0), 1)
    water_ml = round(profile.weight_kg * 35, 0)   # 35 ml/kg body weight

    return {
        "bmr": round(bmr, 1),
        "tdee": round(tdee, 1),
        "daily_targets": {
            "calories": round(calories, 1),
            "protein_g": protein_g,
            "carbs_g": carbs_g,
            "fat_g": fat_g,
            "fiber_g": fiber_g,
            "water_ml": water_ml,
            "sodium_mg": micronutrients.get("sodium_mg_limit"),
            "potassium_mg": micronutrients.get("potassium_mg_min") or micronutrients.get("potassium_mg_limit"),
            "iron_mg": micronutrients.get("iron_mg_min"),
            "calcium_mg": micronutrients.get("calcium_mg_min"),
            "vitamin_d_iu": micronutrients.get("vitamin_d_iu_min"),
            "b12_mcg": micronutrients.get("b12_mcg_min"),
        },
        "disease_notes": disease_notes,
        "medication_interactions": medication_notes,
    }
