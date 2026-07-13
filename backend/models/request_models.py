"""
models/request_models.py
Pydantic v2 request schemas for all API endpoints.
"""
from __future__ import annotations

from enum import Enum
from typing import Any, Literal, List, Optional

from pydantic import BaseModel, Field, model_validator


# â”€â”€ Enumerations â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

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
    low = "low"         # â‚¹100â€“â‚¹200 / day
    medium = "medium"   # â‚¹200â€“â‚¹400 / day
    high = "high"       # â‚¹400+ / day


# â”€â”€ Sub-models â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

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
    bmr_equation: Literal["mifflin_st_jeor", "icmr_nin_who_fao_unu"] = "mifflin_st_jeor"

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


# â”€â”€ Endpoint request bodies â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

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
class UserContextPayload(BaseModel):
    user_id: str = "demo-user"
    health_profile: Optional[HealthProfile] = None
    preference_profile: Optional[PreferenceProfile] = None
    daily_targets: Optional[dict[str, Any]] = None
    meal_plan: Optional[dict[str, Any]] = None
    grocery_list: Optional[dict[str, Any]] = None


class ChatRequest(UserContextPayload):
    message: str = Field(..., min_length=1, max_length=2000)
    preferred_language: Optional[str] = Field(default=None, description="Optional BCP-47 language code, e.g. hi, bn, ta")
    stream: bool = True


class MealFeedbackRequest(BaseModel):
    user_id: str = "demo-user"
    date: str
    day: str
    meal_type: str
    meal_name: str
    rating: int = Field(..., ge=1, le=5)
    liked: Optional[bool] = None
    difficulty: Optional[Literal["easy", "moderate", "hard"]] = None
    taste_preference: Optional[str] = None
    digestion: Optional[Literal["comfortable", "heavy", "acidic", "bloated"]] = None
    hunger_level: Optional[Literal["still_hungry", "satisfied", "too_full"]] = None
    energy_level: Optional[Literal["low", "steady", "high"]] = None
    notes: str = Field(default="", max_length=1000)


class AdherenceLogRequest(BaseModel):
    user_id: str = "demo-user"
    date: str
    meal_type: str
    meal_name: str = ""
    status: Literal["completed", "partial", "skipped"]
    calories: Optional[float] = None
    protein_g: Optional[float] = None
    water_ml: Optional[float] = None
    weight_kg: Optional[float] = None
    sleep_hours: Optional[float] = None
    mood: Optional[Literal["low", "okay", "good", "great"]] = None
    digestion: Optional[Literal["comfortable", "heavy", "acidic", "bloated"]] = None
    notes: str = Field(default="", max_length=1000)


class AnalyticsRequest(UserContextPayload):
    nutrient_intake: Optional[dict[str, Any]] = None
    nutrient_intake: Optional[dict[str, Any]] = None


class ReminderRequest(BaseModel):
    user_id: str = "demo-user"
    reminder_type: Literal["meal", "hydration", "supplement", "grocery", "adherence", "follow_up"]
    title: str = Field(..., min_length=2, max_length=120)
    schedule: str = Field(..., description="Human-readable schedule or cron expression")
    channel: Literal["in_app", "email", "push", "whatsapp_ready", "sms", "whatsapp", "voice"] = "in_app"
    enabled: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)


class CommunicationSendRequest(BaseModel):
    user_id: str = "demo-user"
    channel: Literal["sms", "whatsapp", "voice", "in_app"] = "sms"
    recipient: str = Field(default="", max_length=40)
    message_type: Literal["meal_reminder", "hydration", "supplement", "adherence", "follow_up", "freeform"] = "freeform"
    content: str = Field(..., min_length=1, max_length=1000)
    related_reminder_id: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class CommunicationInboundRequest(BaseModel):
    user_id: str = "demo-user"
    channel: Literal["sms", "whatsapp", "voice", "in_app"] = "sms"
    sender: str = Field(default="", max_length=40)
    content: str = Field(..., min_length=1, max_length=1000)
    related_reminder_id: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)
