"""Diagnostics support for the Eaton AbleEdge Breakers integration."""
from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.core import HomeAssistant

from . import EatonAbleEdgeConfigEntry
from .const import REDACT_KEYS


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: EatonAbleEdgeConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry.

    All configured secrets and any tokens generated at runtime (OAuth token,
    session access token, organization token) are redacted.
    """
    coordinator = entry.runtime_data
    client = coordinator.client

    return {
        "entry_data": async_redact_data(dict(entry.data), REDACT_KEYS),
        "runtime_tokens": async_redact_data(
            {
                "oauth_token": client._oauth_token.value,  # noqa: SLF001
                "session_access_token": client._session_access_token,  # noqa: SLF001
                "organization_token": client._organization_token,  # noqa: SLF001
            },
            REDACT_KEYS,
        ),
        "breaker_data": async_redact_data(coordinator.data or {}, REDACT_KEYS),
    }
