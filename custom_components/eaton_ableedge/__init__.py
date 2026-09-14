"""The Eaton AbleEdge Breakers integration."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_KEY, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import EatonAbleEdgeApiClient
from .const import (
    CONF_API_SECRET,
    CONF_BREAKER_ID,
    CONF_CLIENT_ID,
    CONF_EATON_ACCOUNT_PASSWORD,
    CONF_EATON_ACCOUNT_USERNAME,
    CONF_ORGANIZATION_SECRET,
)
from .coordinator import EatonAbleEdgeCoordinator

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.BINARY_SENSOR]

type EatonAbleEdgeConfigEntry = ConfigEntry[EatonAbleEdgeCoordinator]


async def async_setup_entry(
    hass: HomeAssistant, entry: EatonAbleEdgeConfigEntry
) -> bool:
    """Set up Eaton AbleEdge Breakers from a config entry."""
    session = async_get_clientsession(hass)
    client = EatonAbleEdgeApiClient(
        session=session,
        api_key=entry.data[CONF_API_KEY],
        api_secret=entry.data[CONF_API_SECRET],
        client_id=entry.data[CONF_CLIENT_ID],
        eaton_account_username=entry.data[CONF_EATON_ACCOUNT_USERNAME],
        eaton_account_password=entry.data[CONF_EATON_ACCOUNT_PASSWORD],
        organization_secret=entry.data[CONF_ORGANIZATION_SECRET],
    )

    coordinator = EatonAbleEdgeCoordinator(
        hass, entry, client, entry.data[CONF_BREAKER_ID]
    )
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(
    hass: HomeAssistant, entry: EatonAbleEdgeConfigEntry
) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
