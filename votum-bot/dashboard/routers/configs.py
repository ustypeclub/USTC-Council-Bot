"""API routes for council configuration."""

from fastapi import APIRouter, Depends
from dashboard.auth import get_current_user

router = APIRouter(prefix="/api/configs", tags=["configs"])


@router.get("/council/{council_id}")
async def get_config(council_id: int, user: dict = Depends(get_current_user)):
    return {"council_id": council_id, "config": {}}