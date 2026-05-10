"""
agents/grocery_agent.py
Aggregates all meal ingredients, subtracts pantry items, and produces
a categorised, quantity-estimated grocery list.
"""
from __future__ import annotations

from collections import defaultdict

from loguru import logger

from backend.models.response_models import GroceryItem, GroceryListResponse

# Rough cost estimates in INR per 100g/ml (2024 prices)
_COST_MAP: dict[str, float] = {
    "rice": 5, "dal": 8, "wheat": 4, "atta": 4, "oats": 15,
    "milk": 6, "curd": 5, "paneer": 35, "eggs": 7, "chicken": 22,
    "fish": 25, "tofu": 20, "vegetables": 5, "fruits": 12,
    "oil": 15, "ghee": 50, "nuts": 60, "seeds": 30, "spices": 10,
}

_CATEGORY_MAP: dict[str, str] = {
    "rice": "Grains", "atta": "Grains", "wheat": "Grains", "oats": "Grains", "poha": "Grains",
    "dal": "Protein", "paneer": "Protein", "eggs": "Protein", "chicken": "Protein",
    "fish": "Protein", "tofu": "Protein", "rajma": "Protein", "chana": "Protein",
    "milk": "Dairy", "curd": "Dairy", "yogurt": "Dairy", "buttermilk": "Dairy",
    "spinach": "Vegetables", "tomato": "Vegetables", "onion": "Vegetables",
    "carrot": "Vegetables", "broccoli": "Vegetables", "cauliflower": "Vegetables",
    "banana": "Fruits", "apple": "Fruits", "orange": "Fruits", "papaya": "Fruits",
    "oil": "Fats & Oils", "ghee": "Fats & Oils", "nuts": "Nuts & Seeds", "seeds": "Nuts & Seeds",
}


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

            # Category lookup
            category = next(
                (cat for key, cat in _CATEGORY_MAP.items() if key in ingredient),
                "General",
            )
            # Rough cost
            cost_per_100 = next(
                (c for key, c in _COST_MAP.items() if key in ingredient),
                8.0,
            )
            try:
                qty_num = float("".join(filter(str.isdigit, quantity_str.replace(".", ""))) or "200")
                cost = round((qty_num / 100) * cost_per_100, 2)
            except Exception:
                cost = 0.0
            total_cost += cost

            items.append(GroceryItem(
                ingredient=ingredient.title(),
                quantity=quantity_str,
                estimated_cost_inr=cost,
                category=category,
            ))

        notes = [
            "Prices are approximate (2024 retail rates).",
            "Buy seasonal vegetables and fruits for cost savings.",
            "Prefer whole grains over refined grains per ICMR-NIN guidelines.",
        ]

        return GroceryListResponse(
            items=items,
            total_estimated_cost_inr=round(total_cost, 2),
            notes=notes,
        )
