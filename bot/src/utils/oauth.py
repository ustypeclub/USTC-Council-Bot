"""Discord OAuth2 helper utilities for the dashboard.

This module wraps the OAuth2 flow required to authenticate users via
Discord.  It uses the ``requests-oauthlib`` library to generate
authorization URLs, exchange codes for access tokens and fetch the user's
identity.  Only the ``identify`` scope is requested.

Usage:

    oauth = DiscordOAuth(client_id, client_secret, redirect_uri)
    url, state = oauth.get_authorization_url()
    # redirect user to url
    # after callback:
    token = oauth.fetch_token(code)
    user = oauth.fetch_user(token)
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Tuple

from requests_oauthlib import OAuth2Session


log = logging.getLogger(__name__)

DISCORD_AUTH_BASE = "https://discord.com/api/oauth2/authorize"
DISCORD_TOKEN_URL = "https://discord.com/api/oauth2/token"
DISCORD_API_BASE = "https://discord.com/api"


class DiscordOAuth:
    def __init__(self, client_id: str, client_secret: str, redirect_uri: str) -> None:
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.scope = ["identify"]

    def _session(self, token: Dict[str, Any] | None = None) -> OAuth2Session:
        return OAuth2Session(
            client_id=self.client_id,
            token=token,
            redirect_uri=self.redirect_uri,
            scope=self.scope,
        )

    def get_authorization_url(self, state: str | None = None) -> Tuple[str, str]:
        """Return the Discord OAuth2 authorization URL and state."""
        oauth = self._session()
        url, state = oauth.authorization_url(
            DISCORD_AUTH_BASE,
            prompt="consent",
        )
        return url, state

    def fetch_token(self, code: str) -> Dict[str, Any]:
        """Exchange the authorization code for an access token."""
        oauth = self._session()
        token = oauth.fetch_token(
            DISCORD_TOKEN_URL,
            client_secret=self.client_secret,
            code=code,
        )
        return token

    def fetch_user(self, token: Dict[str, Any]) -> Dict[str, Any]:
        """Fetch the user's identity using the access token."""
        oauth = self._session(token=token)
        resp = oauth.get(f"{DISCORD_API_BASE}/users/@me")
        resp.raise_for_status()
        return resp.json()