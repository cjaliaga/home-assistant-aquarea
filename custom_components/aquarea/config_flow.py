"""Config flow for Aquarea Smart Cloud integration."""
from __future__ import annotations

import logging
from typing import Any, Optional

import aioaquarea
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.aiohttp_client import async_create_clientsession

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {vol.Required(CONF_USERNAME): str, vol.Required(CONF_PASSWORD): str}
)


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Aquarea Smart Cloud."""

    VERSION = 1

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.info = {}
        self._api: aioaquarea.Client = None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        if user_input is None:
            return self.async_show_form(
                step_id="user", data_schema=STEP_USER_DATA_SCHEMA
            )

        errors = {}

        sess = async_create_clientsession(self.hass)
        self._api = aioaquarea.Client(
            sess, user_input[CONF_USERNAME], user_input[CONF_PASSWORD]
        )
        await self.async_set_unique_id(str.lower(user_input[CONF_USERNAME]))
        self._abort_if_unique_id_configured()

        try:
            await self._api.login()
        except CannotConnect:
            errors["base"] = "cannot_connect"
        except aioaquarea.AuthenticationError:
            errors["base"] = "invalid_auth"
        except Exception:  # pylint: disable=broad-except
            _LOGGER.exception("Unexpected exception")
            errors["base"] = "unknown"
        else:
            return self.async_create_entry(
                title=user_input[CONF_USERNAME], data=user_input
            )

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""
