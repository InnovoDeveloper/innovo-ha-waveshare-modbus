"""Binary sensor platform for Waveshare Relay digital inputs."""

from __future__ import annotations

import logging

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, CONF_ENABLE_INPUTS, CONF_NUM_CHANNELS
from .coordinator import WaveshareDIUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Waveshare digital input binary sensors from a config entry."""
    if not config_entry.data.get(CONF_ENABLE_INPUTS, True):
        return

    coordinator: WaveshareDIUpdateCoordinator = hass.data[DOMAIN][
        config_entry.entry_id
    ]["di_coordinator"]

    ip_address = config_entry.data["ip_address"]
    device_name = config_entry.data["device_name"]
    num_channels = config_entry.data.get(CONF_NUM_CHANNELS, 8)

    entities = [
        WaveshareDigitalInput(coordinator, ip_address, device_name, ch)
        for ch in range(num_channels)
    ]
    async_add_entities(entities)


class WaveshareDigitalInput(
    CoordinatorEntity[WaveshareDIUpdateCoordinator], BinarySensorEntity
):
    """Binary sensor for a single Waveshare digital input."""

    _attr_icon = "mdi:electric-switch"
    _attr_should_poll = False

    def __init__(
        self,
        coordinator: WaveshareDIUpdateCoordinator,
        ip_address: str,
        device_name: str,
        channel: int,
    ) -> None:
        super().__init__(coordinator)
        self._ip_address = ip_address
        self._device_name = device_name
        self._channel = channel

    @property
    def unique_id(self) -> str:
        return f"{DOMAIN}_{self._ip_address}_{self._channel}_input"

    @property
    def name(self) -> str:
        return f"{self._device_name} Input {self._channel + 1}"

    @property
    def device_info(self) -> dict:
        return {
            "identifiers": {(DOMAIN, self._ip_address)},
            "name": self._device_name,
            "model": "Modbus POE ETH Relay",
            "manufacturer": "Waveshare",
        }

    @property
    def is_on(self) -> bool | None:
        data = self.coordinator.data
        if data is None or self._channel >= len(data):
            return None
        return data[self._channel]
