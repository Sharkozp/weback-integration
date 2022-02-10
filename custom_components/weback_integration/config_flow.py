"""Config flow for Weback Integration for Hass integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError
from weback_unofficial.client import WebackApi

from .const import (
    DOMAIN,
    DOMAIN_TITLE,
    CONF_PHONE_CODE,
    CONF_USERNAME,
    CONF_PASSWORD
)

_LOGGER = logging.getLogger(__name__)

STEP_INIT_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_PHONE_CODE): str,
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): cv.string,
    }
)


class WebackConfigFlow:
    def __init__(self):
        self.weback_api = None

    async def authenticate(self, phone_code: str, username: str, password: str) -> bool:
        """Test if we can authenticate with the phone_code."""

        try:
            self.weback_api = WebackApi(username, password, phone_code)
            return True
        except Exception:  # pylint: disable=broad-except
            _LOGGER.exception("Unexpected exception")
            return False

    def get_weback_api(self) -> WebackApi:
        return self.weback_api


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect.

    Data has the keys from STEP_INIT_DATA_SCHEMA with values provided by the user.
    """
    # TODO validate the data can be used to set up a connection.

    weback_config_flow = WebackConfigFlow()

    if not await weback_config_flow.authenticate(
            data[CONF_USERNAME],
            data[CONF_PASSWORD],
            data[CONF_PHONE_CODE]
    ):
        raise InvalidAuth

    # If you cannot connect:
    # throw CannotConnect
    # If the authentication is wrong:
    # InvalidAuth

    # Return info that you want to store in the config entry.
    return {"title": DOMAIN_TITLE}


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Weback Integration."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Handle the initial step."""
        if user_input is None:
            return self.async_show_form(step_id="user", data_schema=STEP_INIT_DATA_SCHEMA)

        errors = {}

        try:
            info = await validate_input(self.hass, user_input)
        except CannotConnect:
            errors["base"] = "cannot_connect"
        except InvalidAuth:
            errors["base"] = "invalid_auth"
        except Exception:  # pylint: disable=broad-except
            _LOGGER.exception("Unexpected exception")
            errors["base"] = "unknown"
        else:
            return self.async_create_entry(title=info["title"], data=user_input)

        return self.async_show_form(step_id="user", data_schema=STEP_INIT_DATA_SCHEMA, errors=errors)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Define the config flow to handle options."""
        return ConfigOptionsFlowHandler(config_entry)


class ConfigOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle a Weback Integration options flow."""

    def __init__(self, config_entry):
        """Initialize Weback Integration options flow."""
        self.config_entry = config_entry

    async def async_step_init(self,_user_input=None):
        """Manage the options."""
        return await self.async_step_user()

    async def async_step_user(self, user_input=None):
        """Handle a flow initialized by the user."""
        if user_input is not None:
            option_schema = vol.Schema(
                {
                    vol.Required(CONF_PHONE_CODE, default=user_input[CONF_PHONE_CODE]): str,
                    vol.Required(CONF_USERNAME, default=user_input[CONF_USERNAME]): str,
                    vol.Required(CONF_PASSWORD): cv.string
                }
            )
            return self.async_show_form(step_id="user", data_schema=option_schema)
        elif self.config_entry.data is not None:
            option_schema = vol.Schema(
                {
                    vol.Required(CONF_PHONE_CODE, default=self.config_entry.data[CONF_PHONE_CODE]): str,
                    vol.Required(CONF_USERNAME, default=self.config_entry.data[CONF_USERNAME]): str,
                    vol.Required(CONF_PASSWORD, default=self.config_entry.data[CONF_PASSWORD]): cv.string
                }
            )
            return self.async_show_form(step_id="user", data_schema=option_schema)
        return self.async_show_form(step_id="user", data_schema=STEP_INIT_DATA_SCHEMA)


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""
