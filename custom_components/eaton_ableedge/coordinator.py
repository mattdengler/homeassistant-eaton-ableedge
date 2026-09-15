"""DataUpdateCoordinator for the Eaton AbleEdge Breakers integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import (
    EatonAbleEdgeApiClient,
    EatonAbleEdgeAuthError,
    EatonAbleEdgeConnectionError,
)
from .const import DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)


class EatonAbleEdgeCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator to manage fetching Eaton AbleEdge breaker data."""

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        client: EatonAbleEdgeApiClient,
        breaker_id: str,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            config_entry=config_entry,
            update_interval=DEFAULT_SCAN_INTERVAL,
        )
        self.client = client
        self.breaker_id = breaker_id

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch the latest breaker data from Eaton."""
        try:
            return await self.client.async_get_breaker_data(self.breaker_id)
        except EatonAbleEdgeAuthError as err:
            raise ConfigEntryAuthFailed(str(err)) from err
        except EatonAbleEdgeConnectionError as err:
            raise UpdateFailed(str(err)) from err
