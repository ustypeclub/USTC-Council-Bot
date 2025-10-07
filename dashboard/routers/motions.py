"""API routes for motions."""

from fastapi import APIRouter, Depends
from dashboard.auth import get_current_user

router = APIRouter(prefix="/api/motions", tags=["motions"])


@router.get("/")
async def list_motions(user: dict = Depends(get_current_user)):
    return {"motions": []}


@router.get("/{motion_id}")
async def get_motion(motion_id: int, user: dict = Depends(get_current_user)):
    return {"id": motion_id, "text": "Example motion"}