"""ICMR-NIN inspired nutrient reference tables and adequacy scoring helpers."""
from __future__ import annotations

from typing import Any

from backend.models.request_models import HealthProfile


MICRONUTRIENT_UNITS: dict[str, str] = {
    "vitamin_a_mcg": "mcg RAE",
    "vitamin_b1_mg": "mg",
    "vitamin_b2_mg": "mg",
    "vitamin_b3_mg": "mg",
    "vitamin_b5_mg": "mg",
    "vitamin_b6_mg": "mg",
    "vitamin_b7_mcg": "mcg",
    "vitamin_b9_mcg": "mcg",
    "vitamin_b12_mcg": "mcg",
    "vitamin_c_mg": "mg",
    "vitamin_d_iu": "IU",
    "vitamin_e_mg": "mg",
    "vitamin_k_mcg": "mcg",
    "calcium_mg": "mg",
    "iron_mg": "mg",
    "magnesium_mg": "mg",
    "zinc_mg": "mg",
    "potassium_mg": "mg",
    "sodium_mg": "mg",
    "selenium_mcg": "mcg",
    "copper_mg": "mg",
    "phosphorus_mg": "mg",
    "iodine_mcg": "mcg",
    "chloride_mg": "mg",
    "manganese_mg": "mg",
    "chromium_mcg": "mcg",
    "molybdenum_mcg": "mcg",
    "choline_mg": "mg",
    "omega_3_g": "g",
    "omega_6_g": "g",
    "glycemic_load": "score",
    "glycemic_index": "score",
}


# Practical adult targets used by the app. Sex and condition adjustments below
# keep the values personalized while staying aligned with Indian dietary goals:
# diverse foods, adequate protein quality, high fibre, low sodium, and balanced fats.
BASE_MICRONUTRIENT_TARGETS: dict[str, float] = {
    "vitamin_a_mcg": 840,
    "vitamin_b1_mg": 1.4,
    "vitamin_b2_mg": 1.6,
    "vitamin_b3_mg": 16,
    "vitamin_b5_mg": 5,
    "vitamin_b6_mg": 2.0,
    "vitamin_b7_mcg": 30,
    "vitamin_b9_mcg": 220,
    "vitamin_b12_mcg": 2.2,
    "vitamin_c_mg": 80,
    "vitamin_d_iu": 600,
    "vitamin_e_mg": 10,
    "vitamin_k_mcg": 55,
    "calcium_mg": 1000,
    "iron_mg": 19,
    "magnesium_mg": 340,
    "zinc_mg": 12,
    "potassium_mg": 3500,
    "sodium_mg": 2000,
    "selenium_mcg": 40,
    "copper_mg": 1.7,
    "phosphorus_mg": 1000,
    "iodine_mcg": 150,
    "chloride_mg": 2300,
    "manganese_mg": 4,
    "chromium_mcg": 35,
    "molybdenum_mcg": 45,
    "choline_mg": 550,
    "omega_3_g": 1.6,
    "omega_6_g": 10,
    "glycemic_load": 80,
    "glycemic_index": 55,
}


