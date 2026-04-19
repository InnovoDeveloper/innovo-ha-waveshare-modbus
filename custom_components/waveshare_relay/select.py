"""Select platform for Waveshare Relay DI control mode per channel."""

import logging
from datetime import timedelta

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DOMAIN,
    CONF_EXTENDED_MODE,
    CONF_ENABLE_INPUTS,
    CONF_NUM_CHANNELS,
    DI_MODE_OPTIONS,
    DI_MODE_LABELS,
)
from .utils import read_di_mode, set_di_mode

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(seconds=30)

# Reverse map: int -> string key
_MODE_INT_TO_KEY = {v: k for k, v in DI_MODE_OPTIONS.items()}


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up DI mode selects (extended mode only)."""
    if not config_entry.data.get(CONF_EXTENDED_MODE, False):
        return
    if not config_entry.data.get(CONF_ENABLE_INPUTS, True):
        return

    ip_address = config_entry.data["ip_address"]
    port = config_entry.data["port"]
    device_name = config_entry.data["device_name"]
    num_channels = config_entry.data.get(CONF_NUM_CHANNELS, 8)

    entities = [
        WavshareDIModeSelect(hass, ip_address, port, device_name, ch)
        for ch in range(num_channels)
    ]
    async_add_entities(entities, update_before_add=True)


class WavshareDIModeSelect(SelectEntity):
    """Select entity for configuring a single DI channel's control mode."""

    _attr_icon = "mdi:swap-horizontal"

    def __init__(self, hass, ip_address, port, device_name, channel):
        self.hass = hass
        self._ip_address = ip_address
        self._port = port
        self._device_name = device_name
        self._channel = channel
        self._attr_current_option = "normal"
        self._attr_options = list(DI_MODE_LABELS.values())

    @property
    def unique_id(self):
        return f"{DOMAIN}_{self._ip_address}_{self._channel}_di_mode"

    @property
    def name(self):
        return f"{self._device_name} DI {self._channel + 1} Mode"

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._ip_address)},
            "name": self._device_name,
            "model": "Modbus POE ETH Relay",
            "manufacturer": "Waveshare",
        }

    async def async_select_option(self, option: str) -> None:
        """Set the DI mode on the device."""
        # Find the key from the label
        key = next(
            (k for k, label in DI_MODE_LABELS.items() if label == option), None
        )
        if key is None:
            _LOGGER.error("Unknown DI mode option: %s", option)
            return

        mode_int = DI_MODE_OPTIONS[key]
        success = await self.hass.async_add_executor_job(
            set_di_mode, self._ip_address, self._port, self._channel, mode_int
        )
        if success:
            self._attr_current_option = option
            self.async_write_ha_state()

    async def async_update(self):
        """Read current DI mode from device."""
        mode_int = await self.hass.async_add_executor_job(
            read_di_mode, self._ip_address, self._port, self._channel
        )
        if mode_int is not None:
            key = _MODE_INT_TO_KEY.get(mode_int, "normal")
            self._attr_current_option = DI_MODE_LABELS.get(key, "Normal (command only)")
