"""Integration tests for setting up a config entry and its entities."""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.eaton_ableedge.const import DOMAIN
from custom_components.eaton_ableedge.diagnostics import (
    async_get_config_entry_diagnostics,
)

async def _setup_entry(
    hass: HomeAssistant, config_data, sample_breaker_response
) -> MockConfigEntry:
    entry = MockConfigEntry(
        domain=DOMAIN, data=config_data, unique_id=config_data["breaker_id"]
    )
    entry.add_to_hass(hass)

    with patch(
        "custom_components.eaton_ableedge.api.EatonAbleEdgeApiClient.async_get_breaker_data",
        new=AsyncMock(return_value=sample_breaker_response),
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    return entry


async def test_setup_creates_entities(
    hass: HomeAssistant, config_data, sample_breaker_response
) -> None:
    """Setting up the entry should create the expected sensor entities."""
    await _setup_entry(hass, config_data, sample_breaker_response)

    breaker_id = config_data["breaker_id"].replace("-", "_")
    connected_state = hass.states.get(
        f"binary_sensor.eaton_breaker_{breaker_id}_connected"
    )
    assert connected_state is not None
    assert connected_state.state == "on"

    rssi_state = hass.states.get(f"sensor.eaton_breaker_{breaker_id}_signal_strength")
    assert rssi_state is not None
    assert rssi_state.state == "-81"


async def test_diagnostics_redacts_secrets(
    hass: HomeAssistant, config_data, sample_breaker_response
) -> None:
    """Diagnostics output should redact all secrets and tokens."""
    entry = await _setup_entry(hass, config_data, sample_breaker_response)

    diagnostics = await async_get_config_entry_diagnostics(hass, entry)

    assert diagnostics["entry_data"]["api_secret"] == "**REDACTED**"
    assert diagnostics["entry_data"]["eaton_account_password"] == "**REDACTED**"
    assert diagnostics["entry_data"]["organization_secret"] == "**REDACTED**"
    assert diagnostics["breaker_data"]["id"] == sample_breaker_response["id"]
