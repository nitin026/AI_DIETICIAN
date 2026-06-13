"""Safety rules for nutrition coaching and food-drug interaction warnings."""
from __future__ import annotations


DISCLAIMER = (
    "This AI nutrition assistant provides general education and meal-planning support. "
    "It does not diagnose, treat, prescribe medication, or replace a qualified clinician."
)


INTERACTION_RULES: dict[str, list[str]] = {
    "warfarin": [
        "Keep vitamin K intake consistent; sudden large changes in spinach, kale, methi, or broccoli can affect warfarin response.",
    ],
    "metformin": [
        "Long-term metformin use can increase B12 deficiency risk; discuss B12 testing with your clinician.",
    ],
    "insulin": [
        "Do not skip meals after insulin without clinician guidance; monitor for hypoglycemia symptoms.",
    ],
    "sulfonylurea": [
        "Skipping meals with sulfonylurea diabetes medicines can increase hypoglycemia risk.",
    ],
    "lisinopril": [
        "ACE inhibitors may raise potassium; avoid potassium supplements unless prescribed.",
    ],
    "amlodipine": [
        "For hypertension, keep sodium low and avoid grapefruit-heavy routines unless your clinician approves.",
    ],
    "levothyroxine": [
        "Take levothyroxine away from calcium, iron, soy, and high-fibre supplements by several hours.",
    ],
}


UNSAFE_PATTERNS = (
    "stop medication",
    "quit medicine",
    "replace medicine",
    "cure diabetes",
    "cure hypertension",
    "crash diet",
    "water fast",
    "detox",
)


def medication_warnings(medications: list[str]) -> list[str]:
    warnings: list[str] = []
    meds = " ".join(medications).lower()
    for keyword, notes in INTERACTION_RULES.items():
        if keyword in meds:
            warnings.extend(notes)
    return warnings


def safety_response_needed(message: str) -> bool:
    lower = message.lower()
    return any(pattern in lower for pattern in UNSAFE_PATTERNS)


def build_safety_prefix(medications: list[str]) -> str:
    notes = medication_warnings(medications)
    if not notes:
        return DISCLAIMER
    joined = " ".join(notes)
    return f"{DISCLAIMER} Safety note: {joined}"