"""Constants for the Shark IQ (Local) integration."""
from __future__ import annotations

from datetime import timedelta

DOMAIN = "sharkiq_local"

# Config entry keys
CONF_HOST = "host"
CONF_NAME = "name"
CONF_MAPPING = "mapping"
CONF_USE_MQTT = "use_mqtt"

# Defaults
DEFAULT_MAPPING = "sharkiq_v1"
DEFAULT_USE_MQTT = True
SCAN_INTERVAL = timedelta(seconds=30)

# Platforms provided by this integration
PLATFORMS = ["vacuum", "sensor"]

# Event names fired on the HA bus
EVENT_DUSTBIN_REMOVED = f"{DOMAIN}_dustbin_removed"
EVENT_VACUUM_EVENT = f"{DOMAIN}_event"
