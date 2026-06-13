"""
prompts/nutrient_prompt.py
Prompt builder for the Clinical Analyst Agent.
"""
from __future__ import annotations


NUTRIENT_SYSTEM = """You are a certified clinical dietitian and medical nutrition specialist.
Your task is to analyse the patient's health profile and produce a precise nutrient prescription.
You MUST respond with ONLY a valid JSON object — no explanation, no markdown fences.
Base your recommendations on Indian dietary norms (ICMR-NIN 2024 guidelines).
Do NOT recommend or prescribe any medications."""


def build_nutrient_prompt(
    *,
    health_summary: dict,
    baseline_nutrients: dict,
    icmr_context: list[str],
) -> str:
    context_text = "\n---\n".join(icmr_context) if icmr_context else "No context retrieved."

    return f"""
### Patient Health Summary
{health_summary}

### Baseline Nutrient Estimate (Mifflin-St Jeor)
{baseline_nutrients}

### Relevant ICMR-NIN 2024 Guideline Passages
{context_text}

### Task
Using the above information:
1. Refine the daily nutrient targets (calories, macros, fibre, water, vitamins, minerals, electrolytes, omega fats, and glycemic targets).
2. Add disease-specific adjustments not already captured.
3. Flag medication-food interactions.
4. Cite the ICMR-NIN passages that informed your adjustments.

Respond with ONLY this JSON schema (no extra keys):
{{
  "daily_targets": {{
    "calories": <number>,
    "protein_g": <number>,
    "carbs_g": <number>,
    "fat_g": <number>,
    "fiber_g": <number>,
    "water_ml": <number>,
    "sodium_mg": <number|null>,
    "potassium_mg": <number|null>,
    "iron_mg": <number|null>,
    "calcium_mg": <number|null>,
    "vitamin_d_iu": <number|null>,
    "b12_mcg": <number|null>,
    "vitamin_a_mcg": <number|null>,
    "vitamin_b1_mg": <number|null>,
    "vitamin_b2_mg": <number|null>,
    "vitamin_b3_mg": <number|null>,
    "vitamin_b5_mg": <number|null>,
    "vitamin_b6_mg": <number|null>,
    "vitamin_b7_mcg": <number|null>,
    "vitamin_b9_mcg": <number|null>,
    "vitamin_b12_mcg": <number|null>,
    "vitamin_c_mg": <number|null>,
    "vitamin_e_mg": <number|null>,
    "vitamin_k_mcg": <number|null>,
    "magnesium_mg": <number|null>,
    "zinc_mg": <number|null>,
    "selenium_mcg": <number|null>,
    "copper_mg": <number|null>,
    "phosphorus_mg": <number|null>,
    "iodine_mcg": <number|null>,
    "chloride_mg": <number|null>,
    "manganese_mg": <number|null>,
    "chromium_mcg": <number|null>,
    "molybdenum_mcg": <number|null>,
    "choline_mg": <number|null>,
    "omega_3_g": <number|null>,
    "omega_6_g": <number|null>,
    "glycemic_load": <number|null>,
    "glycemic_index": <number|null>
  }},
  "disease_notes": ["<string>"],
  "medication_interactions": ["<string>"],
  "icmr_references": ["<quoted guideline snippet>"]
}}
"""
