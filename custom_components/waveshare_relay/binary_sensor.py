"""Binary sensor platform for Waveshare Relay digital inputs."""

import logging
from datetime import timedelta

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, CONF_ENABLE_INPUTS, CONF_NUM_CHANNELS
from .utils import read_discrete_inputs, read_device_address, read_software_version

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(seconds=5)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Waveshare digital input binary sensors from a config entry."""
    if not config_entry.data.get(CONF_ENABLE_INPUTS, True):
        return

    ip_address = config_entry.data["ip_address"]
    port = config_entry.data["port"]
    device_name = config_entry.data["device_name"]
    num_channels = config_entry.data.get(CONF_NUM_CHANNELS, 8)

    entities = [
        WaveshareDigitalInput(hass, ip_address, port, device_name, ch)
        for ch in range(num_channels)
    ]
    async_add_entities(entities, update_before_add=True)


class WaveshareDigitalInput(BinarySensorEntity):
    """Binary sensor for a single Waveshare digital input."""

    _attr_icon = "mdi:electric-switch"

    def __init__(self, hass, ip_address, port, device_name, channel):
        self.hass = hass
        self._ip_address = ip_address
        self._port = port
        self._device_name = device_name
        self._channel = channel
        self._attr_is_on = None

    @property
    def unique_id(self):
        return f"{DOMAIN}_{self._ip_address}_{self._channel}_input"

    @property
    def name(self):
        return f"{self._device_name} Input {self._channel + 1}"

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._ip_address)},
            "name": self._device_name,
            "model": "Modbus POE ETH Relay",
            "manufacturer": "Waveshare",
        }

    async def async_update(self):
        """Poll the device for current digital input states."""
        states = await self.hass.async_add_executor_job(
            read_discrete_inputs, self._ip_address, self._port
        )
        if states is not None and self._channel < len(states):
            self._attr_is_on = states[self._channel]
        else:
            _LOGGER.warning(
                "Failed to read digital input %d from %s:%d",
                self._channel, self._ip_address, self._port,
            )
