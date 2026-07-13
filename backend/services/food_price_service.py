"""Commodity price and affordability helpers for meal planning.

The seed catalog uses approximate Indian urban retail prices in INR. Keep this
module as the single place to refresh prices from a market feed or database.
"""
from __future__ import annotations

import json
import os
import re
import time
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen
from typing import Iterable


@dataclass(frozen=True)
class FoodPrice:
    name: str
    aliases: tuple[str, ...]
    category: str
    price_per_kg: float
    calories_per_100g: float
    protein_per_100g: float
    fiber_per_100g: float
    tier: str = "medium"
    default_serving_g: float = 100
    regional_multiplier: dict[str, float] | None = None

    @property
    def nutrient_density(self) -> float:
        return self.protein_per_100g * 4 + self.fiber_per_100g * 2 + self.calories_per_100g / 100

    @property
    def affordability_score(self) -> float:
        price_per_100g = self.price_per_kg / 10
        return round(self.nutrient_density / price_per_100g, 3) if price_per_100g else 0


FOOD_PRICE_CATALOG: tuple[FoodPrice, ...] = (
    FoodPrice("rice", ("rice", "chawal"), "Grains", 55, 345, 7, 1, "low", 75, {"south": 0.95, "bengal": 0.95, "east": 0.95}),
    FoodPrice("atta", ("atta", "wheat", "roti", "chapati", "phulka"), "Grains", 45, 340, 12, 11, "low", 60, {"north": 0.95, "punjabi": 0.95}),
    FoodPrice("poha", ("poha", "flattened rice"), "Grains", 70, 350, 7, 2, "low", 60),
    FoodPrice("oats", ("oats",), "Grains", 160, 389, 17, 10, "medium", 50),
    FoodPrice("ragi", ("ragi", "finger millet"), "Grains", 70, 336, 7, 11, "low", 60),
    FoodPrice("moong dal", ("moong dal", "green gram"), "Protein", 125, 347, 24, 16, "low", 60),
    FoodPrice("masoor dal", ("masoor", "red lentil"), "Protein", 110, 352, 25, 11, "low", 60),
    FoodPrice("chana dal", ("chana dal", "bengal gram"), "Protein", 95, 360, 20, 11, "low", 60),
    FoodPrice("toor dal", ("toor", "arhar"), "Protein", 165, 335, 22, 15, "medium", 60),
    FoodPrice("rajma", ("rajma", "kidney bean"), "Protein", 140, 333, 24, 25, "medium", 60),
    FoodPrice("chickpea", ("chickpea", "chana", "chole"), "Protein", 110, 364, 19, 17, "low", 60),
    FoodPrice("soy chunks", ("soy chunk", "soya chunk", "soybean", "soya"), "Protein", 150, 345, 52, 13, "low", 40),
    FoodPrice("egg", ("egg", "anda"), "Protein", 120, 155, 13, 0, "low", 100),
    FoodPrice("curd", ("curd", "yogurt", "dahi"), "Dairy", 80, 61, 3.5, 0, "low", 150),
    FoodPrice("milk", ("milk", "doodh"), "Dairy", 70, 67, 3.2, 0, "low", 200),
    FoodPrice("paneer", ("paneer",), "Protein", 420, 265, 18, 0, "high", 75),
    FoodPrice("tofu", ("tofu",), "Protein", 260, 76, 8, 1, "medium", 100),
    FoodPrice("chicken", ("chicken",), "Protein", 260, 239, 27, 0, "high", 120),
    FoodPrice("fish", ("fish", "rohu", "pomfret"), "Protein", 300, 180, 22, 0, "high", 120, {"bengal": 0.9, "coastal": 0.9, "kerala": 0.9}),
    FoodPrice("peanut", ("peanut", "groundnut"), "Nuts & Seeds", 160, 567, 26, 9, "low", 25),
    FoodPrice("almond", ("almond", "badam"), "Nuts & Seeds", 900, 579, 21, 13, "high", 20),
    FoodPrice("vegetables", ("vegetable", "sabzi", "spinach", "palak", "tomato", "onion", "carrot", "cabbage", "cauliflower"), "Vegetables", 50, 35, 2, 3, "low", 150),
    FoodPrice("seasonal fruit", ("banana", "papaya", "guava", "orange", "fruit"), "Fruits", 70, 80, 1, 3, "low", 120),
    FoodPrice("apple", ("apple",), "Fruits", 180, 52, 0.3, 2, "high", 120),
    FoodPrice("oil", ("oil",), "Fats & Oils", 160, 884, 0, 0, "low", 10),
    FoodPrice("ghee", ("ghee", "butter"), "Fats & Oils", 650, 900, 0, 0, "high", 10),
)

