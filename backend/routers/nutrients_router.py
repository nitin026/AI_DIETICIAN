"""routers/nutrients_router.py"""
from fastapi import APIRouter
from backend.agents.clinical_analyst import ClinicalAnalystAgent
from backend.models.request_models import NutrientPredictionRequest
from backend.models.response_models import NutrientPredictionResponse

router = APIRouter()
agent = ClinicalAnalystAgent()


@router.post("", response_model=NutrientPredictionResponse)
async def predict_nutrients(request: NutrientPredictionRequest) -> NutrientPredictionResponse:
    """
    Analyse the patient's health profile and return personalised daily nutrient targets.
    Uses Mifflin-St Jeor → disease/medication adjustments → BioMistral + ICMR-NIN RAG.
    """
    return await agent.analyse(request.health_profile)
