"""The Waveshare Relay integration."""

import logging

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from .const import DOMAIN, CONF_ENABLE_INPUTS, CONF_ENABLE_SWITCHES, CONF_DI_TOGGLE_MODE
from .utils import set_di_toggle_mode

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Waveshare Relay from a config entry."""
    platforms = []
    if entry.data.get(CONF_ENABLE_SWITCHES, True):
        platforms.append("switch")
    if entry.data.get(CONF_ENABLE_INPUTS, True):
        platforms.append("binary_sensor")

    if platforms:
        await hass.config_entries.async_forward_entry_setups(entry, platforms)

    # Configure DI toggle mode if enabled
    if entry.data.get(CONF_DI_TOGGLE_MODE, False):
        ip = entry.data["ip_address"]
        port = entry.data["port"]
        num_ch = entry.data.get("num_channels", 8)
        _LOGGER.info("Setting DI toggle mode for %s:%d (%d channels)", ip, port, num_ch)
        await hass.async_add_executor_job(set_di_toggle_mode, ip, port, num_ch)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    platforms = []
    if entry.data.get(CONF_ENABLE_SWITCHES, True):
        platforms.append("switch")
    if entry.data.get(CONF_ENABLE_INPUTS, True):
        platforms.append("binary_sensor")

    unload_ok = True
    for platform in platforms:
        unload_ok = unload_ok and await hass.config_entries.async_forward_entry_unload(
            entry, platform
        )
    return unload_ok
