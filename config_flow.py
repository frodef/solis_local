"""Config flow for solis_local integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries

# from homeassistant import data_entry_flow
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN
from .solis_local import AuthorizationFailed, ConnectionFailed, SolisLocalHttpAPI

_LOGGER = logging.getLogger(__name__)

# XTODO fix defaults
STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required("host", default="192.168.1.166"): str,
        vol.Required("username", default="admin"): str,
        vol.Required("password", default="gbgfvf"): str,
    }
)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """
    api = SolisLocalHttpAPI(data)
    info = await api.load_status()
    #    raise InvalidAuth
    _LOGGER.debug("info: %s", info)

    # Return info that you want to store in the config entry.
    return info


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for solis_local."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        if user_input is None:
            return self.async_show_form(
                step_id="user",
                data_schema=STEP_USER_DATA_SCHEMA,
                description_placeholders={"host": "message"},
            )

        errors = {}

        try:
            info = await validate_input(self.hass, user_input)
            if info["webdata_sn"]:
                await self.async_set_unique_id(info["webdata_sn"])
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=f"Solis Local {info['webdata_sn']}", data=info
                )
        except ConnectionFailed:
            errors["base"] = "cannot_connect"
        except AuthorizationFailed:
            errors["base"] = "invalid_auth"
        else:
            return self.async_create_entry(
                title="solis" + info["webdata_sn"], data=user_input
            )
        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )
