"""
agents/ingredient_validator.py
Compares meal ingredients against the pantry and triggers substitutions / grocery alerts.
"""
from __future__ import annotations

from loguru import logger

from backend.models.response_models import IngredientValidationResponse, SubstitutionAlert
from backend.prompts.substitution_prompt import build_substitution_prompt, SUBSTITUTION_SYSTEM
from backend.services import llm_service


class IngredientValidatorAgent:
    """
    Responsibilities:
    - Scan each meal's ingredient list against the pantry
    - For missing ingredients: call BioMistral for a substitution
    - Collect grocery alerts when substitutions fail
    - Return a validated meal plan with substitutions applied
    """

    async def validate(
        self,
        meal_plan: dict,
        pantry: list[str],
        nutrient_targets: dict,
    ) -> IngredientValidationResponse:
        logger.info("IngredientValidatorAgent: validating ingredients against pantry of {} items", len(pantry))
        pantry_lower = {p.strip().lower() for p in pantry}
        substitutions: list[SubstitutionAlert] = []
        grocery_additions: list[str] = []

        for day_plan in meal_plan.get("week", []):
            for meal_key in ("breakfast", "mid_morning_snack", "lunch", "evening_snack", "dinner"):
                meal = day_plan.get(meal_key, {})
                updated_ingredients = []
                for ingredient in meal.get("ingredients", []):
                    if ingredient.strip().lower() in pantry_lower:
                        updated_ingredients.append(ingredient)
                        continue

                    # Attempt substitution via LLM
                    sub = await self._get_substitution(ingredient, meal, pantry, nutrient_targets)
                    substitutions.append(sub)

                    if sub.substitute:
                        updated_ingredients.append(sub.substitute)
                        logger.debug("Substituted '{}' → '{}'", ingredient, sub.substitute)
                    else:
                        updated_ingredients.append(ingredient)  # keep original; flag for grocery
                        if ingredient not in grocery_additions:
                            grocery_additions.append(ingredient)

                meal["ingredients"] = updated_ingredients

        return IngredientValidationResponse(
            validated_meal_plan=meal_plan,
            substitutions=substitutions,
            grocery_additions=grocery_additions,
        )

    async def _get_substitution(
        self,
        missing: str,
        meal: dict,
        pantry: list[str],
        nutrient_targets: dict,
    ) -> SubstitutionAlert:
        prompt = build_substitution_prompt(
            missing_ingredient=missing,
            meal_context=meal,
            pantry=pantry,
            nutrient_targets=nutrient_targets,
        )
        try:
            result = await llm_service.generate_json(prompt, system=SUBSTITUTION_SYSTEM)
            return SubstitutionAlert(**result)
        except Exception as exc:
            logger.warning("Substitution LLM call failed for '{}': {}", missing, exc)
            return SubstitutionAlert(
                original_ingredient=missing,
                substitute=None,
                grocery_alert=True,
                note="LLM unavailable; please add to grocery list.",
            )
