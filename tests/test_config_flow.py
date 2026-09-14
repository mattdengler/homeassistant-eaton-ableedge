"""Tests for the Eaton AbleEdge config flow."""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResultType

from custom_components.eaton_ableedge.api import (
    EatonAbleEdgeAuthError,
    EatonAbleEdgeConnectionError,
)
from custom_components.eaton_ableedge.const import DOMAIN

USER_INPUT = {
    "api_key": "api-key",
    "api_secret": "api-secret",
    "client_id": "client-id",
    "eaton_account_username": "user@example.com",
    "eaton_account_password": "password",
    "organization_secret": "org-secret",
    "breaker_id": "ffabf727-d62b-4900-886b-946574e4dd66",
}


async def test_user_flow_success(hass) -> None:
    """A valid configuration should create a config entry."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM

    with patch(
        "custom_components.eaton_ableedge.config_flow._async_validate_input",
        new=AsyncMock(return_value=None),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], USER_INPUT
        )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == USER_INPUT


async def test_user_flow_invalid_auth(hass) -> None:
    """Auth errors should be surfaced as a form error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "custom_components.eaton_ableedge.config_flow._async_validate_input",
        new=AsyncMock(side_effect=EatonAbleEdgeAuthError("bad auth")),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], USER_INPUT
        )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "invalid_auth"}


async def test_user_flow_cannot_connect(hass) -> None:
    """Connection errors should be surfaced as a form error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "custom_components.eaton_ableedge.config_flow._async_validate_input",
        new=AsyncMock(side_effect=EatonAbleEdgeConnectionError("no connection")),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], USER_INPUT
        )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}
