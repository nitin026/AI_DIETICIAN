"""Feedback-aware scoring and analytics for adaptive meal recommendations."""
from __future__ import annotations

from collections import Counter, defaultdict
from statistics import mean
from typing import Any


MEAL_KEYS = ("breakfast", "mid_morning_snack", "lunch", "evening_snack", "dinner")


def build_preference_memory(feedback_records: list[dict[str, Any]]) -> dict[str, Any]:
    liked: Counter[str] = Counter()
    disliked: Counter[str] = Counter()
    issues: Counter[str] = Counter()
    ratings: dict[str, list[float]] = defaultdict(list)

    for record in feedback_records:
        meal_name = (record.get("meal_name") or "unknown").lower()
        rating = float(record.get("rating") or 0)
        if rating:
            ratings[meal_name].append(rating)
        if record.get("liked") is True or rating >= 4:
            liked[meal_name] += 1
        if record.get("liked") is False or rating <= 2:
            disliked[meal_name] += 1
        for key in ("difficulty", "taste_preference", "digestion", "hunger_level", "energy_level"):
            value = record.get(key)
            if value:
                issues[f"{key}:{value}"] += 1

    avg_ratings = {meal: round(mean(values), 2) for meal, values in ratings.items() if values}
    return {
        "liked_meals": liked.most_common(8),
        "disliked_meals": disliked.most_common(8),
        "average_ratings": avg_ratings,
        "reported_patterns": issues.most_common(10),
    }


def score_meal(meal: dict[str, Any], memory: dict[str, Any], targets: dict[str, Any]) -> float:
    score = 70.0
    name = (meal.get("name") or "").lower()
    calories = float(meal.get("calories") or 0)
    protein = float(meal.get("protein_g") or 0)

    disliked = dict(memory.get("disliked_meals", []))
    liked = dict(memory.get("liked_meals", []))
    score += liked.get(name, 0) * 4
    score -= disliked.get(name, 0) * 10

    if targets.get("calories") and calories:
        per_meal_target = float(targets["calories"]) / 5
        score -= min(abs(calories - per_meal_target) / max(per_meal_target, 1) * 12, 12)
    if targets.get("protein_g") and protein:
        per_meal_protein = float(targets["protein_g"]) / 5
        if protein >= per_meal_protein * 0.85:
            score += 8
    return round(max(0, min(100, score)), 1)


def adherence_summary(records: list[dict[str, Any]]) -> dict[str, Any]:
    if not records:
        return {
            "average_score": 0,
            "current_streak": 0,
            "completed_meals": 0,
            "skipped_meals": 0,
            "daily_scores": [],
        }

    by_date: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        by_date[record.get("date", "")].append(record)

    daily_scores = []
    for date, day_records in sorted(by_date.items()):
        completed = sum(1 for r in day_records if r.get("status") == "completed")
        total = max(len(day_records), 1)
        daily_scores.append({"date": date, "score": round(completed / total * 100, 1)})

    current_streak = 0
    for item in reversed(daily_scores):
        if item["score"] >= 80:
            current_streak += 1
        else:
            break

    return {
        "average_score": round(mean(item["score"] for item in daily_scores), 1),
        "current_streak": current_streak,
        "completed_meals": sum(1 for r in records if r.get("status") == "completed"),
        "skipped_meals": sum(1 for r in records if r.get("status") == "skipped"),
        "daily_scores": daily_scores,
    }