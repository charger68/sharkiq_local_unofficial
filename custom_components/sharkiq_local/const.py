"""Constants for the Shark IQ (Local) integration."""
from __future__ import annotations

DOMAIN = "sharkiq_local"

# Config entry keys (initial setup)
CONF_HOST = "host"
CONF_NAME = "name"
CONF_MAPPING = "mapping"
CONF_USE_MQTT = "use_mqtt"

# Options keys (editable after setup via "Configure")
CONF_SCAN_INTERVAL = "scan_interval"

# Defaults
DEFAULT_MAPPING = "sharkiq_v1"
DEFAULT_USE_MQTT = True
DEFAULT_SCAN_INTERVAL = 30  # seconds

# Sanity bounds for the polling interval. 5s lower bound prevents users from
# accidentally setting something pathological; 600s upper is "you basically
# turned polling off but didn't want to disable the entity".
MIN_SCAN_INTERVAL = 5
MAX_SCAN_INTERVAL = 600

# Platforms provided by this integration
PLATFORMS = ["vacuum", "sensor"]

# Event names fired on the HA bus
EVENT_DUSTBIN_REMOVED = f"{DOMAIN}_dustbin_removed"
EVENT_VACUUM_EVENT = f"{DOMAIN}_event"