PRICE_OVERRIDE_PATH = Path("data/food_prices.json")
GOV_PRICE_CACHE_PATH = Path("data/gov_food_prices_cache.json")
GOV_PRICE_CACHE_TTL_SECONDS = 24 * 60 * 60

BUDGET_LIMITS_INR = {
    "low": 200.0,
    "medium": 400.0,
    "high": 700.0,
}

BUDGET_TIERS = {
    "low": {"low"},
    "medium": {"low", "medium"},
    "high": {"low", "medium", "high"},
}


def budget_limit(budget: str) -> float:
    return BUDGET_LIMITS_INR.get(budget, BUDGET_LIMITS_INR["medium"])


def find_food(ingredient: str) -> FoodPrice | None:
    return _find_food_in_catalog(ingredient, _active_catalog())


def _find_food_in_catalog(ingredient: str, catalog: tuple[FoodPrice, ...]) -> FoodPrice | None:
    text = ingredient.lower()
    for food in catalog:
        if any(re.search(rf"\b{re.escape(alias)}s?\b", text) for alias in food.aliases):
            return food
    return None


def _load_price_overrides() -> tuple[FoodPrice, ...]:
    if not PRICE_OVERRIDE_PATH.exists():
        return ()
    try:
        rows = json.loads(PRICE_OVERRIDE_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return ()
    foods = []
    for row in rows if isinstance(rows, list) else []:
        try:
            foods.append(
                FoodPrice(
                    name=str(row["name"]),
                    aliases=tuple(str(alias) for alias in row.get("aliases", [row["name"]])),
                    category=str(row["category"]),
                    price_per_kg=float(row["price_per_kg"]),
                    calories_per_100g=float(row.get("calories_per_100g", 0)),
                    protein_per_100g=float(row.get("protein_per_100g", 0)),
                    fiber_per_100g=float(row.get("fiber_per_100g", 0)),
                    tier=str(row.get("tier", "medium")),
                    default_serving_g=float(row.get("default_serving_g", 100)),
                    regional_multiplier=row.get("regional_multiplier"),
                )
            )
        except (KeyError, TypeError, ValueError):
            continue
    return tuple(foods)


def _build_data_gov_url() -> str | None:
    explicit_url = os.getenv("GOV_FOOD_PRICE_API_URL")
    if explicit_url:
        return explicit_url

    resource_id = os.getenv("DATA_GOV_FOOD_PRICE_RESOURCE_ID")
    api_key = os.getenv("DATA_GOV_API_KEY")
    if not resource_id or not api_key:
        return None

    params = urlencode({
        "api-key": api_key,
        "format": "json",
        "limit": os.getenv("DATA_GOV_FOOD_PRICE_LIMIT", "5000"),
    })
    return f"https://api.data.gov.in/resource/{resource_id}?{params}"


def _price_per_kg_from_record(record: dict) -> float | None:
    price_fields = (
        "modal_price",
        "Modal Price",
        "modal_price_rs_quintal",
        "price",
        "Price",
        "retail_price",
        "Retail Price",
    )
    raw_price = next((record.get(field) for field in price_fields if record.get(field)), None)
    if raw_price is None:
        return None
    try:
        price = float(str(raw_price).replace(",", "").strip())
    except ValueError:
        return None

    unit_text = " ".join(
        str(record.get(field, ""))
        for field in ("unit", "Unit", "price_unit", "Price Unit", "commodity_unit")
    ).lower()
    if "quintal" in unit_text or price > 1000:
        return round(price / 100, 2)
    if "100g" in unit_text or "100 g" in unit_text:
        return round(price * 10, 2)
    return round(price, 2)


def _record_name(record: dict) -> str | None:
    name_fields = ("commodity", "Commodity", "item", "Item", "food", "Food", "name", "Name")
    return next((str(record[field]).strip().lower() for field in name_fields if record.get(field)), None)


def refresh_government_prices(force: bool = False) -> int:
    """Fetch configured government commodity prices and cache normalized INR/kg rows.

    Configure either GOV_FOOD_PRICE_API_URL or DATA_GOV_FOOD_PRICE_RESOURCE_ID plus
    DATA_GOV_API_KEY. The parser accepts common data.gov.in/Agmarknet-style field
    names and stores only normalized prices used by the meal optimizer.
    """
    if (
        not force
        and GOV_PRICE_CACHE_PATH.exists()
        and time.time() - GOV_PRICE_CACHE_PATH.stat().st_mtime < GOV_PRICE_CACHE_TTL_SECONDS
    ):
        return 0

    url = _build_data_gov_url()
    if not url:
        return 0

    try:
        with urlopen(url, timeout=20) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except Exception:
        return 0

    records = payload.get("records", payload if isinstance(payload, list) else [])
    normalized = []
    for record in records if isinstance(records, list) else []:
        if not isinstance(record, dict):
            continue
        name = _record_name(record)
        price_per_kg = _price_per_kg_from_record(record)
        if not name or not price_per_kg:
            continue
        normalized.append({
            "name": name,
            "aliases": [name],
            "price_per_kg": price_per_kg,
            "source": "government",
            "market": record.get("market") or record.get("Market"),
            "district": record.get("district") or record.get("District"),
            "state": record.get("state") or record.get("State"),
            "fetched_at": int(time.time()),
        })

    if not normalized:
        return 0

    GOV_PRICE_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    GOV_PRICE_CACHE_PATH.write_text(json.dumps(normalized, indent=2), encoding="utf-8")
    return len(normalized)


def _load_government_price_overrides() -> tuple[FoodPrice, ...]:
    if not GOV_PRICE_CACHE_PATH.exists():
        refresh_government_prices()
    if not GOV_PRICE_CACHE_PATH.exists():
        return ()
    try:
        rows = json.loads(GOV_PRICE_CACHE_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return ()

    foods = []
    for row in rows if isinstance(rows, list) else []:
        if not isinstance(row, dict):
            continue
        base = _find_food_in_catalog(str(row.get("name", "")), FOOD_PRICE_CATALOG)
        try:
            foods.append(
                FoodPrice(
                    name=str(row["name"]).lower(),
                    aliases=tuple(str(alias).lower() for alias in row.get("aliases", [row["name"]])),
                    category=base.category if base else "General",
                    price_per_kg=float(row["price_per_kg"]),
                    calories_per_100g=base.calories_per_100g if base else 0,
                    protein_per_100g=base.protein_per_100g if base else 0,
                    fiber_per_100g=base.fiber_per_100g if base else 0,
                    tier=base.tier if base else "medium",
                    default_serving_g=base.default_serving_g if base else 100,
                    regional_multiplier=base.regional_multiplier if base else None,
                )
            )
        except (KeyError, TypeError, ValueError):
            continue
    return tuple(foods)


def _active_catalog() -> tuple[FoodPrice, ...]:
    gov_overrides = _load_government_price_overrides()
    overrides = _load_price_overrides() + gov_overrides
    if not overrides:
        return FOOD_PRICE_CATALOG
    override_names = {food.name for food in overrides}
    base = tuple(food for food in FOOD_PRICE_CATALOG if food.name not in override_names)
    return overrides + base


def _is_diet_compatible(food: FoodPrice, dietary_preference: str) -> bool:
    name = food.name
    if dietary_preference in {"vegetarian", "vegan"} and name in {"egg", "chicken", "fish"}:
        return False
    if dietary_preference == "vegan" and name in {"curd", "milk", "paneer", "ghee"}:
        return False
    return True


def _candidate_substitutes(food: FoodPrice, budget: str, dietary_preference: str) -> Iterable[FoodPrice]:
    allowed_tiers = BUDGET_TIERS.get(budget, BUDGET_TIERS["medium"])
    for candidate in _active_catalog():
        if candidate.name == food.name:
            continue
        if candidate.tier not in allowed_tiers:
            continue
        if not _is_diet_compatible(candidate, dietary_preference):
            continue
        same_category = candidate.category == food.category
        protein_swap = food.category == "Protein" and candidate.category == "Protein"
        fat_swap = food.category == "Fats & Oils" and candidate.category == "Fats & Oils"
        if same_category or protein_swap or fat_swap:
            yield candidate


def find_budget_substitute(
    ingredient: str,
    budget: str,
    dietary_preference: str = "vegetarian",
) -> str:
    food = find_food(ingredient)
    if not food:
        return ingredient
    if food.tier in BUDGET_TIERS.get(budget, BUDGET_TIERS["medium"]) and _is_diet_compatible(
        food, dietary_preference
    ):
        return ingredient

    candidates = list(_candidate_substitutes(food, budget, dietary_preference))
    if not candidates:
        return ingredient

    best = max(
        candidates,
        key=lambda item: (
            item.affordability_score,
            -item.price_per_kg,
            item.protein_per_100g,
        ),
    )
    return best.name


def normalize_ingredient_for_budget(
    ingredient: str,
    budget: str,
    dietary_preference: str = "vegetarian",
) -> str:
    return find_budget_substitute(ingredient, budget, dietary_preference)


def estimate_ingredient_cost(ingredient: str, regional_cuisine: str = "", serving_g: float | None = None) -> float:
    food = find_food(ingredient)
    if not food:
        return 8.0
    multiplier = 1.0
    if food.regional_multiplier:
        region = regional_cuisine.lower()
        multiplier = next((value for key, value in food.regional_multiplier.items() if key in region), 1.0)
    grams = serving_g or food.default_serving_g
    return round((food.price_per_kg / 1000) * grams * multiplier, 2)


def estimate_meal_cost(ingredients: list[str], regional_cuisine: str = "") -> float:
    return round(sum(estimate_ingredient_cost(item, regional_cuisine) for item in ingredients), 2)


def calculate_meal_affordability(ingredients: list[str], meal_cost_inr: float) -> float:
    density = 0.0
    for ingredient in ingredients:
        food = find_food(ingredient)
        density += food.nutrient_density if food else 1.0
    return round(density / meal_cost_inr, 3) if meal_cost_inr > 0 else 0.0


def food_price_context(budget: str, regional_cuisine: str = "") -> dict:
    allowed_tiers = BUDGET_TIERS.get(budget, BUDGET_TIERS["medium"])
    foods = [food for food in _active_catalog() if food.tier in allowed_tiers]
    ranked = sorted(foods, key=lambda item: item.affordability_score, reverse=True)
    return {
        "budget_level": budget,
        "daily_budget_limit_inr": budget_limit(budget),
        "regional_cuisine": regional_cuisine,
        "preferred_foods": [
            {
                "name": food.name,
                "category": food.category,
                "price_per_kg_inr": food.price_per_kg,
                "affordability": food.affordability_score,
            }
            for food in ranked[:12]
        ],
        "premium_foods_allowed": budget == "high",
    }


def category_for_ingredient(ingredient: str) -> str:
    food = find_food(ingredient)
    return food.category if food else "General"
