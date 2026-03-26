from fastapi import APIRouter

from backend.models.schemas import APIResponse, CheckInCreate

router = APIRouter(prefix="/checkin", tags=["checkin"])


@router.post("/", response_model=APIResponse)
async def create_checkin(payload: CheckInCreate):
    # TODO: Forward to companion agent, update graph, recalculate score
    return APIResponse(
        success=True,
        data={"reply": "TODO: companion response", "session_id": "todo"},
    )
