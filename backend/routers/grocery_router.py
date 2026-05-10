"""routers/grocery_router.py"""
from fastapi import APIRouter
from backend.agents.grocery_agent import GroceryAgent
from backend.models.request_models import GroceryListRequest
from backend.models.response_models import GroceryListResponse

router = APIRouter()
agent = GroceryAgent()


@router.post("", response_model=GroceryListResponse)
async def generate_grocery_list(request: GroceryListRequest) -> GroceryListResponse:
    """
    Generate a categorised weekly grocery list from the meal plan,
    subtracting items already in the pantry.
    """
    return agent.generate(
        meal_plan=request.meal_plan,
        pantry_ingredients=request.pantry_ingredients,
    )
