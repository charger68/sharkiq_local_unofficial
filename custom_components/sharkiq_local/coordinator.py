"""DataUpdateCoordinator for a single Shark IQ vacuum."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from sharklocal import (
    ConnectError,
    SharklocalError,
    VacuumClient,
)
from sharklocal.models import DeviceInfo, VacuumStatus

from .const import DOMAIN, SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)


@dataclass
class SharkData:
    """Snapshot of all data we expose for one vacuum."""

    status: VacuumStatus
    device_info: DeviceInfo | None
    wifi: DeviceInfo | None


class SharkCoordinator(DataUpdateCoordinator[SharkData]):
    """Coordinate polling of a single Shark vacuum.

    Holds a long-lived VacuumClient and refreshes status every SCAN_INTERVAL.
    Device info is fetched once at startup and then occasionally refreshed.
    """

    def __init__(
        self,
        hass: HomeAssistant,
        client: VacuumClient,
        entry_id: str,
        host: str,
    ) -> None:
        """Initialize."""
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{host}",
            update_interval=SCAN_INTERVAL,
        )
        self.client = client
        self.entry_id = entry_id
        self.host = host
        # Cached once-per-session info (firmware, MAC, etc.)
        self._device_info: DeviceInfo | None = None
        self._wifi: DeviceInfo | None = None
        self._device_info_cycle = 0

    async def async_setup(self) -> None:
        """Initial setup: fetch device info so we can register a device in HA."""
        try:
            self._device_info = await self.client.get_device_info()
        except SharklocalError as err:
            _LOGGER.debug("Could not fetch device info for %s: %s", self.host, err)
        try:
            self._wifi = await self.client.get_wifi_status()
        except SharklocalError as err:
            _LOGGER.debug("Could not fetch wifi status for %s: %s", self.host, err)

    async def _async_update_data(self) -> SharkData:
        """Poll the vacuum for current status."""
        try:
            status = await self.client.get_status()
        except ConnectError as err:
            raise UpdateFailed(f"Vacuum {self.host} unreachable: {err}") from err
        except SharklocalError as err:
            raise UpdateFailed(f"Vacuum {self.host} error: {err}") from err

        # Refresh wifi info every ~10 polls (~5 min at 30s interval) for RSSI updates.
        # Firmware/MAC are stable, so we don't need to hammer the device.
        self._device_info_cycle += 1
        if self._device_info_cycle >= 10:
            self._device_info_cycle = 0
            try:
                self._wifi = await self.client.get_wifi_status()
            except SharklocalError as err:
                _LOGGER.debug("WiFi refresh failed for %s: %s", self.host, err)

        return SharkData(
            status=status,
            device_info=self._device_info,
            wifi=self._wifi,
        )

    @property
    def unique_id(self) -> str:
        """Stable unique ID for this vacuum.

        Prefers MAC from wifi_status (recommended by the upstream lib),
        falls back to host if MAC isn't available.
        """
        if self._wifi and self._wifi.mac_address:
            return self._wifi.mac_address
        if self._device_info and self._device_info.mac_address:
            return self._device_info.mac_address
        return self.host

    def get_device_metadata(self) -> dict[str, Any]:
        """Return metadata for HA device registry."""
        firmware = None
        mac = None
        if self._device_info:
            firmware = self._device_info.firmware
            mac = self._device_info.mac_address
        if self._wifi and not mac:
            mac = self._wifi.mac_address
        return {"firmware": firmware, "mac": mac}
