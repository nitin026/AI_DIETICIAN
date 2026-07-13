"""Prompt builder for fully personalized LLM meal planning."""
from __future__ import annotations

import json

MEAL_SYSTEM = """You are an expert Indian dietitian and culinary planner.
Return only one valid compact JSON object. Never use markdown or explanatory text.
Create authentic personalized meals from the supplied user data. Do not use a fixed menu.
Strictly exclude allergens, disliked foods, and foods incompatible with the dietary preference.
Prefer the requested Indian regional cuisine and pantry ingredients where practical."""


def build_single_day_prompt(
    *,
    day_name: str,
    day_number: int,
    daily_targets: dict,
    health_profile: dict,
    medication_warnings: list[str],
    preference_profile: dict,
    price_context: dict,
    used_meals: list[str],
    icmr_context: list[str],
) -> str:
    return f"""Generate day {day_number} of 7: {day_name}.

USER HEALTH PROFILE:
{json.dumps(health_profile, ensure_ascii=True)}

PREFERENCES AND PANTRY:
{json.dumps(preference_profile, ensure_ascii=True)}

NUTRIENT ANALYSIS TARGETS:
{json.dumps(daily_targets, ensure_ascii=True)}

COST, AFFORDABILITY AND BUDGET CONSTRAINTS:
{json.dumps(price_context, ensure_ascii=True)}

MEDICATION AND FOOD CAUTIONS:
{json.dumps(medication_warnings, ensure_ascii=True)}

MEALS ALREADY USED THIS WEEK - DO NOT REPEAT:
{json.dumps(used_meals, ensure_ascii=True)}

ICMR-NIN CONTEXT:
{json.dumps(icmr_context, ensure_ascii=True)}

Generate breakfast, mid_morning_snack, lunch, evening_snack, and dinner.
Use the dietary preference exactly: vegetarian excludes meat, fish and eggs; vegan also excludes dairy;
eggetarian permits eggs but excludes meat and fish; non_vegetarian permits animal foods.
Use the requested regional Indian cuisine even when it is not a common preset. Favor pantry items,
stay within the requested budget, match the cooking skill, and keep each day close to nutrient targets.
Budget is strict: use the supplied daily_budget_limit_inr as a hard cap for total estimated daily food cost.
Optimize nutrient fulfillment under that cap: minimize calorie, protein, fat, carb, fiber, and micronutrient gaps.
For low budget, prioritize the highest-affordability foods and avoid premium foods.
For medium budget, mix economical staples with moderate variety.
For high budget, include more diverse and premium foods while still meeting nutrition targets.
Use distinct dishes throughout the week. Keep the JSON compact: use 3-5 short ingredients per meal.
The backend will calculate portions, nutrients, time, cost and grocery quantities.

Return only this compact JSON shape. Populate all five meal objects.
Every `n` value must be a specific authentic dish name, never `breakfast`, `snack`, `lunch`, or `dinner`:
{{
  "b":{{"n":"breakfast dish","i":["ingredient"]}},
  "m":{{"n":"mid-morning snack","i":["ingredient"]}},
  "l":{{"n":"lunch dish","i":["ingredient"]}},
  "e":{{"n":"evening snack","i":["ingredient"]}},
  "d":{{"n":"dinner dish","i":["ingredient"]}}
}}"""


def build_week_prompt(
    *,
    daily_targets: dict,
    health_profile: dict,
    medication_warnings: list[str],
    preference_profile: dict,
    price_context: dict,
    icmr_context: list[str],
) -> str:
    return f"""Generate a personalized 7-day Indian meal plan.

USER HEALTH PROFILE:
{json.dumps(health_profile, ensure_ascii=True)}

PREFERENCES AND PANTRY:
{json.dumps(preference_profile, ensure_ascii=True)}

DAILY NUTRIENT ANALYSIS TARGETS:
{json.dumps(daily_targets, ensure_ascii=True)}

COST, AFFORDABILITY AND BUDGET CONSTRAINTS:
{json.dumps(price_context, ensure_ascii=True)}

MEDICATION AND FOOD CAUTIONS:
{json.dumps(medication_warnings, ensure_ascii=True)}

ICMR-NIN CONTEXT:
{json.dumps(icmr_context, ensure_ascii=True)}

Generate exactly seven distinct days: Monday through Sunday.
Each day needs breakfast, mid-morning snack, lunch, evening snack, and dinner.
Use specific authentic dish names, not generic labels. Avoid repeating dishes.
Strictly exclude allergies, dislikes, and foods incompatible with the dietary preference.
Use the requested regional Indian cuisine, pantry ingredients, cooking skill, and budget.
Budget is strict: keep each day's total estimated food cost within daily_budget_limit_inr.
Optimize nutrient fulfillment under that cap: minimize calorie, protein, fat, carb, fiber, and micronutrient gaps.
For low budget, build around high-affordability staples such as dals, eggs when allowed, soy chunks,
rice, atta, peanuts, curd, and seasonal vegetables. Avoid premium items.
For medium budget, add moderate variety without relying on premium foods every day.
For high budget, allow premium and diverse options such as paneer, tofu, chicken/fish when allowed,
nuts, and varied fruits.
The backend calculates portions, nutrients, prep time, cost, and grocery quantities.
Return only compact valid JSON in this exact shape:
{{
  "week":[
    {{
      "day":"Monday",
      "b":{{"n":"specific breakfast dish","i":["ingredient"]}},
      "m":{{"n":"specific mid-morning snack","i":["ingredient"]}},
      "l":{{"n":"specific lunch dish","i":["ingredient"]}},
      "e":{{"n":"specific evening snack","i":["ingredient"]}},
      "d":{{"n":"specific dinner dish","i":["ingredient"]}}
    }}
  ]
}}"""
