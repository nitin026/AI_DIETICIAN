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
    vitamin_a_mcg: Optional[float] = None
    vitamin_b1_mg: Optional[float] = None
    vitamin_b2_mg: Optional[float] = None
    vitamin_b3_mg: Optional[float] = None
    vitamin_b5_mg: Optional[float] = None
    vitamin_b6_mg: Optional[float] = None
    vitamin_b7_mcg: Optional[float] = None
    vitamin_b9_mcg: Optional[float] = None
    vitamin_b12_mcg: Optional[float] = None
    vitamin_c_mg: Optional[float] = None
    vitamin_e_mg: Optional[float] = None
    vitamin_k_mcg: Optional[float] = None
    magnesium_mg: Optional[float] = None
    zinc_mg: Optional[float] = None
    selenium_mcg: Optional[float] = None
    copper_mg: Optional[float] = None
    phosphorus_mg: Optional[float] = None
    iodine_mcg: Optional[float] = None
    chloride_mg: Optional[float] = None
    manganese_mg: Optional[float] = None
    chromium_mcg: Optional[float] = None
    molybdenum_mcg: Optional[float] = None
    choline_mg: Optional[float] = None
    omega_3_g: Optional[float] = None
    omega_6_g: Optional[float] = None
    glycemic_load: Optional[float] = None
    glycemic_index: Optional[float] = None

class NutrientPredictionResponse(BaseModel):
    bmr: float
    tdee: float
    daily_targets: DailyTargets
    disease_notes: List[str] = Field(default_factory=list)
    medication_interactions: List[str] = Field(default_factory=list)
    icmr_references: List[str] = Field(default_factory=list)
    nutrient_adequacy: dict = Field(default_factory=dict)
    deficiency_risks: List[str] = Field(default_factory=list)
    food_suggestions: dict = Field(default_factory=dict)
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
    fiber_g: float
    preparation_time_minutes: int = Field(..., ge=0)
    difficulty: str
    estimated_cost_inr: float = Field(..., ge=0)
    recipe_steps: List[str] = Field(default_factory=list)
    youtube_url: Optional[str] = None
    recommendation_score: Optional[float] = None
    affordability_score: Optional[float] = None


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



class VisualMealAnalysis(BaseModel):
    dish_name: str
    estimated_calories: float
    protein_g: float
    carbs_g: float
    fat_g: float
    confidence_score: float
    nutrition_assessment: str


class ChatResponse(BaseModel):
    user_id: str
    message_id: str
    answer: str
    warnings: List[str] = Field(default_factory=list)
    suggested_actions: List[str] = Field(default_factory=list)
    detected_language: str = "en"
    english_message: Optional[str] = None
    disclaimer: str = (
        "This AI nutrition assistant is informational and is not a substitute for medical care."
    )


class FeedbackResponse(BaseModel):
    saved: bool
    feedback: dict
    preference_memory: dict = Field(default_factory=dict)


class AdherenceResponse(BaseModel):
    saved: bool
    log: dict
    summary: dict = Field(default_factory=dict)


class AnalyticsResponse(BaseModel):
    user_id: str
    nutrient_adequacy: dict = Field(default_factory=dict)
    adherence: dict = Field(default_factory=dict)
    preference_memory: dict = Field(default_factory=dict)
    health_score: float = 0
    predicted_adherence_risk: str = "unknown"
    insights: List[str] = Field(default_factory=list)