FOOD_SOURCES: dict[str, list[str]] = {
    "vitamin_a_mcg": ["carrot", "pumpkin", "spinach", "mango", "papaya"],
    "vitamin_b1_mg": ["whole wheat", "brown rice", "dal", "groundnuts", "sesame"],
    "vitamin_b2_mg": ["milk", "curd", "eggs", "mushrooms", "almonds"],
    "vitamin_b3_mg": ["groundnuts", "whole grains", "chicken", "fish", "mushrooms"],
    "vitamin_b5_mg": ["mushrooms", "eggs", "curd", "dal", "whole grains"],
    "vitamin_b6_mg": ["banana", "chickpeas", "potato", "fish", "sunflower seeds"],
    "vitamin_b7_mcg": ["eggs", "groundnuts", "almonds", "sweet potato", "soybean"],
    "vitamin_b9_mcg": ["spinach", "amaranth leaves", "chana", "rajma", "sprouts"],
    "iron_mg": ["ragi", "rajma", "chana", "garden cress seeds", "amaranth leaves"],
    "calcium_mg": ["ragi", "curd", "milk", "sesame seeds", "paneer"],
    "vitamin_b12_mcg": ["milk", "curd", "paneer", "eggs", "fish"],
    "vitamin_c_mg": ["amla", "guava", "citrus fruits", "capsicum", "tomato"],
    "vitamin_d_iu": ["fortified milk", "eggs", "fish", "safe sunlight exposure"],
    "vitamin_e_mg": ["sunflower seeds", "almonds", "groundnuts", "mustard oil", "wheat germ"],
    "vitamin_k_mcg": ["spinach", "methi leaves", "cabbage", "broccoli", "drumstick leaves"],
    "potassium_mg": ["banana", "coconut water", "dal", "spinach", "sweet potato"],
    "sodium_mg": ["limit packaged snacks", "limit pickles", "limit papad", "use herbs", "check labels"],
    "magnesium_mg": ["millets", "nuts", "seeds", "whole pulses", "leafy greens"],
    "zinc_mg": ["chana", "rajma", "pumpkin seeds", "eggs", "fish"],
    "selenium_mcg": ["eggs", "fish", "whole grains", "sunflower seeds", "mushrooms"],
    "copper_mg": ["sesame seeds", "cashews", "rajma", "chana", "cocoa"],
    "phosphorus_mg": ["dal", "milk", "curd", "eggs", "fish"],
    "chloride_mg": ["iodized salt", "tomato", "celery", "olives", "seaweed"],
    "manganese_mg": ["whole grains", "millets", "nuts", "tea", "leafy greens"],
    "chromium_mcg": ["whole grains", "broccoli", "potato", "eggs", "spices"],
    "molybdenum_mcg": ["dal", "beans", "peas", "whole grains", "nuts"],
    "choline_mg": ["eggs", "soybean", "milk", "fish", "peanuts"],
    "omega_3_g": ["flaxseed", "chia seeds", "walnuts", "fish", "mustard oil"],
    "omega_6_g": ["sunflower oil", "sesame oil", "groundnuts", "seeds", "nuts"],
    "iodine_mcg": ["iodized salt", "curd", "eggs", "fish"],
    "glycemic_load": ["whole pulses", "millets", "vegetables", "curd", "smaller rice portions"],
    "glycemic_index": ["low-GI grains", "dal", "beans", "vegetables", "nuts"],
}


def build_micronutrient_targets(profile: HealthProfile) -> dict[str, float]:
    targets = dict(BASE_MICRONUTRIENT_TARGETS)
    if profile.gender == "female":
        targets["iron_mg"] = 29
        targets["calcium_mg"] = 1000
    if profile.age > 60:
        targets["calcium_mg"] = 1200
        targets["vitamin_d_iu"] = 800

    diseases = " ".join(profile.diseases).lower()
    medications = " ".join(profile.medications).lower()
    if "diabetes" in diseases or "pcos" in diseases:
        targets["glycemic_load"] = 60
        targets["glycemic_index"] = 50
        targets["fiber_g"] = 30
    if "hypertension" in diseases:
        targets["sodium_mg"] = 1500
        targets["potassium_mg"] = 4000
    if "anaemia" in diseases or "anemia" in diseases:
        targets["iron_mg"] = max(targets["iron_mg"], 27)
        targets["vitamin_c_mg"] = 100
        targets["vitamin_b12_mcg"] = 2.4
    if "kidney" in diseases or "ckd" in diseases:
        targets["sodium_mg"] = 1500
        targets["potassium_mg"] = min(targets["potassium_mg"], 2500)
        targets["phosphorus_mg"] = 800
    if "metformin" in medications:
        targets["vitamin_b12_mcg"] = max(targets["vitamin_b12_mcg"], 2.4)
    if "warfarin" in medications:
        targets["vitamin_k_mcg"] = 55
    return targets


def score_nutrient_adequacy(targets: dict[str, Any], intake: dict[str, Any] | None = None) -> dict[str, Any]:
    intake = intake or targets
    scores: dict[str, dict[str, Any]] = {}
    for key, target in targets.items():
        if not isinstance(target, (int, float)) or target <= 0:
            continue
        actual = intake.get(key, target)
        if not isinstance(actual, (int, float)):
            continue
        if key in {"sodium_mg", "glycemic_load", "glycemic_index"}:
            ratio = max(0, 1 - max(actual - target, 0) / target)
        else:
            ratio = min(actual / target, 1.2) / 1.2
        status = "adequate" if ratio >= 0.75 else "low"
        scores[key] = {
            "target": round(target, 2),
            "actual": round(actual, 2),
            "unit": MICRONUTRIENT_UNITS.get(key, ""),
            "score": round(ratio * 100, 1),
            "status": status,
            "food_sources": FOOD_SOURCES.get(key, []),
        }
    average = round(sum(item["score"] for item in scores.values()) / max(len(scores), 1), 1)
    return {"overall_score": average, "nutrients": scores}  
