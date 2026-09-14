"""API client for the Eaton AbleEdge Breakers integration.

This module implements the API flow described in the project README using
Home Assistant's shared async HTTP client (aiohttp). No shell commands or
blocking I/O are used.
"""
from __future__ import annotations

import base64
import logging
import time
from dataclasses import dataclass, field
from typing import Any

from aiohttp import ClientError, ClientResponse, ClientSession

from .const import (
    BREAKER_URL_TEMPLATE,
    DEFAULT_TOKEN_LIFETIME_SECONDS,
    OAUTH_TOKEN_URL,
    ORGANIZATION_TOKEN_URL,
    TOKEN_REFRESH_SAFETY_MARGIN_SECONDS,
    USER_LOGIN_URL,
)

_LOGGER = logging.getLogger(__name__)


class EatonAbleEdgeApiError(Exception):
    """Base error for the Eaton AbleEdge API client."""


class EatonAbleEdgeAuthError(EatonAbleEdgeApiError):
    """Raised when authentication/authorization with Eaton fails.

    This covers invalid API key/secret, invalid account credentials, an
    invalid/expired organization secret, or a 401/403 response from Eaton.
    """


class EatonAbleEdgeConnectionError(EatonAbleEdgeApiError):
    """Raised when there is a network/communication problem with Eaton."""


@dataclass
class _CachedToken:
    """An in-memory cached token with an expiry timestamp."""

    value: str | None = None
    expires_at: float = 0.0

    def is_valid(self) -> bool:
        """Return True if the token exists and is not near expiry."""
        return bool(self.value) and time.monotonic() < self.expires_at


