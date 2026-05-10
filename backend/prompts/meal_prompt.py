"""
prompts/meal_prompt.py
Prompt builder for the Dynamic Meal Planner Agent.
Generates meal plan one day at a time to avoid token truncation.
"""
from __future__ import annotations
import json

MEAL_SYSTEM = """You are an expert Indian dietitian and culinary specialist.
Generate a structured Indian meal plan for ONE day that:
- Meets the patient's daily nutrient targets
- Respects dietary preferences, allergies, and dislikes
- Uses available pantry ingredients where possible
- Follows ICMR-NIN 2024 guidelines for Indian meal patterns
- Uses authentic Indian regional recipes
Respond with ONLY valid JSON for that single day. No explanations, no markdown fences."""


def build_single_day_prompt(
    *,
    day_name: str,
    daily_targets: dict,
    preference_profile: dict,
    pantry: list[str],
    used_meals: list[str],
    icmr_context: list[str],
) -> str:
    context_text = "\n---\n".join(icmr_context) if icmr_context else ""
    pantry_str = ", ".join(pantry) if pantry else "Not specified"
    used_str = ", ".join(used_meals) if used_meals else "None yet"

    return f"""
### Day: {day_name}

### Daily Nutrient Targets
{json.dumps(daily_targets, indent=2)}

### Patient Preferences
- Dietary Type: {preference_profile.get('dietary_preference')}
- Likes: {preference_profile.get('likes', [])}
- Dislikes: {preference_profile.get('dislikes', [])}
- Allergies: {preference_profile.get('allergies', [])}
- Regional Cuisine: {preference_profile.get('regional_cuisine', 'North Indian')}
- Cooking Skill: {preference_profile.get('cooking_skill', 'intermediate')}
- Budget: {preference_profile.get('budget', 'medium')}

### Available Pantry
{pantry_str}

### Already Used Meals This Week (DO NOT REPEAT)
{used_str}

### ICMR-NIN Context
{context_text}

### Task
Generate the meal plan for {day_name} only.
Include: breakfast, mid_morning_snack, lunch, evening_snack, dinner.
Each meal must have: name, ingredients (list), calories, protein_g, carbs_g, fat_g, recipe_steps (3-4 steps max).

Respond with ONLY this JSON (no markdown, no extra text):
{{
  "day": "{day_name}",
  "breakfast": {{
    "name": "<str>",
    "ingredients": ["<str>"],
    "calories": <num>,
    "protein_g": <num>,
    "carbs_g": <num>,
    "fat_g": <num>,
    "recipe_steps": ["<str>"]
  }},
  "mid_morning_snack": {{
    "name": "<str>",
    "ingredients": ["<str>"],
    "calories": <num>,
    "protein_g": <num>,
    "carbs_g": <num>,
    "fat_g": <num>,
    "recipe_steps": ["<str>"]
  }},
  "lunch": {{
    "name": "<str>",
    "ingredients": ["<str>"],
    "calories": <num>,
    "protein_g": <num>,
    "carbs_g": <num>,
    "fat_g": <num>,
    "recipe_steps": ["<str>"]
  }},
  "evening_snack": {{
    "name": "<str>",
    "ingredients": ["<str>"],
    "calories": <num>,
    "protein_g": <num>,
    "carbs_g": <num>,
    "fat_g": <num>,
    "recipe_steps": ["<str>"]
  }},
  "dinner": {{
    "name": "<str>",
    "ingredients": ["<str>"],
    "calories": <num>,
    "protein_g": <num>,
    "carbs_g": <num>,
    "fat_g": <num>,
    "recipe_steps": ["<str>"]
  }},
  "daily_totals": {{
    "calories": <num>,
    "protein_g": <num>,
    "carbs_g": <num>,
    "fat_g": <num>,
    "fiber_g": <num>,
    "water_ml": <num>
  }}
}}
"""