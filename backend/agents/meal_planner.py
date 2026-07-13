"""
agents/meal_planner.py
Generates a personalized 7-day meal plan with the configured LLM.
"""
from __future__ import annotations

import asyncio
import re

from loguru import logger

from backend.models.request_models import HealthProfile, PreferenceProfile
from backend.models.response_models import MealPlanResponse
from backend.prompts.meal_prompt import MEAL_SYSTEM, build_single_day_prompt, build_week_prompt
from backend.rag.retriever import retrieve
from backend.services import llm_service
from backend.services.health_warning_service import medication_warnings
from backend.services.personalization_service import score_meal
from backend.services.food_price_service import (
    budget_limit,
    calculate_meal_affordability,
    estimate_meal_cost,
    food_price_context,
    normalize_ingredient_for_budget,
)
from backend.services.youtube_service import get_recipe_url

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
MEAL_KEYS = ("breakfast", "mid_morning_snack", "lunch", "evening_snack", "dinner")


class MealPlannerAgent:
    """Generate a fully LLM-driven week, one day at a time to prevent truncation."""

    async def generate(
        self,
        health_profile: HealthProfile,
        preference_profile: PreferenceProfile,
        daily_targets: dict,
    ) -> MealPlanResponse:
        logger.info("MealPlannerAgent: generating personalized week with configured meal-plan LLM")
        icmr_context = self._retrieve_context(preference_profile)
        used_meals: list[str] = []
        groceries: dict[str, str] = {}
        pantry = {item.strip().lower() for item in preference_profile.pantry_ingredients}
        provider, _ = llm_service.get_task_model("meal_plan")
        if provider == "biomistral":
            generated_days = []
            for day_number, day_name in enumerate(DAYS, start=1):
                generated_days.append(await self._generate_day(
                    day_name=day_name,
                    day_number=day_number,
                    daily_targets=daily_targets,
                    health_profile=health_profile,
                    preference_profile=preference_profile,
                    icmr_context=icmr_context,
                    used_meals=used_meals,
                ))
        else:
            async def generate_day_with_fallback(day_number: int, day_name: str) -> dict:
                try:
                    return await self._generate_day(
                        day_name=day_name,
                        day_number=day_number,
                        daily_targets=daily_targets,
                        health_profile=health_profile,
                        preference_profile=preference_profile,
                        icmr_context=icmr_context,
                        used_meals=used_meals,
                    )
                except Exception as exc:
                    logger.warning(f"LLM day generation failed for {day_name} ({exc}); using deterministic fallback.")
                    fallback_week = self._fallback_week(daily_targets, preference_profile)
                    return next(d for d in fallback_week if d["day"] == day_name)
                    
            tasks = [
                generate_day_with_fallback(day_number, day_name)
                for day_number, day_name in enumerate(DAYS, start=1)
            ]
            generated_days = await asyncio.gather(*tasks)

        week: list[dict] = []
        for day_plan in generated_days:
            for meal_key in MEAL_KEYS:
                meal = day_plan[meal_key]
                used_meals.append(meal["name"])
                meal["recommendation_score"] = score_meal(
                    meal, {"liked_meals": [], "disliked_meals": []}, daily_targets
                )
                for ingredient in meal["ingredients"]:
                    clean = ingredient.strip()
                    if clean and clean.lower() not in pantry:
                        groceries.setdefault(clean.lower(), "as needed")
            urls = await asyncio.gather(*[
                get_recipe_url(day_plan[key]["name"], preference_profile.regional_cuisine)
                for key in MEAL_KEYS
            ])
            for meal_key, url in zip(MEAL_KEYS, urls):
                day_plan[meal_key]["youtube_url"] = url
            for item in day_plan.pop("grocery_recommendations", []):
                ingredient = item["ingredient"].strip()
                if ingredient:
                    groceries.setdefault(ingredient.lower(), item["quantity"])
            week.append(day_plan)

        return MealPlanResponse(week=week, weekly_grocery_list=groceries)

    def _fallback_week(self, daily_targets: dict, preferences: PreferenceProfile) -> list[dict]:
        """Build a safe template week when the hosted LLM is rate-limited or unavailable."""
        vegetarian = preferences.dietary_preference.value in {"vegetarian", "vegan"}
        eggetarian = preferences.dietary_preference.value == "eggetarian"
        regional = preferences.regional_cuisine.lower()
        if "south" in regional or "tamil" in regional or "kerala" in regional:
            base_days = [
                ("Vegetable oats upma", "Sambar rice with cucumber salad", "Ragi dosa with chutney"),
                ("Idli with sambar", "Curd rice with beans poriyal", "Vegetable pongal"),
                ("Ragi porridge with nuts", "Lemon millet rice with dal", "Adai dosa with avial"),
                ("Poha with peanuts", "Brown rice rasam with cabbage poriyal", "Vegetable uttapam"),
                ("Dosa with sambar", "Millet khichdi with curd", "Tomato rice with sprouts salad"),
                ("Vegetable semiya upma", "Rice, dal, and mixed vegetable kootu", "Ragi idli with sambar"),
                ("Pesarattu with chutney", "Curd millet bowl with vegetables", "Vegetable stew with appam"),
            ]
        else:
            base_days = [
                ("Vegetable dalia", "Rajma brown rice with salad", "Phulka with mixed veg and dal"),
                ("Besan chilla with curd", "Chole with millet roti", "Moong dal khichdi with salad"),
                ("Poha with peanuts", "Dal, rice, and bhindi sabzi", "Paneer bhurji with phulka"),
                ("Oats porridge with nuts", "Kadhi with rice and kachumber", "Vegetable pulao with raita"),
                ("Sprouts chaat with toast", "Soya matar curry with roti", "Dal tadka with lauki sabzi"),
                ("Stuffed vegetable paratha with curd", "Sambar millet bowl", "Chana dal with rice"),
                ("Moong dal cheela", "Vegetable khichdi with curd", "Palak dal with phulka"),
            ]
        if not vegetarian and not eggetarian:
            base_days[2] = ("Egg bhurji with roti", "Chicken curry with rice and salad", "Dal with vegetable roti")
            base_days[5] = ("Oats omelette", "Fish curry with rice and salad", "Vegetable dalia")
        elif eggetarian:
            base_days[2] = ("Egg bhurji with roti", base_days[2][1], base_days[2][2])

        return [
            self._fallback_day(day_name, meals, daily_targets, preferences)
            for day_name, meals in zip(DAYS, base_days)
        ]

    def _fallback_day(
        self,
        day_name: str,
        meals: tuple[str, str, str],
        daily_targets: dict,
        preferences: PreferenceProfile,
    ) -> dict:
        calories = float(daily_targets.get("calories") or 1800)
        protein = float(daily_targets.get("protein_g") or 70)
        carbs = float(daily_targets.get("carbs_g") or 230)
        fat = float(daily_targets.get("fat_g") or 55)
        fiber = float(daily_targets.get("fiber_g") or 25)
        water = float(daily_targets.get("water_ml") or 2500)
        specs = {
            "breakfast": (meals[0], 0.25, ["grain or millet", "dal/curd/protein", "seasonal vegetables"]),
            "mid_morning_snack": ("Fruit with roasted chana", 0.10, ["seasonal fruit", "roasted chana"]),
            "lunch": (meals[1], 0.30, ["whole grain or rice", "dal/beans/protein", "salad", "vegetables"]),
            "evening_snack": ("Buttermilk with sprouts chaat", 0.10, ["buttermilk", "sprouts", "lemon", "spices"]),
            "dinner": (meals[2], 0.25, ["whole grain", "dal/protein", "cooked vegetables"]),
        }
        day: dict = {"day": day_name}
        for meal_key, (name, share, ingredients) in specs.items():
            normalized_ingredients = [
                normalize_ingredient_for_budget(item, preferences.budget.value, preferences.dietary_preference.value)
                for item in ingredients
            ]
            estimated_cost = estimate_meal_cost(normalized_ingredients, preferences.regional_cuisine)
            day[meal_key] = {
                "name": name,
                "ingredients": normalized_ingredients,
                "calories": round(calories * share, 1),
                "protein_g": round(protein * share, 1),
                "carbs_g": round(carbs * share, 1),
                "fat_g": round(fat * share, 1),
                "fiber_g": round(fiber * share, 1),
                "preparation_time_minutes": 15 if "snack" in meal_key else 25,
                "difficulty": "easy" if preferences.cooking_skill.value == "beginner" else "moderate",
                "estimated_cost_inr": estimated_cost,
                "affordability_score": calculate_meal_affordability(normalized_ingredients, estimated_cost),
                "recipe_steps": [
                    "Use minimal oil and salt.",
                    "Cook ingredients fresh and pair with vegetables or salad.",
                    "Adjust portions to match hunger and prescribed targets.",
                ],
            }
        day["daily_totals"] = {
            "calories": round(calories, 1),
            "protein_g": round(protein, 1),
            "carbs_g": round(carbs, 1),
            "fat_g": round(fat, 1),
            "fiber_g": round(fiber, 1),
            "water_ml": round(water, 1),
        }
        day["grocery_recommendations"] = []
        return day

    def _retrieve_context(self, preferences: PreferenceProfile) -> list[str]:
        queries = [
            f"{preferences.regional_cuisine} Indian meal pattern",
            f"Indian {preferences.dietary_preference.value} diet recommendations",
            "Indian breakfast lunch dinner snack ICMR guidelines",
        ]
        context: list[str] = []
        for query in queries:
            for item in retrieve(query, k=2):
                context.append(item["text"])
        return list(dict.fromkeys(context))

    async def _generate_day(
        self,
        *,
        day_name: str,
        day_number: int,
        daily_targets: dict,
        health_profile: HealthProfile,
        preference_profile: PreferenceProfile,
        icmr_context: list[str],
        used_meals: list[str],
    ) -> dict:
        prompt = build_single_day_prompt(
            day_name=day_name,
            day_number=day_number,
            daily_targets=daily_targets,
            health_profile=health_profile.model_dump(mode="json"),
            medication_warnings=medication_warnings(health_profile.medications),
            preference_profile=preference_profile.model_dump(mode="json"),
            price_context=food_price_context(
                preference_profile.budget.value, preference_profile.regional_cuisine
            ),
            used_meals=used_meals,
            icmr_context=icmr_context,
        )
        for attempt in range(2):
            result = await llm_service.generate_json(
                prompt, system=MEAL_SYSTEM, task="meal_plan"
            )
            normalized = self._normalize_day(result, day_name, daily_targets, preference_profile)
            try:
                self._validate_constraints(normalized, preference_profile, daily_targets)
                return normalized
            except ValueError as exc:
                if attempt == 1:
                    raise
                prompt += f"\nYour previous JSON violated this constraint: {exc}. Regenerate the day correctly."
        raise ValueError(f"The meal-planning model could not generate a valid plan for {day_name}")

    def _normalize_day(
        self,
        result: dict | list,
        day_name: str,
        daily_targets: dict,
        preferences: PreferenceProfile,
    ) -> dict:
        """Validate LLM JSON and retain only the public response shape."""
        if isinstance(result, list):
            if not result:
                raise ValueError("The meal-planning model returned an empty list")
            result = result[0]
        if not isinstance(result, dict):
            raise ValueError("The meal plan must be a JSON object")
        if all(key in result for key in ("b", "m", "l", "e", "d")):
            result = self._expand_compact_result(result, daily_targets, preferences)

        normalized: dict = {"day": day_name}
        for meal_key in MEAL_KEYS:
            meal = result.get(meal_key)
            if not isinstance(meal, dict):
                raise ValueError(f"The meal-planning model omitted required meal: {meal_key}")
            ingredients = [
                normalize_ingredient_for_budget(
                    str(item).strip(),
                    preferences.budget.value,
                    preferences.dietary_preference.value,
                )
                for item in meal["ingredients"]
                if str(item).strip()
            ]
            estimated_cost = estimate_meal_cost(ingredients, preferences.regional_cuisine)
            normalized[meal_key] = {
                "name": str(meal["name"]).strip(),
                "ingredients": ingredients,
                "calories": float(meal["calories"]),
                "protein_g": float(meal["protein_g"]),
                "carbs_g": float(meal["carbs_g"]),
                "fat_g": float(meal["fat_g"]),
                "fiber_g": float(meal["fiber_g"]),
                "preparation_time_minutes": int(meal["preparation_time_minutes"]),
                "difficulty": str(meal["difficulty"]).strip().lower(),
                "estimated_cost_inr": estimated_cost,
                "affordability_score": calculate_meal_affordability(ingredients, estimated_cost),
                "recipe_steps": [str(step).strip() for step in meal["recipe_steps"] if str(step).strip()],
            }
        totals = result.get("daily_totals")
        if not isinstance(totals, dict):
            raise ValueError("The meal-planning model omitted required daily_totals")
        normalized["daily_totals"] = {
            "calories": float(totals["calories"]),
            "protein_g": float(totals["protein_g"]),
            "carbs_g": float(totals["carbs_g"]),
            "fat_g": float(totals["fat_g"]),
            "fiber_g": float(totals["fiber_g"]),
            "water_ml": float(totals["water_ml"]),
        }
        normalized["grocery_recommendations"] = self._normalize_groceries(
            result.get("grocery_recommendations", [])
        )
        return normalized

    def _expand_compact_result(
        self, result: dict, daily_targets: dict, preferences: PreferenceProfile
    ) -> dict:
        """Expand compact LLM dishes and allocate target-based serving estimates."""
        meal_map = {
            "b": "breakfast",
            "m": "mid_morning_snack",
            "l": "lunch",
            "e": "evening_snack",
            "d": "dinner",
        }
        shares = {
            "breakfast": 0.25,
            "mid_morning_snack": 0.10,
            "lunch": 0.30,
            "evening_snack": 0.10,
            "dinner": 0.25,
        }
        expanded: dict = {}
        for short_key, meal_key in meal_map.items():
            meal = result.get(short_key, {})
            share = shares[meal_key]
            is_snack = "snack" in meal_key
            ingredients = [
                normalize_ingredient_for_budget(
                    str(item).strip(),
                    preferences.budget.value,
                    preferences.dietary_preference.value,
                )
                for item in meal.get("i", [])
                if str(item).strip()
            ]
            estimated_cost = estimate_meal_cost(ingredients, preferences.regional_cuisine)
            expanded[meal_key] = {
                "name": str(meal.get("n", "")).strip(),
                "ingredients": ingredients,
                "calories": round(float(daily_targets.get("calories", 0)) * share, 1),
                "protein_g": round(float(daily_targets.get("protein_g", 0)) * share, 1),
                "carbs_g": round(float(daily_targets.get("carbs_g", 0)) * share, 1),
                "fat_g": round(float(daily_targets.get("fat_g", 0)) * share, 1),
                "fiber_g": round(float(daily_targets.get("fiber_g", 0)) * share, 1),
                "preparation_time_minutes": 10 if is_snack else 25,
                "difficulty": "easy" if preferences.cooking_skill.value == "beginner" else "moderate",
                "estimated_cost_inr": estimated_cost,
                "affordability_score": calculate_meal_affordability(ingredients, estimated_cost),
                "recipe_steps": ["Prepare the listed ingredients and cook to taste."],
            }
        expanded["daily_totals"] = {
            key: float(daily_targets.get(key, 0))
            for key in ("calories", "protein_g", "carbs_g", "fat_g", "fiber_g", "water_ml")
        }
        expanded["grocery_recommendations"] = []
        return expanded

    def _normalize_groceries(self, items: list) -> list[dict[str, str]]:
        if not isinstance(items, list):
            raise ValueError("Meal-plan grocery_recommendations must be a list")
        groceries = []
        for item in items:
            if isinstance(item, dict) and item.get("ingredient") and item.get("quantity"):
                groceries.append({
                    "ingredient": str(item["ingredient"]),
                    "quantity": str(item["quantity"]),
                })
        return groceries

    def _validate_constraints(
        self, day_plan: dict, preferences: PreferenceProfile, daily_targets: dict
    ) -> None:
        """Reject meals that violate explicit user exclusions before returning them."""
        exclusions = [*preferences.allergies, *preferences.dislikes]
        preference = preferences.dietary_preference.value
        if preference in {"vegetarian", "eggetarian", "vegan"}:
            exclusions.extend(["chicken", "fish", "mutton", "lamb", "pork", "beef", "prawn", "shrimp", "meat"])
        if preference in {"vegetarian", "vegan"}:
            exclusions.append("egg")
        if preference == "vegan":
            exclusions.extend(["milk", "curd", "yogurt", "paneer", "ghee", "butter", "cheese", "cream", "dairy"])

        parts: list[str] = []
        for key in MEAL_KEYS:
            parts.extend([day_plan[key]["name"], *day_plan[key]["ingredients"]])
        searchable = " ".join(parts).lower()
        for exclusion in exclusions:
            term = exclusion.strip().lower()
            if term and re.search(rf"\b{re.escape(term)}\b", searchable):
                raise ValueError(f"meal includes excluded ingredient '{term}'")
        for meal_key in MEAL_KEYS:
            if not day_plan[meal_key]["name"] or not day_plan[meal_key]["ingredients"]:
                raise ValueError(f"{meal_key} must include an LLM-generated dish and ingredients")

        daily_cost = sum(float(day_plan[meal_key]["estimated_cost_inr"]) for meal_key in MEAL_KEYS)
        limit = budget_limit(preferences.budget.value)
        if daily_cost > limit:
            raise ValueError(
                f"daily cost INR {daily_cost:g} exceeds {preferences.budget.value} budget cap INR {limit:g}"
            )

        tolerance = 0.20
        for nutrient in ("calories", "protein_g", "carbs_g", "fat_g", "fiber_g"):
            target = float(daily_targets.get(nutrient) or 0)
            actual = float(day_plan["daily_totals"].get(nutrient) or 0)
            if target and abs(actual - target) / target > tolerance:
                raise ValueError(
                    f"{nutrient} total {actual:g} must be within 20% of target {target:g}"
                )
