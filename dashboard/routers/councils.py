"""API routes for councils.

Provides JSON endpoints for listing councils and retrieving details.  For
demonstration these endpoints return empty lists.
"""

from fastapi import APIRouter, Depends, HTTPException
from dashboard.auth import get_current_user

router = APIRouter(prefix="/api/councils", tags=["councils"])


@router.get("/")
async def list_councils(user: dict = Depends(get_current_user)):
    # In a full implementation this would query the bot database
    return {"councils": []}


@router.get("/{council_id}")
async def get_council(council_id: int, user: dict = Depends(get_current_user)):
    # Return dummy council
    return {"id": council_id, "name": f"Council {council_id}"}