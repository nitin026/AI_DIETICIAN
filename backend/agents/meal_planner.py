"""
agents/meal_planner.py
Generates a 7-day meal plan one day at a time to avoid LLM token truncation.
"""
from __future__ import annotations

from loguru import logger

from backend.models.request_models import HealthProfile, PreferenceProfile
from backend.models.response_models import MealPlanResponse
from backend.prompts.meal_prompt import build_single_day_prompt, MEAL_SYSTEM
from backend.rag.retriever import retrieve
from backend.services import llm_service
from backend.services.youtube_service import get_recipe_url

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

FALLBACK_DAY = {
    "breakfast":        {"name": "Oats Porridge", "ingredients": ["oats", "milk", "banana"], "calories": 320, "protein_g": 10, "carbs_g": 55, "fat_g": 7, "recipe_steps": ["Boil milk.", "Add oats and cook 5 mins.", "Top with banana."]},
    "mid_morning_snack":{"name": "Mixed Fruit", "ingredients": ["apple", "orange"], "calories": 120, "protein_g": 1, "carbs_g": 28, "fat_g": 0, "recipe_steps": ["Chop and serve."]},
    "lunch":            {"name": "Dal Rice", "ingredients": ["dal", "rice", "turmeric", "ghee"], "calories": 500, "protein_g": 18, "carbs_g": 85, "fat_g": 8, "recipe_steps": ["Cook dal with turmeric.", "Cook rice.", "Mix and serve with ghee."]},
    "evening_snack":    {"name": "Roasted Chana", "ingredients": ["chana", "lemon", "spices"], "calories": 150, "protein_g": 8, "carbs_g": 22, "fat_g": 3, "recipe_steps": ["Roast chana.", "Add lemon and spices."]},
    "dinner":           {"name": "Vegetable Khichdi", "ingredients": ["rice", "moong dal", "vegetables", "ghee"], "calories": 420, "protein_g": 14, "carbs_g": 70, "fat_g": 7, "recipe_steps": ["Pressure cook rice and dal.", "Add vegetables.", "Season with ghee and spices."]},
    "daily_totals":     {"calories": 1510, "protein_g": 51, "carbs_g": 260, "fat_g": 25, "fiber_g": 18, "water_ml": 2500},
}


class MealPlannerAgent:
    """Generates 7-day plan by calling LLM once per day — avoids JSON truncation."""

    async def generate(
        self,
        health_profile: HealthProfile,
        preference_profile: PreferenceProfile,
        daily_targets: dict,
    ) -> MealPlanResponse:
        logger.info("MealPlannerAgent: generating 7-day plan (1 day per LLM call)")

        # ── RAG retrieval (done once, reused for all days) ────────
        rag_queries = [
            f"{preference_profile.regional_cuisine} Indian meal pattern",
            f"Indian {preference_profile.dietary_preference.value} diet recommendations",
            "Indian breakfast lunch dinner snack ICMR guidelines",
        ]
        icmr_context: list[str] = []
        for q in rag_queries:
            icmr_context.extend(retrieve(q, k=2))
        icmr_context = list(dict.fromkeys(icmr_context))  # deduplicate

        # ── Generate one day at a time ────────────────────────────
        week = []
        used_meals: list[str] = []
        all_ingredients: dict[str, str] = {}

        for day in DAYS:
            logger.info("Generating meal plan for {}", day)
            day_plan = await self._generate_day(
                day=day,
                daily_targets=daily_targets,
                preference_profile=preference_profile,
                icmr_context=icmr_context,
                used_meals=used_meals,
            )

            # Track meal names to avoid repetition
            for meal_key in ("breakfast", "mid_morning_snack", "lunch", "evening_snack", "dinner"):
                meal = day_plan.get(meal_key, {})
                if meal.get("name"):
                    used_meals.append(meal["name"])

                # Collect ingredients for grocery list
                for ing in meal.get("ingredients", []):
                    if ing.strip().lower() not in all_ingredients:
                        all_ingredients[ing.strip().lower()] = "as needed"

            # Add YouTube links
            cuisine = preference_profile.regional_cuisine
            for meal_key in ("breakfast", "mid_morning_snack", "lunch", "evening_snack", "dinner"):
                meal = day_plan.get(meal_key, {})
                if meal.get("name"):
                    meal["youtube_url"] = await get_recipe_url(meal["name"], cuisine)

            week.append(day_plan)

        return MealPlanResponse(
            week=week,
            weekly_grocery_list=all_ingredients,
        )

    async def _generate_day(
        self,
        *,
        day: str,
        daily_targets: dict,
        preference_profile: PreferenceProfile,
        icmr_context: list[str],
        used_meals: list[str],
    ) -> dict:
        """Call LLM for a single day and return parsed dict. Falls back on error."""
        prompt = build_single_day_prompt(
            day_name=day,
            daily_targets=daily_targets,
            preference_profile=preference_profile.model_dump(),
            pantry=preference_profile.pantry_ingredients,
            used_meals=used_meals,
            icmr_context=icmr_context,
        )
        try:
            result = await llm_service.generate_json(prompt, system=MEAL_SYSTEM)
            # Ensure the day key is set
            result["day"] = day
            return result
        except Exception as exc:
            logger.warning("Day '{}' LLM generation failed ({}); using fallback.", day, exc)
            fallback = dict(FALLBACK_DAY)
            fallback["day"] = day
            return fallback