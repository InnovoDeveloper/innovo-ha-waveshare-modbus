"""Config flow for Waveshare Relay integration."""

import logging
import socket

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.exceptions import HomeAssistantError

from .const import (
    DOMAIN,
    CONF_ENABLE_INPUTS,
    CONF_ENABLE_SWITCHES,
    CONF_NUM_CHANNELS,
    CONF_DI_TOGGLE_MODE,
)

_LOGGER = logging.getLogger(__name__)

DATA_SCHEMA = vol.Schema(
    {
        vol.Required("ip_address"): str,
        vol.Required("port", default=4196): vol.Coerce(int),
        vol.Required("device_name", default="Waveshare Relay"): str,
        vol.Required(CONF_NUM_CHANNELS, default=8): vol.In({8: "8 Channels", 4: "4 Channels", 2: "2 Channels"}),
        vol.Required(CONF_ENABLE_SWITCHES, default=True): bool,
        vol.Required(CONF_ENABLE_INPUTS, default=True): bool,
        vol.Optional(CONF_DI_TOGGLE_MODE, default=False): bool,
    }
)


class WaveshareRelayConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Waveshare Relay."""

    VERSION = 2

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}
        if user_input is not None:
            try:
                await self.hass.async_add_executor_job(
                    self._validate_connection,
                    user_input["ip_address"],
                    user_input["port"],
                )
                # Set unique ID based on IP to prevent duplicate entries
                await self.async_set_unique_id(f"waveshare_{user_input['ip_address']}")
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=user_input["device_name"], data=user_input
                )
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected error during config flow")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user", data_schema=DATA_SCHEMA, errors=errors
        )

    @staticmethod
    def _validate_connection(ip_address: str, port: int) -> None:
        """Validate we can reach the Waveshare device."""
        try:
            with socket.create_connection((ip_address, port), timeout=5):
                pass
        except (OSError, socket.timeout) as e:
            raise CannotConnect(
                f"Cannot connect to {ip_address}:{port}"
            ) from e


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""
