"""Base entity for Shark IQ (Local)."""
from __future__ import annotations

from homeassistant.helpers.device_registry import CONNECTION_NETWORK_MAC, DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import SharkCoordinator


class SharkBaseEntity(CoordinatorEntity[SharkCoordinator]):
    """Common base for all Shark entities — links them to one HA device."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: SharkCoordinator, entry_title: str) -> None:
        """Initialize."""
        super().__init__(coordinator)
        self._entry_title = entry_title
        meta = coordinator.get_device_metadata()
        connections = set()
        if meta["mac"]:
            connections.add((CONNECTION_NETWORK_MAC, meta["mac"]))

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.unique_id)},
            connections=connections,
            name=entry_title,
            manufacturer="SharkNinja",
            model="Shark IQ Robot",
            sw_version=meta["firmware"],
            configuration_url=f"https://{coordinator.host}",
        )
