"""Number platform for Waveshare Relay flash/pulse duration per channel."""

import logging

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .const import DOMAIN, CONF_EXTENDED_MODE, CONF_ENABLE_SWITCHES, CONF_NUM_CHANNELS

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up flash duration numbers (extended mode only)."""
    if not config_entry.data.get(CONF_EXTENDED_MODE, False):
        return
    if not config_entry.data.get(CONF_ENABLE_SWITCHES, True):
        return

    ip_address = config_entry.data["ip_address"]
    port = config_entry.data["port"]
    device_name = config_entry.data["device_name"]
    num_channels = config_entry.data.get(CONF_NUM_CHANNELS, 8)

    entities = [
        WaveshareFlashDuration(ip_address, device_name, ch)
        for ch in range(num_channels)
    ]
    async_add_entities(entities)


class WaveshareFlashDuration(RestoreEntity, NumberEntity):
    """Number entity for configuring flash/pulse duration per relay channel."""

    _attr_icon = "mdi:timer-outline"
    _attr_mode = NumberMode.SLIDER
    _attr_native_min_value = 0.1
    _attr_native_max_value = 3276.7  # 0x7FFF * 100ms
    _attr_native_step = 0.1
    _attr_native_unit_of_measurement = "s"
    _attr_device_class = "duration"

    def __init__(self, ip_address, device_name, channel):
        self._ip_address = ip_address
        self._device_name = device_name
        self._channel = channel
        self._attr_native_value = 1.0  # default 1 second

    @property
    def unique_id(self):
        return f"{DOMAIN}_{self._ip_address}_{self._channel}_flash_duration"

    @property
    def name(self):
        return f"{self._device_name} Relay {self._channel + 1} Pulse Duration"

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._ip_address)},
            "name": self._device_name,
            "model": "Modbus POE ETH Relay",
            "manufacturer": "Waveshare",
        }

    async def async_added_to_hass(self):
        """Restore previous value on restart."""
        last_state = await self.async_get_last_state()
        if last_state and last_state.state not in (None, "unknown", "unavailable"):
            try:
                self._attr_native_value = float(last_state.state)
            except ValueError:
                self._attr_native_value = 1.0

    async def async_set_native_value(self, value: float) -> None:
        """Set the flash duration."""
        self._attr_native_value = value
        self.async_write_ha_state()
