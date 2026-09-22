"""Tests for the Eaton AbleEdge API client."""
from __future__ import annotations

import pytest

from custom_components.eaton_ableedge.api import (
    EatonAbleEdgeApiClient,
    EatonAbleEdgeAuthError,
    EatonAbleEdgeConnectionError,
)
from custom_components.eaton_ableedge.const import (
    BREAKER_URL_TEMPLATE,
    OAUTH_TOKEN_URL,
    ORGANIZATION_TOKEN_URL,
    USER_LOGIN_URL,
)

def _make_client(session) -> EatonAbleEdgeApiClient:
    return EatonAbleEdgeApiClient(
        session=session,
        api_key="api-key",
        api_secret="api-secret",
        client_id="client-id",
        eaton_account_username="user@example.com",
        eaton_account_password="password",
        organization_secret="org-secret",
    )


def _mock_success_chain(aioclient_mock, breaker_id, sample_breaker_response) -> None:
    aioclient_mock.post(
        OAUTH_TOKEN_URL,
        json={"access_token": "oauth-token-1", "expires_in": 3600},
    )
    aioclient_mock.post(
        USER_LOGIN_URL,
        json={"accessToken": "session-token-1"},
    )
    aioclient_mock.post(
        ORGANIZATION_TOKEN_URL,
        json={"token": "org-token-1"},
    )
    aioclient_mock.get(
        BREAKER_URL_TEMPLATE.format(breaker_id=breaker_id),
        json=sample_breaker_response,
    )


async def test_basic_auth_value_matches_expected_base64(hass, aioclient_mock) -> None:
    """The Basic auth value should be base64("api_key:api_secret")."""
    from homeassistant.helpers.aiohttp_client import async_get_clientsession

    client = _make_client(async_get_clientsession(hass))
    assert client._basic_auth_value() == "YXBpLWtleTphcGktc2VjcmV0"


async def test_full_auth_flow_and_breaker_fetch(
    hass, aioclient_mock, breaker_id, sample_breaker_response
) -> None:
    """The client should walk the full auth chain and fetch breaker data."""
    from homeassistant.helpers.aiohttp_client import async_get_clientsession

    _mock_success_chain(aioclient_mock, breaker_id, sample_breaker_response)
    client = _make_client(async_get_clientsession(hass))

    data = await client.async_get_breaker_data(breaker_id)

    assert data == sample_breaker_response
    assert client._oauth_token.value == "oauth-token-1"
    assert client._session_access_token is None  # only requested via async_authorize_user
    assert client._organization_token == "org-token-1"


async def test_oauth_token_is_cached(
    hass, aioclient_mock, breaker_id, sample_breaker_response
) -> None:
    """A second call should reuse the cached OAuth token."""
    from homeassistant.helpers.aiohttp_client import async_get_clientsession

    _mock_success_chain(aioclient_mock, breaker_id, sample_breaker_response)
    client = _make_client(async_get_clientsession(hass))

    token1 = await client.async_get_oauth_token()
    token2 = await client.async_get_oauth_token()

    assert token1 == token2
    oauth_calls = [
        call for call in aioclient_mock.mock_calls if str(call[1]).startswith(OAUTH_TOKEN_URL)
    ]
    assert len(oauth_calls) == 1


async def test_auth_error_raised_on_401(hass, aioclient_mock) -> None:
    """A 401 response should raise EatonAbleEdgeAuthError."""
    from homeassistant.helpers.aiohttp_client import async_get_clientsession

    aioclient_mock.post(OAUTH_TOKEN_URL, status=401, json={"error": "invalid_client"})
    client = _make_client(async_get_clientsession(hass))

    with pytest.raises(EatonAbleEdgeAuthError):
        await client.async_get_oauth_token()


async def test_auth_error_raised_on_401_with_unparsable_body(
    hass, aioclient_mock
) -> None:
    """A 401 response with a non-JSON body should still raise an auth error."""
    from homeassistant.helpers.aiohttp_client import async_get_clientsession

    aioclient_mock.post(OAUTH_TOKEN_URL, status=401, text="not json")
    client = _make_client(async_get_clientsession(hass))

    with pytest.raises(EatonAbleEdgeAuthError):
        await client.async_get_oauth_token()


async def test_connection_error_raised_on_500(hass, aioclient_mock) -> None:
    """A 500 response should raise EatonAbleEdgeConnectionError."""
    from homeassistant.helpers.aiohttp_client import async_get_clientsession

    aioclient_mock.post(OAUTH_TOKEN_URL, status=500, json={"error": "server_error"})
    client = _make_client(async_get_clientsession(hass))

    with pytest.raises(EatonAbleEdgeConnectionError):
        await client.async_get_oauth_token()


async def test_breaker_fetch_retries_after_expired_org_token(
    hass, aioclient_mock, breaker_id
) -> None:
    """An expired org token should trigger a refresh and retry once."""
    from homeassistant.helpers.aiohttp_client import async_get_clientsession

    aioclient_mock.post(
        OAUTH_TOKEN_URL,
        json={"access_token": "oauth-token-1", "expires_in": 3600},
    )
    aioclient_mock.post(
        ORGANIZATION_TOKEN_URL,
        json={"token": "org-token-1"},
    )
    breaker_url = BREAKER_URL_TEMPLATE.format(breaker_id=breaker_id)
    aioclient_mock.get(breaker_url, status=401, json={"error": "unauthorized"})

    client = _make_client(async_get_clientsession(hass))

    with pytest.raises(EatonAbleEdgeAuthError):
        await client.async_get_breaker_data(breaker_id)

    # Initial attempt + one retry after forcing a token refresh.
    breaker_calls = [
        call for call in aioclient_mock.mock_calls if str(call[1]) == breaker_url
    ]
    assert len(breaker_calls) == 2