@dataclass
class EatonAbleEdgeApiClient:
    """Client for interacting with the Eaton AbleEdge APIs.

    Tokens are cached in memory only for the lifetime of this object and are
    never persisted to disk, logs, or diagnostics.
    """

    session: ClientSession
    api_key: str
    api_secret: str
    client_id: str
    eaton_account_username: str
    eaton_account_password: str
    organization_secret: str

    _oauth_token: _CachedToken = field(default_factory=_CachedToken, init=False)
    _session_access_token: str | None = field(default=None, init=False)
    _organization_token: str | None = field(default=None, init=False)

    def _basic_auth_value(self) -> str:
        """Build the Basic authorization value from the API key/secret.

        Equivalent to `echo -n "<API_KEY>:<API_SECRET>" | base64`, done
        directly in Python instead of shelling out.
        """
        raw = f"{self.api_key}:{self.api_secret}".encode("utf-8")
        return base64.b64encode(raw).decode("ascii")

    async def _request_json(
        self, method: str, url: str, **kwargs: Any
    ) -> tuple[ClientResponse, Any]:
        """Make an HTTP request and return the response and parsed JSON body."""
        try:
            response = await self.session.request(method, url, **kwargs)
        except ClientError as err:
            raise EatonAbleEdgeConnectionError(
                f"Error communicating with Eaton API ({url}): {err}"
            ) from err

        try:
            data = await response.json(content_type=None)
        except (ValueError, ClientError) as err:
            data = None
            if response.status >= 400:
                raise EatonAbleEdgeConnectionError(
                    f"Invalid response from Eaton API ({url}): "
                    f"status {response.status}"
                ) from err

        if response.status in (401, 403):
            raise EatonAbleEdgeAuthError(
                f"Eaton API authorization failed for {url} "
                f"(status {response.status})"
            )
        if response.status >= 400:
            raise EatonAbleEdgeConnectionError(
                f"Eaton API request to {url} failed with status "
                f"{response.status}"
            )

        return response, data

    async def async_get_oauth_token(self, *, force_refresh: bool = False) -> str:
        """Return a valid OAuth token, refreshing it if needed.

        Refreshes proactively before expiry (with a safety margin) based on
        the `expires_in` value returned by Eaton, rather than a hard-coded
        interval.
        """
        if not force_refresh and self._oauth_token.is_valid():
            return self._oauth_token.value  # type: ignore[return-value]

        headers = {
            "Authorization": f"Basic {self._basic_auth_value()}",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        params = {"grant_type": "client_credentials"}

        _, data = await self._request_json(
            "POST",
            OAUTH_TOKEN_URL,
            headers=headers,
            params=params,
            data="",
        )

        if not isinstance(data, dict) or "access_token" not in data:
            raise EatonAbleEdgeAuthError(
                "Eaton OAuth token response did not include an access_token"
            )

        access_token = data["access_token"]
        try:
            expires_in = int(data.get("expires_in", DEFAULT_TOKEN_LIFETIME_SECONDS))
        except (TypeError, ValueError):
            expires_in = DEFAULT_TOKEN_LIFETIME_SECONDS

        safety_margin = min(
            TOKEN_REFRESH_SAFETY_MARGIN_SECONDS, max(expires_in // 2, 0)
        )
        self._oauth_token = _CachedToken(
            value=access_token,
            expires_at=time.monotonic() + expires_in - safety_margin,
        )
        return access_token

    async def async_authorize_user(self, *, force_refresh: bool = False) -> str:
        """Authorize the Eaton account user and cache the session access token."""
        if not force_refresh and self._session_access_token:
            return self._session_access_token

        oauth_token = await self.async_get_oauth_token()
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + oauth_token,
        }
        body = {
            "email": self.eaton_account_username,
            "password": self.eaton_account_password,
        }

        _, data = await self._request_json(
            "POST", USER_LOGIN_URL, headers=headers, json=body
        )

        if not isinstance(data, dict) or "accessToken" not in data:
            raise EatonAbleEdgeAuthError(
                "Eaton user login response did not include an accessToken"
            )

        self._session_access_token = data["accessToken"]
        return self._session_access_token

    async def async_get_organization_token(
        self, *, force_refresh: bool = False
    ) -> str:
        """Retrieve and cache the AbleEdge organization token."""
        if not force_refresh and self._organization_token:
            return self._organization_token

        oauth_token = await self.async_get_oauth_token()
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": "Bearer " + oauth_token,
        }
        body = {
            "clientId": self.client_id,
            "secret": self.organization_secret,
        }

        _, data = await self._request_json(
            "POST", ORGANIZATION_TOKEN_URL, headers=headers, json=body
        )

        if not isinstance(data, dict) or "token" not in data:
            raise EatonAbleEdgeAuthError(
                "Eaton organization token response did not include a token"
            )

        self._organization_token = data["token"]
        return self._organization_token

    async def async_get_breaker_data(
        self, breaker_id: str, *, retry_on_auth_error: bool = True
    ) -> dict[str, Any]:
        """Fetch breaker data for the configured breaker ID."""
        organization_token = await self.async_get_organization_token()
        headers = {
            "accept": "application/json",
            "api-key": self.api_key,
            "authorization": "Bearer " + organization_token,
        }
        url = BREAKER_URL_TEMPLATE.format(breaker_id=breaker_id)

        try:
            _, data = await self._request_json("GET", url, headers=headers)
        except EatonAbleEdgeAuthError:
            if not retry_on_auth_error:
                raise
            # The organization token (or OAuth token backing it) may have
            # expired or been revoked; force a refresh and retry once.
            self._organization_token = None
            await self.async_get_oauth_token(force_refresh=True)
            await self.async_get_organization_token(force_refresh=True)
            return await self.async_get_breaker_data(
                breaker_id, retry_on_auth_error=False
            )

        if not isinstance(data, dict):
            raise EatonAbleEdgeConnectionError(
                f"Unexpected breaker data response for breaker {breaker_id}"
            )

        return data

    def get_cached_token_diagnostics(self) -> dict[str, str | None]:
        """Return the current in-memory token values, for diagnostics use only.

        These values are never persisted; callers are responsible for
        redacting them before including them in any diagnostics output.
        """
        return {
            "oauth_token": self._oauth_token.value,
            "session_access_token": self._session_access_token,
            "organization_token": self._organization_token,
        }

    async def async_validate_credentials(self) -> None:
        """Validate credentials end-to-end (used by the config flow).

        Runs the full auth flow: OAuth token, user authorization, and
        organization token acquisition. Raises EatonAbleEdgeAuthError or
        EatonAbleEdgeConnectionError on failure.
        """
        await self.async_get_oauth_token(force_refresh=True)
        await self.async_authorize_user(force_refresh=True)
        await self.async_get_organization_token(force_refresh=True)
