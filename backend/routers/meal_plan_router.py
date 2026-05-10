"""routers/meal_plan_router.py"""
from fastapi import APIRouter
from backend.agents.clinical_analyst import ClinicalAnalystAgent
from backend.agents.meal_planner import MealPlannerAgent
from backend.models.request_models import MealPlanRequest
from backend.models.response_models import MealPlanResponse

router = APIRouter()
analyst = ClinicalAnalystAgent()
planner = MealPlannerAgent()


@router.post("", response_model=MealPlanResponse)
async def generate_meal_plan(request: MealPlanRequest) -> MealPlanResponse:
    """
    Generate a 7-day personalised Indian meal plan.
    If daily_targets are not provided, they are computed from the health profile.
    """
    if request.daily_targets:
        targets = request.daily_targets
    else:
        nutrient_resp = await analyst.analyse(request.health_profile)
        targets = nutrient_resp.daily_targets.model_dump()

    return await planner.generate(
        health_profile=request.health_profile,
        preference_profile=request.preference_profile,
        daily_targets=targets,
    )
