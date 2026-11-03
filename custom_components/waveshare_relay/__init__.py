"""The Waveshare Relay integration."""

import logging
from datetime import timedelta

import voluptuous as vol
from homeassistant.core import HomeAssistant, ServiceCall, callback
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.event import async_track_time_interval

from .const import (
    DOMAIN,
    CONF_ENABLE_INPUTS,
    CONF_ENABLE_SWITCHES,
    CONF_DI_TOGGLE_MODE,
    CONF_EXTENDED_MODE,
    CONF_NUM_CHANNELS,
    DI_MODE_TOGGLE,
)
from .coordinator import WaveshareDIUpdateCoordinator
from .utils import ensure_di_modes, toggle_relay, toggle_all_relays

_LOGGER = logging.getLogger(__name__)

DI_MODE_CHECK_INTERVAL = timedelta(seconds=30)

# Standard mode platforms
STANDARD_PLATFORMS = {
    "switch": CONF_ENABLE_SWITCHES,
    "binary_sensor": CONF_ENABLE_INPUTS,
}

# Extended mode adds these
EXTENDED_PLATFORMS = ["button", "number", "select", "sensor"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Waveshare Relay from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    ip_address = entry.data["ip_address"]
    port = entry.data["port"]
    num_channels = entry.data.get(CONF_NUM_CHANNELS, 8)

    di_coordinator: WaveshareDIUpdateCoordinator | None = None
    if entry.data.get(CONF_ENABLE_INPUTS, True):
        di_coordinator = WaveshareDIUpdateCoordinator(
            hass, ip_address, port, num_channels
        )
        await di_coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = {
        "config": entry.data,
        "di_coordinator": di_coordinator,
    }

    # Determine platforms to load
    platforms = []
    for platform, conf_key in STANDARD_PLATFORMS.items():
        if entry.data.get(conf_key, True):
            platforms.append(platform)

    if entry.data.get(CONF_EXTENDED_MODE, False):
        platforms.extend(EXTENDED_PLATFORMS)

    if platforms:
        await hass.config_entries.async_forward_entry_setups(entry, platforms)

    # Configure DI toggle mode if enabled. The board can drop the mode (a timeout
    # mid-write, or a reboot), and then inputs stop driving their relays until the
    # next HA start. Check it every 30s and as soon as the board answers again.
    if entry.data.get(CONF_DI_TOGGLE_MODE, False):
        _LOGGER.info(
            "Setting DI toggle mode for %s:%d (%d channels)",
            ip_address, port, num_channels,
        )

        async def _enforce_di_mode(_now=None) -> None:
            fixed = await hass.async_add_executor_job(
                ensure_di_modes, ip_address, port, DI_MODE_TOGGLE, num_channels
            )
            if fixed:
                _LOGGER.warning(
                    "DI mode had drifted on %s:%d inputs %s; set back to toggle",
                    ip_address, port, [ch + 1 for ch in fixed],
                )

        await _enforce_di_mode()
        entry.async_on_unload(
            async_track_time_interval(hass, _enforce_di_mode, DI_MODE_CHECK_INTERVAL)
        )

        if di_coordinator is not None:
            board_ok = di_coordinator.last_update_success

            @callback
            def _on_di_update() -> None:
                nonlocal board_ok
                if di_coordinator.last_update_success and not board_ok:
                    hass.async_create_task(_enforce_di_mode())
                board_ok = di_coordinator.last_update_success

            entry.async_on_unload(di_coordinator.async_add_listener(_on_di_update))

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
