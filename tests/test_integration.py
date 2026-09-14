"""Integration tests for setting up a config entry and its entities."""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.eaton_ableedge.const import DOMAIN
from custom_components.eaton_ableedge.diagnostics import (
    async_get_config_entry_diagnostics,
)

from .test_api import SAMPLE_BREAKER_RESPONSE

ENTRY_DATA = {
    "api_key": "api-key",
    "api_secret": "api-secret",
    "client_id": "client-id",
    "eaton_account_username": "user@example.com",
    "eaton_account_password": "password",
    "organization_secret": "org-secret",
    "breaker_id": SAMPLE_BREAKER_RESPONSE["id"],
}


async def _setup_entry(hass: HomeAssistant, aioclient_mock) -> MockConfigEntry:
    entry = MockConfigEntry(domain=DOMAIN, data=ENTRY_DATA, unique_id=ENTRY_DATA["breaker_id"])
    entry.add_to_hass(hass)

    with patch(
        "custom_components.eaton_ableedge.api.EatonAbleEdgeApiClient.async_get_breaker_data",
        new=AsyncMock(return_value=SAMPLE_BREAKER_RESPONSE),
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    return entry


async def test_setup_creates_entities(hass: HomeAssistant, aioclient_mock) -> None:
    """Setting up the entry should create the expected sensor entities."""
    await _setup_entry(hass, aioclient_mock)

    breaker_id = ENTRY_DATA["breaker_id"].replace("-", "_")
    connected_state = hass.states.get(
        f"binary_sensor.eaton_breaker_{breaker_id}_connected"
    )
    assert connected_state is not None
    assert connected_state.state == "on"

    rssi_state = hass.states.get(f"sensor.eaton_breaker_{breaker_id}_signal_strength")
    assert rssi_state is not None
    assert rssi_state.state == "-81"


async def test_diagnostics_redacts_secrets(hass: HomeAssistant, aioclient_mock) -> None:
    """Diagnostics output should redact all secrets and tokens."""
    entry = await _setup_entry(hass, aioclient_mock)

    diagnostics = await async_get_config_entry_diagnostics(hass, entry)

    assert diagnostics["entry_data"]["api_secret"] == "**REDACTED**"
    assert diagnostics["entry_data"]["eaton_account_password"] == "**REDACTED**"
    assert diagnostics["entry_data"]["organization_secret"] == "**REDACTED**"
    assert diagnostics["breaker_data"]["id"] == SAMPLE_BREAKER_RESPONSE["id"]
