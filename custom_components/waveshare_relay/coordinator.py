"""DataUpdateCoordinator for Waveshare digital inputs.

Polls all DI channels in a single Modbus read and fans the result out to every
binary_sensor entity. Previously each entity polled independently at 5s, producing
8× redundant reads and ~2s of perceived latency on button presses. One shared
coordinator at 250ms gives sub-quarter-second response with less total traffic.
"""

from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .utils import read_discrete_inputs

_LOGGER = logging.getLogger(__name__)

DI_POLL_INTERVAL = timedelta(milliseconds=250)


class WaveshareDIUpdateCoordinator(DataUpdateCoordinator[list[bool]]):
    """Polls all discrete inputs in one Modbus read per cycle."""

    def __init__(
        self,
        hass: HomeAssistant,
        ip_address: str,
        port: int,
        num_channels: int,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=f"waveshare_relay_di_{ip_address}",
            update_interval=DI_POLL_INTERVAL,
        )
        self._ip_address = ip_address
        self._port = port
        self._num_channels = num_channels

    async def _async_update_data(self) -> list[bool]:
        states = await self.hass.async_add_executor_job(
            read_discrete_inputs,
            self._ip_address,
            self._port,
            0,
            self._num_channels,
        )
        if states is None:
            raise UpdateFailed(
                f"No response from {self._ip_address}:{self._port}"
            )
        return states
