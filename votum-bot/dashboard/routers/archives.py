"""API routes for archives."""

from fastapi import APIRouter, Depends
from dashboard.auth import get_current_user

router = APIRouter(prefix="/api/archives", tags=["archives"])


@router.get("/")
async def list_archives(user: dict = Depends(get_current_user)):
    return {"archives": []}