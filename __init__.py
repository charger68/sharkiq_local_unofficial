"""The Shark IQ (Local) integration."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from sharklocal import SharklocalError, VacuumClient

from .const import (
    CONF_HOST,
    CONF_MAPPING,
    CONF_USE_MQTT,
    DEFAULT_MAPPING,
    DEFAULT_USE_MQTT,
    DOMAIN,
    PLATFORMS,
)
from .coordinator import SharkCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Shark IQ (Local) from a config entry."""
    host: str = entry.data[CONF_HOST]
    mapping: str = entry.data.get(CONF_MAPPING, DEFAULT_MAPPING)
    use_mqtt: bool = entry.data.get(CONF_USE_MQTT, DEFAULT_USE_MQTT)

    client = VacuumClient(
        host=host,
        rest_mappings=mapping,
        mqtt_mappings=mapping if use_mqtt else None,
    )

    # VacuumClient supports async-context-manager use; we manage it manually
    # because we want it to live for the lifetime of the config entry.
    try:
        await client.__aenter__()
    except SharklocalError as err:
        raise ConfigEntryNotReady(f"Could not connect to {host}: {err}") from err

    coordinator = SharkCoordinator(hass, client, entry.entry_id, host)

    try:
        await coordinator.async_setup()
        await coordinator.async_config_entry_first_refresh()
    except Exception:
        # If first refresh failed, close the client we just opened.
        await client.close()
        raise

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        coordinator: SharkCoordinator = hass.data[DOMAIN].pop(entry.entry_id)
        await coordinator.client.close()
    return unload_ok
