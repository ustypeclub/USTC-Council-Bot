"""API routes for votes."""

from fastapi import APIRouter, Depends
from dashboard.auth import get_current_user

router = APIRouter(prefix="/api/votes", tags=["votes"])


@router.get("/motion/{motion_id}")
async def list_votes(motion_id: int, user: dict = Depends(get_current_user)):
    return {"motion_id": motion_id, "votes": []}