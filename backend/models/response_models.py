"""
models/response_models.py
Pydantic v2 response schemas – all LLM outputs are validated against these.
"""
from __future__ import annotations

from typing import Dict, List, Optional

from pydantic import BaseModel, Field


# ── Nutrition ─────────────────────────────────────────────────────────────────

class DailyTargets(BaseModel):
    calories: float
    protein_g: float
    carbs_g: float
    fat_g: float
    fiber_g: float
    water_ml: float
    sodium_mg: Optional[float] = None
    potassium_mg: Optional[float] = None
    iron_mg: Optional[float] = None
    calcium_mg: Optional[float] = None
    vitamin_d_iu: Optional[float] = None
    b12_mcg: Optional[float] = None


class NutrientPredictionResponse(BaseModel):
    bmr: float
    tdee: float
    daily_targets: DailyTargets
    disease_notes: List[str] = Field(default_factory=list)
    medication_interactions: List[str] = Field(default_factory=list)
    icmr_references: List[str] = Field(default_factory=list)
    disclaimer: str = (
        "This AI dietitian is an informational assistant and is not a substitute "
        "for professional medical advice, diagnosis, or treatment."
    )


# ── Meal Plan ─────────────────────────────────────────────────────────────────

class Meal(BaseModel):
    name: str
    ingredients: List[str]
    quantity_g: Optional[float] = None
    calories: float
    protein_g: float
    carbs_g: float
    fat_g: float
    recipe_steps: List[str] = Field(default_factory=list)
    youtube_url: Optional[str] = None


class DayPlan(BaseModel):
    day: str                # "Monday", "Tuesday", …
    breakfast: Meal
    mid_morning_snack: Meal
    lunch: Meal
    evening_snack: Meal
    dinner: Meal
    daily_totals: DailyTargets


class MealPlanResponse(BaseModel):
    week: List[DayPlan]
    weekly_grocery_list: Dict[str, str] = Field(
        default_factory=dict,
        description="ingredient → estimated quantity (e.g. 'brown rice' → '1 kg')"
    )
    disclaimer: str = (
        "This AI dietitian is an informational assistant and is not a substitute "
        "for professional medical advice, diagnosis, or treatment."
    )


# ── Ingredient Validation ─────────────────────────────────────────────────────

class SubstitutionAlert(BaseModel):
    original_ingredient: str
    substitute: Optional[str] = None
    grocery_alert: bool = False
    note: str = ""


class IngredientValidationResponse(BaseModel):
    validated_meal_plan: dict
    substitutions: List[SubstitutionAlert] = Field(default_factory=list)
    grocery_additions: List[str] = Field(default_factory=list)


# ── Grocery List ──────────────────────────────────────────────────────────────

class GroceryItem(BaseModel):
    ingredient: str
    quantity: str
    estimated_cost_inr: Optional[float] = None
    category: str = "General"    # Vegetables / Grains / Dairy / Protein / Spices


class GroceryListResponse(BaseModel):
    items: List[GroceryItem]
    total_estimated_cost_inr: Optional[float] = None
    notes: List[str] = Field(default_factory=list)
