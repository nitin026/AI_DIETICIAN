"""
agents/grocery_agent.py
Aggregates all meal ingredients, subtracts pantry items, and produces
a categorised, quantity-estimated grocery list.
"""
from __future__ import annotations

from collections import defaultdict

from loguru import logger

from backend.models.response_models import GroceryItem, GroceryListResponse
from backend.services.food_price_service import category_for_ingredient, estimate_ingredient_cost


class GroceryAgent:
    """Aggregates weekly meal ingredients minus pantry to create a grocery list."""

    def generate(
        self,
        meal_plan: dict,
        pantry_ingredients: list[str],
    ) -> GroceryListResponse:
        logger.info("GroceryAgent: building grocery list")
        pantry_lower = {p.strip().lower() for p in pantry_ingredients}

        # Count ingredient occurrences across all meals
        ingredient_counts: dict[str, int] = defaultdict(int)
        for day_plan in meal_plan.get("week", []):
            for meal_key in ("breakfast", "mid_morning_snack", "lunch", "evening_snack", "dinner"):
                meal = day_plan.get(meal_key, {})
                for ingredient in meal.get("ingredients", []):
                    clean = ingredient.strip().lower()
                    if clean and clean not in pantry_lower:
                        ingredient_counts[clean] += 1

        # Also include items from weekly_grocery_list if present
        for ingredient, quantity in meal_plan.get("weekly_grocery_list", {}).items():
            clean = ingredient.strip().lower()
            if clean not in pantry_lower and clean not in ingredient_counts:
                ingredient_counts[clean] = 1

        # Build GroceryItem list
        items: list[GroceryItem] = []
        total_cost = 0.0
        for ingredient, count in sorted(ingredient_counts.items()):
            quantity_str = meal_plan.get("weekly_grocery_list", {}).get(ingredient)
            if not quantity_str:
                quantity_str = f"{count * 100}g" if count <= 7 else "1 kg"

            category = category_for_ingredient(ingredient)
            cost = estimate_ingredient_cost(ingredient)
            total_cost += cost

            items.append(GroceryItem(
                ingredient=ingredient.title(),
                quantity=quantity_str,
                estimated_cost_inr=cost,
                category=category,
            ))

        notes = [
            "Prices use the backend commodity price catalog and standard serving assumptions.",
            "Buy seasonal vegetables and fruits for cost savings.",
            "Prefer whole grains over refined grains per ICMR-NIN guidelines.",
        ]

        return GroceryListResponse(
            items=items,
            total_estimated_cost_inr=round(total_cost, 2),
            notes=notes,
        )
