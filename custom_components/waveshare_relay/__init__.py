"""The Waveshare Relay integration."""

import logging

import voluptuous as vol
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers import config_validation as cv

from .const import (
    DOMAIN,
    CONF_ENABLE_INPUTS,
    CONF_ENABLE_SWITCHES,
    CONF_DI_TOGGLE_MODE,
    CONF_EXTENDED_MODE,
)
from .utils import set_di_toggle_mode, toggle_relay, toggle_all_relays

_LOGGER = logging.getLogger(__name__)

# Standard mode platforms
STANDARD_PLATFORMS = {
    "switch": CONF_ENABLE_SWITCHES,
    "binary_sensor": CONF_ENABLE_INPUTS,
}

# Extended mode adds these
EXTENDED_PLATFORMS = ["button", "number", "select", "sensor"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Waveshare Relay from a config entry."""
    # Store entry data for service calls
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = entry.data

    # Determine platforms to load
    platforms = []
    for platform, conf_key in STANDARD_PLATFORMS.items():
        if entry.data.get(conf_key, True):
            platforms.append(platform)

    if entry.data.get(CONF_EXTENDED_MODE, False):
        platforms.extend(EXTENDED_PLATFORMS)

    if platforms:
        await hass.config_entries.async_forward_entry_setups(entry, platforms)

    # Configure DI toggle mode if enabled
    if entry.data.get(CONF_DI_TOGGLE_MODE, False):
        ip = entry.data["ip_address"]
        port = entry.data["port"]
        num_ch = entry.data.get("num_channels", 8)
        _LOGGER.info("Setting DI toggle mode for %s:%d (%d channels)", ip, port, num_ch)
        await hass.async_add_executor_job(set_di_toggle_mode, ip, port, num_ch)

    # Register services (once per integration, not per entry)
    if not hass.services.has_service(DOMAIN, "toggle_relay"):
        _register_services(hass)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    platforms = []
    for platform, conf_key in STANDARD_PLATFORMS.items():
        if entry.data.get(conf_key, True):
            platforms.append(platform)
    if entry.data.get(CONF_EXTENDED_MODE, False):
        platforms.extend(EXTENDED_PLATFORMS)

    unload_ok = True
    for platform in platforms:
        unload_ok = unload_ok and await hass.config_entries.async_forward_entry_unload(
            entry, platform
        )

    # Remove stored data
    hass.data[DOMAIN].pop(entry.entry_id, None)
    if not hass.data[DOMAIN]:
        hass.data.pop(DOMAIN, None)

    return unload_ok


def _register_services(hass: HomeAssistant) -> None:
    """Register waveshare_relay services."""

    async def handle_toggle_relay(call: ServiceCall) -> None:
        """Toggle a single relay by channel number."""
        ip = call.data["ip_address"]
        port = call.data["port"]
        channel = call.data["channel"]
        await hass.async_add_executor_job(toggle_relay, ip, port, channel)

    async def handle_toggle_all(call: ServiceCall) -> None:
        """Toggle all relays at once."""
        ip = call.data["ip_address"]
        port = call.data["port"]
        await hass.async_add_executor_job(toggle_all_relays, ip, port)

    hass.services.async_register(
        DOMAIN,
        "toggle_relay",
        handle_toggle_relay,
        schema=vol.Schema(
            {
                vol.Required("ip_address"): cv.string,
                vol.Required("port"): cv.port,
                vol.Required("channel"): vol.All(
                    vol.Coerce(int), vol.Range(min=0, max=7)
                ),
            }
        ),
    )

    hass.services.async_register(
        DOMAIN,
        "toggle_all",
        handle_toggle_all,
        schema=vol.Schema(
            {
                vol.Required("ip_address"): cv.string,
                vol.Required("port"): cv.port,
            }
        ),
    )
