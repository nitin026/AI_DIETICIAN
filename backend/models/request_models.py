"""
models/request_models.py
Pydantic v2 request schemas for all API endpoints.
"""
from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, model_validator


# ── Enumerations ─────────────────────────────────────────────────────────────

class Gender(str, Enum):
    male = "male"
    female = "female"
    other = "other"


class ActivityLevel(str, Enum):
    sedentary = "sedentary"           # desk job, little exercise
    lightly_active = "lightly_active" # light exercise 1-3 days/week
    moderately_active = "moderately_active"  # moderate 3-5 days/week
    very_active = "very_active"       # hard exercise 6-7 days/week
    extra_active = "extra_active"     # very hard / physical job


class AddictionFrequency(str, Enum):
    never = "never"
    monthly = "monthly"
    weekly = "weekly"
    daily = "daily"


class DietaryPreference(str, Enum):
    vegetarian = "vegetarian"
    eggetarian = "eggetarian"
    non_vegetarian = "non_vegetarian"
    vegan = "vegan"


class CookingSkill(str, Enum):
    beginner = "beginner"
    intermediate = "intermediate"
    advanced = "advanced"


class BudgetPreference(str, Enum):
    low = "low"         # ₹100–₹200 / day
    medium = "medium"   # ₹200–₹400 / day
    high = "high"       # ₹400+ / day


# ── Sub-models ───────────────────────────────────────────────────────────────

class AddictionProfile(BaseModel):
    smoking: AddictionFrequency = AddictionFrequency.never
    alcohol: AddictionFrequency = AddictionFrequency.never
    tobacco: AddictionFrequency = AddictionFrequency.never


class HealthProfile(BaseModel):
    age: int = Field(..., ge=5, le=120, description="Age in years")
    gender: Gender
    height_cm: float = Field(..., ge=50, le=250, description="Height in centimetres")
    weight_kg: float = Field(..., ge=10, le=300, description="Weight in kilograms")
    occupation: str = Field(..., min_length=2, max_length=100)
    activity_level: ActivityLevel
    diseases: List[str] = Field(default_factory=list, description="e.g. ['type-2 diabetes','hypertension']")
    medications: List[str] = Field(default_factory=list, description="e.g. ['metformin 500mg']")
    addictions: AddictionProfile = Field(default_factory=AddictionProfile)

    @model_validator(mode="after")
    def bmi_sanity(self) -> "HealthProfile":
        bmi = self.weight_kg / ((self.height_cm / 100) ** 2)
        if bmi < 10 or bmi > 80:
            raise ValueError(f"Computed BMI {bmi:.1f} is physiologically implausible.")
        return self


class PreferenceProfile(BaseModel):
    likes: List[str] = Field(default_factory=list)
    dislikes: List[str] = Field(default_factory=list)
    dietary_preference: DietaryPreference = DietaryPreference.vegetarian
    allergies: List[str] = Field(default_factory=list)
    pantry_ingredients: List[str] = Field(default_factory=list)
    budget: BudgetPreference = BudgetPreference.medium
    cooking_skill: CookingSkill = CookingSkill.intermediate
    regional_cuisine: str = Field(default="North Indian", description="e.g. 'South Indian', 'Bengali'")


# ── Endpoint request bodies ───────────────────────────────────────────────────

class NutrientPredictionRequest(BaseModel):
    health_profile: HealthProfile


class MealPlanRequest(BaseModel):
    health_profile: HealthProfile
    preference_profile: PreferenceProfile
    daily_targets: Optional[dict] = None  # pre-computed; if None, will be computed


class IngredientValidationRequest(BaseModel):
    meal_plan: dict = Field(..., description="Raw 7-day meal plan JSON from /generate-meal-plan")
    pantry_ingredients: List[str]


class GroceryListRequest(BaseModel):
    meal_plan: dict
    pantry_ingredients: List[str]
