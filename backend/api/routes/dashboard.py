from fastapi import APIRouter

from backend.models.schemas import APIResponse

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/{user_id}/score", response_model=APIResponse)
async def get_life_score(user_id: str):
    # TODO: Calculate and return life score
    return APIResponse(
        success=True,
        data={"user_id": user_id, "total": 0, "spheres": []},
    )


@router.get("/{user_id}/scenarios", response_model=APIResponse)
async def get_scenarios(user_id: str):
    # TODO: Generate and return scenarios
    return APIResponse(
        success=True,
        data={"user_id": user_id, "scenarios": []},
    )


@router.get("/{user_id}/graph", response_model=APIResponse)
async def get_graph(user_id: str):
    # TODO: Return user's knowledge graph
    return APIResponse(
        success=True,
        data={"user_id": user_id, "nodes": [], "edges": []},
    )
