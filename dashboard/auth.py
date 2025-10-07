"""Authentication utilities for the dashboard.

This module implements a minimal OAuth2 flow with Discord.  Users are
redirected to Discord to grant the ``identify`` scope.  On return, a JWT
session cookie is issued containing the Discord user ID and username.  The
JWT is signed with ``SECRET_KEY`` from the environment.

Functions ``get_current_user`` and ``require_admin`` can be used as
dependencies in FastAPI routes to enforce authentication and authorisation.
"""

from __future__ import annotations

import os
import time
import jwt
from fastapi import Depends, HTTPException, Request
from fastapi.responses import RedirectResponse

from bot.src.utils.oauth import DiscordOAuth


SECRET_KEY = os.getenv("SECRET_KEY", "change_me")
DISCORD_CLIENT_ID = os.getenv("DISCORD_CLIENT_ID", "")
DISCORD_CLIENT_SECRET = os.getenv("DISCORD_CLIENT_SECRET", "")
OAUTH_REDIRECT_URI = os.getenv("OAUTH_REDIRECT_URI", "http://localhost:8000/api/auth/callback")


oauth_client = DiscordOAuth(DISCORD_CLIENT_ID, DISCORD_CLIENT_SECRET, OAUTH_REDIRECT_URI)


def create_jwt(payload: dict, expires_in: int = 3600) -> str:
    """Create a signed JWT containing ``payload`` with an expiry."""
    now = int(time.time())
    payload_copy = payload.copy()
    payload_copy.update({"exp": now + expires_in, "iat": now})
    return jwt.encode(payload_copy, SECRET_KEY, algorithm="HS256")


def decode_jwt(token: str) -> dict:
    """Decode a JWT and return its payload or raise JWTError."""
    return jwt.decode(token, SECRET_KEY, algorithms=["HS256"])


async def get_current_user(request: Request) -> dict:
    """Retrieve the currently logged‑in user from the session cookie.

    If no valid session exists, redirect to the login route.
    """
    token = request.cookies.get("session")
    if not token:
        # redirect to login
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = decode_jwt(token)
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid session token")
    return payload


async def require_admin(user: dict = Depends(get_current_user)) -> dict:
    """Dependency that requires the user to be an admin.

    The user payload must contain an ``is_admin`` boolean.  Otherwise 403 is
    raised.  In this example, the admin flag is always false because role
    membership is not checked.
    """
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Insufficient privileges")
    return user


async def login(request: Request) -> RedirectResponse:
    """Initiate the OAuth2 login by redirecting to Discord."""
    url, state = oauth_client.get_authorization_url()
    response = RedirectResponse(url)
    # Save state in session cookie for CSRF protection (omitted in this example)
    return response


async def callback(request: Request) -> RedirectResponse:
    """Handle OAuth2 callback from Discord and set the session cookie."""
    code = request.query_params.get("code")
    if not code:
        raise HTTPException(status_code=400, detail="Missing code in callback")
    token = oauth_client.fetch_token(code)
    user = oauth_client.fetch_user(token)
    # Build session payload
    payload = {
        "user_id": user.get("id"),
        "username": user.get("username"),
        # admin flag false by default; a real implementation would query
        # Discord API to check roles or guild permissions
        "is_admin": False,
    }
    jwt_token = create_jwt(payload)
    response = RedirectResponse("/")
    response.set_cookie("session", jwt_token, httponly=True, secure=os.getenv("HTTPS", "false").lower() == "true")
    return response