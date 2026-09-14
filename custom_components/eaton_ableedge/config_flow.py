"""Config flow for the Eaton AbleEdge Breakers integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_API_KEY
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import (
    EatonAbleEdgeApiClient,
    EatonAbleEdgeAuthError,
    EatonAbleEdgeConnectionError,
)
from .const import (
    CONF_API_SECRET,
    CONF_BREAKER_ID,
    CONF_CLIENT_ID,
    CONF_EATON_ACCOUNT_PASSWORD,
    CONF_EATON_ACCOUNT_USERNAME,
    CONF_ORGANIZATION_SECRET,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_API_KEY): str,
        vol.Required(CONF_API_SECRET): str,
        vol.Required(CONF_CLIENT_ID): str,
        vol.Required(CONF_EATON_ACCOUNT_USERNAME): str,
        vol.Required(CONF_EATON_ACCOUNT_PASSWORD): str,
        vol.Required(CONF_ORGANIZATION_SECRET): str,
        vol.Required(CONF_BREAKER_ID): str,
    }
)

# Fields that should be rendered as password inputs in the config flow UI.
_PASSWORD_FIELDS = {
    CONF_API_SECRET,
    CONF_EATON_ACCOUNT_PASSWORD,
    CONF_ORGANIZATION_SECRET,
}


def _build_selector_schema() -> vol.Schema:
    """Build the schema, marking secret fields as password inputs."""
    try:
        from homeassistant.helpers import selector
    except ImportError:  # pragma: no cover - very old HA fallback
        return STEP_USER_DATA_SCHEMA

    schema: dict[Any, Any] = {}
    for key, validator in STEP_USER_DATA_SCHEMA.schema.items():
        if str(key) in _PASSWORD_FIELDS:
            schema[key] = selector.TextSelector(
                selector.TextSelectorConfig(type=selector.TextSelectorType.PASSWORD)
            )
        else:
            schema[key] = validator
    return vol.Schema(schema)


# Computed once at module load time since the underlying schema and password
# field set are both static.
_SELECTOR_SCHEMA = _build_selector_schema()


async def _async_validate_input(
    hass: HomeAssistant, data: dict[str, Any]
) -> None:
    """Validate the user input allows us to authenticate with Eaton."""
    session = async_get_clientsession(hass)
    client = EatonAbleEdgeApiClient(
        session=session,
        api_key=data[CONF_API_KEY],
        api_secret=data[CONF_API_SECRET],
        client_id=data[CONF_CLIENT_ID],
        eaton_account_username=data[CONF_EATON_ACCOUNT_USERNAME],
        eaton_account_password=data[CONF_EATON_ACCOUNT_PASSWORD],
        organization_secret=data[CONF_ORGANIZATION_SECRET],
    )
    await client.async_validate_credentials()
    await client.async_get_breaker_data(data[CONF_BREAKER_ID])


class EatonAbleEdgeConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Eaton AbleEdge Breakers."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            await self.async_set_unique_id(user_input[CONF_BREAKER_ID])
            self._abort_if_unique_id_configured()

            try:
                await _async_validate_input(self.hass, user_input)
            except EatonAbleEdgeAuthError:
                errors["base"] = "invalid_auth"
            except EatonAbleEdgeConnectionError:
                errors["base"] = "cannot_connect"
            except Exception:  # noqa: BLE001 pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception during config flow")
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(
                    title=f"Eaton Breaker {user_input[CONF_BREAKER_ID]}",
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=_SELECTOR_SCHEMA,
            errors=errors,
        )

    async def async_step_reauth(
        self, entry_data: dict[str, Any]
    ) -> ConfigFlowResult:
        """Handle reauthentication when Eaton credentials expire or are revoked."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Confirm reauthentication with updated credentials."""
        errors: dict[str, str] = {}
        reauth_entry = self._get_reauth_entry()

        if user_input is not None:
            data = {**reauth_entry.data, **user_input}
            try:
                await _async_validate_input(self.hass, data)
            except EatonAbleEdgeAuthError:
                errors["base"] = "invalid_auth"
            except EatonAbleEdgeConnectionError:
                errors["base"] = "cannot_connect"
            except Exception:  # noqa: BLE001 pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception during reauth")
                errors["base"] = "unknown"
            else:
                return self.async_update_reload_and_abort(
                    reauth_entry, data=data
                )

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=_SELECTOR_SCHEMA,
            errors=errors,
        )
