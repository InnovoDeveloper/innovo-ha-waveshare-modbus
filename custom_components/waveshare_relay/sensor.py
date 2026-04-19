"""Sensor platform for Waveshare Relay device diagnostics."""

import logging
from datetime import timedelta

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, CONF_EXTENDED_MODE
from .utils import read_software_version, read_device_address

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(minutes=5)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up diagnostic sensors (extended mode only)."""
    if not config_entry.data.get(CONF_EXTENDED_MODE, False):
        return

    ip_address = config_entry.data["ip_address"]
    port = config_entry.data["port"]
    device_name = config_entry.data["device_name"]

    async_add_entities(
        [
            WavshareFirmwareSensor(hass, ip_address, port, device_name),
            WaveshareAddressSensor(hass, ip_address, port, device_name),
        ],
        update_before_add=True,
    )


class WavshareFirmwareSensor(SensorEntity):
    """Sensor showing the device firmware version."""

    _attr_icon = "mdi:information-outline"
    _attr_entity_category = "diagnostic"

    def __init__(self, hass, ip_address, port, device_name):
        self.hass = hass
        self._ip_address = ip_address
        self._port = port
        self._device_name = device_name

    @property
    def unique_id(self):
        return f"{DOMAIN}_{self._ip_address}_firmware"

    @property
    def name(self):
        return f"{self._device_name} Firmware"

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._ip_address)},
            "name": self._device_name,
            "model": "Modbus POE ETH Relay",
            "manufacturer": "Waveshare",
        }

    async def async_update(self):
        version = await self.hass.async_add_executor_job(
            read_software_version, self._ip_address, self._port
        )
        self._attr_native_value = version if version else "unknown"


class WaveshareAddressSensor(SensorEntity):
    """Sensor showing the Modbus device address."""

    _attr_icon = "mdi:identifier"
    _attr_entity_category = "diagnostic"

    def __init__(self, hass, ip_address, port, device_name):
        self.hass = hass
        self._ip_address = ip_address
        self._port = port
        self._device_name = device_name

    @property
    def unique_id(self):
        return f"{DOMAIN}_{self._ip_address}_device_address"

    @property
    def name(self):
        return f"{self._device_name} Modbus Address"

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._ip_address)},
            "name": self._device_name,
            "model": "Modbus POE ETH Relay",
            "manufacturer": "Waveshare",
        }

    async def async_update(self):
        addr = await self.hass.async_add_executor_job(
            read_device_address, self._ip_address, self._port
        )
        self._attr_native_value = addr if addr is not None else "unknown"
