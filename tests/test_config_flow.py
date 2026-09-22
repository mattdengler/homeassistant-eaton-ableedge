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

async def test_user_flow_success(hass, config_data) -> None:
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
            result["flow_id"], config_data
        )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == config_data


async def test_user_flow_invalid_auth(hass, config_data) -> None:
    """Auth errors should be surfaced as a form error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "custom_components.eaton_ableedge.config_flow._async_validate_input",
        new=AsyncMock(side_effect=EatonAbleEdgeAuthError("bad auth")),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], config_data
        )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "invalid_auth"}


async def test_user_flow_cannot_connect(hass, config_data) -> None:
    """Connection errors should be surfaced as a form error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "custom_components.eaton_ableedge.config_flow._async_validate_input",
        new=AsyncMock(side_effect=EatonAbleEdgeConnectionError("no connection")),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], config_data
        )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}
