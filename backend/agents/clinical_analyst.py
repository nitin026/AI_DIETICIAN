"""
agents/clinical_analyst.py
Orchestrates BMR calculation, RAG retrieval, and BioMistral refinement
to produce a medically-grounded nutrient prescription.
"""
from __future__ import annotations

from loguru import logger

from backend.models.request_models import HealthProfile
from backend.models.response_models import NutrientPredictionResponse
from backend.prompts.nutrient_prompt import build_nutrient_prompt, NUTRIENT_SYSTEM
from backend.rag.retriever import retrieve
from backend.services.nutrient_reference import FOOD_SOURCES, score_nutrient_adequacy
from backend.services import llm_service, nutrition_service


class ClinicalAnalystAgent:
    """
    Responsibilities:
    - Compute BMR/TDEE baseline (deterministic)
    - Query ICMR-NIN vector store for disease-specific guidelines
    - Refine nutrient targets via BioMistral
    - Return a validated NutrientPredictionResponse
    """

    async def analyse(self, profile: HealthProfile) -> NutrientPredictionResponse:
        logger.info("ClinicalAnalystAgent: analysing profile for {}-year-old {}", profile.age, profile.gender)

        # ── Step 1: Baseline calculation (no LLM) ────────────────────
        baseline = nutrition_service.compute_baseline_nutrients(profile)

        # ── Step 2: RAG retrieval ─────────────────────────────────────
        rag_queries = self._build_rag_queries(profile)
        icmr_context: list[str] = []
        for query in rag_queries:
            icmr_context.extend(retrieve(query, k=2))
        icmr_context = list(dict.fromkeys(icmr_context))  # deduplicate while preserving order

        # ── Step 3: LLM refinement ────────────────────────────────────
        health_summary = {
            "age": profile.age,
            "gender": profile.gender,
            "weight_kg": profile.weight_kg,
            "height_cm": profile.height_cm,
            "activity_level": profile.activity_level,
            "diseases": profile.diseases,
            "medications": profile.medications,
            "addictions": profile.addictions.model_dump(),
        }
        prompt = build_nutrient_prompt(
            health_summary=health_summary,
            baseline_nutrients=baseline,
            icmr_context=icmr_context,
        )

        try:
            llm_output = await llm_service.generate_json(prompt, system=NUTRIENT_SYSTEM, task="nutrient")
            refined_targets = self._merge_daily_targets(
                baseline["daily_targets"],
                llm_output.get("daily_targets", {}),
            )
            disease_notes = llm_output.get("disease_notes", baseline["disease_notes"])
            med_interactions = llm_output.get("medication_interactions", baseline["medication_interactions"])
            icmr_refs = llm_output.get("icmr_references", [])
        except Exception as exc:
            logger.warning("LLM refinement failed ({}); falling back to baseline.", exc)
            refined_targets = baseline["daily_targets"]
            disease_notes = baseline["disease_notes"]
            med_interactions = baseline["medication_interactions"]
            icmr_refs = []

        adequacy = score_nutrient_adequacy(refined_targets)
        deficiency_risks = [
            f"{name.replace('_', ' ').title()} may need attention."
            for name, item in adequacy.get("nutrients", {}).items()
            if item.get("status") == "low"
        ][:8]

        return NutrientPredictionResponse(
            bmr=baseline["bmr"],
            tdee=baseline["tdee"],
            daily_targets=refined_targets,
            disease_notes=disease_notes,
            medication_interactions=med_interactions,
            icmr_references=icmr_refs,
            nutrient_adequacy=adequacy,
            deficiency_risks=deficiency_risks,
            food_suggestions=FOOD_SOURCES,
        )

    def _merge_daily_targets(self, baseline_targets: dict, llm_targets: dict | None) -> dict:
        """Preserve the full deterministic micronutrient panel after LLM refinement."""
        merged = dict(baseline_targets)
        for key, value in (llm_targets or {}).items():
            if value is not None:
                merged[key] = value

        if "b12_mcg" in merged and "vitamin_b12_mcg" not in merged:
            merged["vitamin_b12_mcg"] = merged["b12_mcg"]
        elif "vitamin_b12_mcg" in merged:
            merged["b12_mcg"] = merged["vitamin_b12_mcg"]

        return merged

    def _build_rag_queries(self, profile: HealthProfile) -> list[str]:
        """Construct semantic queries tailored to the patient's conditions."""
        queries = ["Indian daily nutrient requirements", "ICMR-NIN recommended dietary allowances"]
        for disease in profile.diseases:
            queries.append(f"dietary recommendations for {disease}")
        for med in profile.medications:
            queries.append(f"food interaction with {med}")
        if profile.age > 60:
            queries.append("nutrition for elderly Indians")
        return queries
