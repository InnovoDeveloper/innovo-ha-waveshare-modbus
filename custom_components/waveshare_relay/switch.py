"""Switch platform for Waveshare Relay outputs."""

import logging
from datetime import timedelta

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, CONF_ENABLE_SWITCHES, CONF_NUM_CHANNELS
from .utils import read_coils, write_single_coil, read_device_address, read_software_version

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(seconds=5)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Waveshare relay switches from a config entry."""
    if not config_entry.data.get(CONF_ENABLE_SWITCHES, True):
        return

    ip_address = config_entry.data["ip_address"]
    port = config_entry.data["port"]
    device_name = config_entry.data["device_name"]
    num_channels = config_entry.data.get(CONF_NUM_CHANNELS, 8)

    switches = [
        WaveshareRelaySwitch(hass, ip_address, port, device_name, ch)
        for ch in range(num_channels)
    ]
    async_add_entities(switches, update_before_add=True)


class WaveshareRelaySwitch(SwitchEntity):
    """Switch for a single Waveshare relay output."""

    _attr_icon = "mdi:electric-switch-closed"

    def __init__(self, hass, ip_address, port, device_name, channel):
        self.hass = hass
        self._ip_address = ip_address
        self._port = port
        self._device_name = device_name
        self._channel = channel
        self._attr_is_on = False

    @property
    def unique_id(self):
        return f"{DOMAIN}_{self._ip_address}_{self._channel}_switch"

    @property
    def name(self):
        return f"{self._device_name} Relay {self._channel + 1}"

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._ip_address)},
            "name": self._device_name,
            "model": "Modbus POE ETH Relay",
            "manufacturer": "Waveshare",
        }

    async def async_turn_on(self, **kwargs):
        """Turn the relay ON."""
        success = await self.hass.async_add_executor_job(
            write_single_coil, self._ip_address, self._port, self._channel, True
        )
        if success:
            self._attr_is_on = True
            self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        """Turn the relay OFF."""
        success = await self.hass.async_add_executor_job(
            write_single_coil, self._ip_address, self._port, self._channel, False
        )
        if success:
            self._attr_is_on = False
            self.async_write_ha_state()

    async def async_update(self):
        """Poll the device for current relay states."""
        states = await self.hass.async_add_executor_job(
            read_coils, self._ip_address, self._port
        )
        if states is not None and self._channel < len(states):
            self._attr_is_on = states[self._channel]
        else:
            _LOGGER.warning(
                "Failed to read relay %d from %s:%d",
                self._channel, self._ip_address, self._port,
            )
