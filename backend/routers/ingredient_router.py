"""routers/ingredient_router.py"""
from fastapi import APIRouter
from backend.agents.ingredient_validator import IngredientValidatorAgent
from backend.models.request_models import IngredientValidationRequest
from backend.models.response_models import IngredientValidationResponse

router = APIRouter()
agent = IngredientValidatorAgent()


@router.post("", response_model=IngredientValidationResponse)
async def validate_ingredients(request: IngredientValidationRequest) -> IngredientValidationResponse:
    """
    Validate meal plan ingredients against the pantry.
    Returns a revised meal plan with substitutions and a grocery alert list.
    """
    return await agent.validate(
        meal_plan=request.meal_plan,
        pantry=request.pantry_ingredients,
        nutrient_targets={},   # pass targets for richer substitution context if available
    )
