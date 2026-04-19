"""Button platform for Waveshare Relay flash/pulse actions."""

import logging

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, CONF_EXTENDED_MODE, CONF_ENABLE_SWITCHES, CONF_NUM_CHANNELS
from .utils import flash_relay_on, toggle_relay, toggle_all_relays, control_all_relays

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up flash/pulse buttons and master controls (extended mode only)."""
    if not config_entry.data.get(CONF_EXTENDED_MODE, False):
        return
    if not config_entry.data.get(CONF_ENABLE_SWITCHES, True):
        return

    ip_address = config_entry.data["ip_address"]
    port = config_entry.data["port"]
    device_name = config_entry.data["device_name"]
    num_channels = config_entry.data.get(CONF_NUM_CHANNELS, 8)

    entities = []

    # Per-channel pulse buttons
    for ch in range(num_channels):
        entities.append(
            WaveshareFlashButton(hass, ip_address, port, device_name, ch)
        )

    # Master controls
    entities.append(WaveshareAllOnButton(hass, ip_address, port, device_name))
    entities.append(WaveshareAllOffButton(hass, ip_address, port, device_name))
    entities.append(WaveshareToggleAllButton(hass, ip_address, port, device_name))

    async_add_entities(entities)


class WaveshareFlashButton(ButtonEntity):
    """Button that pulses a relay ON for the configured duration, then auto-OFF."""

    _attr_icon = "mdi:flash"

    def __init__(self, hass, ip_address, port, device_name, channel):
        self.hass = hass
        self._ip_address = ip_address
        self._port = port
        self._device_name = device_name
        self._channel = channel

    @property
    def unique_id(self):
        return f"{DOMAIN}_{self._ip_address}_{self._channel}_flash"

    @property
    def name(self):
        return f"{self._device_name} Relay {self._channel + 1} Pulse"

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._ip_address)},
            "name": self._device_name,
            "model": "Modbus POE ETH Relay",
            "manufacturer": "Waveshare",
        }

    async def async_press(self) -> None:
        """Fire a pulse: relay ON for configured duration, then auto-OFF."""
        # Look up the duration from the corresponding number entity
        duration_uid = f"{DOMAIN}_{self._ip_address}_{self._channel}_flash_duration"
        entity_registry = er.async_get(self.hass)
        entity_id = entity_registry.async_get_entity_id("number", DOMAIN, duration_uid)

        duration_s = 1.0  # default 1 second
        if entity_id:
            state = self.hass.states.get(entity_id)
            if state and state.state not in (None, "unknown", "unavailable"):
                try:
                    duration_s = float(state.state)
                except ValueError:
                    pass

        duration_ms = int(duration_s * 1000)
        await self.hass.async_add_executor_job(
            flash_relay_on, self._ip_address, self._port, self._channel, duration_ms
        )


class WaveshareAllOnButton(ButtonEntity):
    """Button to turn all relays ON."""

    _attr_icon = "mdi:power-plug"

    def __init__(self, hass, ip_address, port, device_name):
        self.hass = hass
        self._ip_address = ip_address
        self._port = port
        self._device_name = device_name

    @property
    def unique_id(self):
        return f"{DOMAIN}_{self._ip_address}_all_on"

    @property
    def name(self):
        return f"{self._device_name} All Relays ON"

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._ip_address)},
            "name": self._device_name,
            "model": "Modbus POE ETH Relay",
            "manufacturer": "Waveshare",
        }

    async def async_press(self) -> None:
        await self.hass.async_add_executor_job(
            control_all_relays, self._ip_address, self._port, True
        )


class WaveshareAllOffButton(ButtonEntity):
    """Button to turn all relays OFF."""

    _attr_icon = "mdi:power-plug-off"

    def __init__(self, hass, ip_address, port, device_name):
        self.hass = hass
        self._ip_address = ip_address
        self._port = port
        self._device_name = device_name

    @property
    def unique_id(self):
        return f"{DOMAIN}_{self._ip_address}_all_off"

    @property
    def name(self):
        return f"{self._device_name} All Relays OFF"

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._ip_address)},
            "name": self._device_name,
            "model": "Modbus POE ETH Relay",
            "manufacturer": "Waveshare",
        }

    async def async_press(self) -> None:
        await self.hass.async_add_executor_job(
            control_all_relays, self._ip_address, self._port, False
        )


class WaveshareToggleAllButton(ButtonEntity):
    """Button to toggle all relays at once."""

    _attr_icon = "mdi:swap-vertical"

    def __init__(self, hass, ip_address, port, device_name):
        self.hass = hass
        self._ip_address = ip_address
        self._port = port
        self._device_name = device_name

    @property
    def unique_id(self):
        return f"{DOMAIN}_{self._ip_address}_toggle_all"

    @property
    def name(self):
        return f"{self._device_name} Toggle All Relays"

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._ip_address)},
            "name": self._device_name,
            "model": "Modbus POE ETH Relay",
            "manufacturer": "Waveshare",
        }

    async def async_press(self) -> None:
        await self.hass.async_add_executor_job(
            toggle_all_relays, self._ip_address, self._port
        )
