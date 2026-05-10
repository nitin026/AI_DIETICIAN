"""
utils/helpers.py
Mifflin-St Jeor BMR / TDEE calculators and activity multiplier lookup.
"""
from __future__ import annotations

ACTIVITY_MULTIPLIERS: dict[str, float] = {
    "sedentary": 1.2,
    "lightly_active": 1.375,
    "moderately_active": 1.55,
    "very_active": 1.725,
    "extra_active": 1.9,
}


def calculate_bmr(weight_kg: float, height_cm: float, age: int, gender: str) -> float:
    """
    Mifflin-St Jeor Equation.
    BMR = 10*weight + 6.25*height − 5*age + s
    s = +5  (male)
    s = −161 (female / other)
    """
    s = 5 if gender.lower() == "male" else -161
    return 10 * weight_kg + 6.25 * height_cm - 5 * age + s


def calculate_tdee(bmr: float, activity_level: str) -> float:
    """Total Daily Energy Expenditure = BMR × activity multiplier."""
    multiplier = ACTIVITY_MULTIPLIERS.get(activity_level, 1.2)
    return round(bmr * multiplier, 1)


def bmi(weight_kg: float, height_cm: float) -> float:
    return round(weight_kg / (height_cm / 100) ** 2, 1)
