"""
prompts/substitution_prompt.py
Prompt builder for the Ingredient Validator Agent.
"""
from __future__ import annotations

import json


SUBSTITUTION_SYSTEM = """You are a culinary nutrition expert specialising in Indian cuisine.
When a meal ingredient is unavailable, suggest the best nutritional substitute from the pantry
or flag it for grocery shopping. Always preserve the dish's nutrient balance.
Respond with ONLY valid JSON."""


def build_substitution_prompt(
    *,
    missing_ingredient: str,
    meal_context: dict,
    pantry: list[str],
    nutrient_targets: dict,
) -> str:
    pantry_str = ", ".join(pantry) if pantry else "empty pantry"
    return f"""
### Missing Ingredient
"{missing_ingredient}"

### Meal Context
{json.dumps(meal_context, indent=2)}

### Available Pantry
{pantry_str}

### Nutrient Targets to Preserve
{json.dumps(nutrient_targets, indent=2)}

### Task
1. Suggest the best pantry-available substitute for "{missing_ingredient}".
2. If no suitable substitute exists, set substitute to null and grocery_alert to true.
3. Explain the nutritional impact briefly.

Respond with ONLY:
{{
  "original_ingredient": "{missing_ingredient}",
  "substitute": "<str or null>",
  "grocery_alert": <true|false>,
  "note": "<brief explanation>"
}}
"""
