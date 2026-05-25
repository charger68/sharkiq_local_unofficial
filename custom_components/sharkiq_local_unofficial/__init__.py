"""The Shark IQ (Local) integration."""
from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from sharklocal import SharklocalError, VacuumClient

from .const import (
    CONF_HOST,
    CONF_MAPPING,
    CONF_SCAN_INTERVAL,
    CONF_USE_MQTT,
    DEFAULT_MAPPING,
    DEFAULT_SCAN_INTERVAL,
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
    # scan_interval lives in options (editable post-setup), not data.
    scan_interval: int = entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)

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

    coordinator = SharkCoordinator(hass, client, entry.entry_id, host, scan_interval)

    try:
        await coordinator.async_setup()
        await coordinator.async_config_entry_first_refresh()
    except Exception:
        # If first refresh failed, close the client we just opened.
        await client.close()
        raise

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Apply options changes (e.g. new scan interval) live, no restart needed.
    entry.async_on_unload(entry.add_update_listener(_async_options_updated))

    return True


async def _async_options_updated(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options updates by applying the new scan interval in place."""
    coordinator: SharkCoordinator = hass.data[DOMAIN][entry.entry_id]
    new_interval: int = entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
    coordinator.update_interval = timedelta(seconds=new_interval)
    _LOGGER.debug(
        "Updated %s poll interval to %ss", coordinator.host, new_interval
    )


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        coordinator: SharkCoordinator = hass.data[DOMAIN].pop(entry.entry_id)
        await coordinator.client.close()
    return unload_ok
