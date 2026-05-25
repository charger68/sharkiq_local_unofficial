"""Config flow for Shark IQ (Local)."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_HOST, CONF_NAME

from sharklocal import (
    ConnectError,
    SharklocalError,
    VacuumClient,
)

from .const import (
    CONF_MAPPING,
    CONF_USE_MQTT,
    DEFAULT_MAPPING,
    DEFAULT_USE_MQTT,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_NAME): str,
        vol.Optional(CONF_MAPPING, default=DEFAULT_MAPPING): str,
        vol.Optional(CONF_USE_MQTT, default=DEFAULT_USE_MQTT): bool,
    }
)


async def _probe(host: str, mapping: str, use_mqtt: bool) -> str | None:
    """Try to talk to the vacuum. Returns the MAC address as a unique ID, or None."""
    client = VacuumClient(
        host=host,
        rest_mappings=mapping,
        mqtt_mappings=mapping if use_mqtt else None,
    )
    try:
        async with client:
            # Confirm we can read status — this is the cheapest call.
            await client.get_status()
            # Try to get the MAC for a stable unique ID. Best-effort.
            try:
                wifi = await client.get_wifi_status()
                if wifi and wifi.mac_address:
                    return wifi.mac_address
            except SharklocalError:
                pass
    except ConnectError:
        raise
    except SharklocalError:
        raise
    return None


class SharkIQLocalConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Shark IQ (Local)."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step (manual entry)."""
        errors: dict[str, str] = {}

        if user_input is not None:
            host = user_input[CONF_HOST].strip()
            mapping = user_input.get(CONF_MAPPING, DEFAULT_MAPPING)
            use_mqtt = user_input.get(CONF_USE_MQTT, DEFAULT_USE_MQTT)

            # Make host the fallback unique ID; replaced by MAC if we can read it.
            unique_id = host
            try:
                mac = await _probe(host, mapping, use_mqtt)
                if mac:
                    unique_id = mac
            except ConnectError:
                errors["base"] = "cannot_connect"
            except SharklocalError:
                errors["base"] = "unknown"
            except Exception:  # noqa: BLE001
                _LOGGER.exception("Unexpected error probing %s", host)
                errors["base"] = "unknown"

            if not errors:
                await self.async_set_unique_id(unique_id)
                self._abort_if_unique_id_configured(updates={CONF_HOST: host})

                return self.async_create_entry(
                    title=user_input[CONF_NAME],
                    data={
                        CONF_HOST: host,
                        CONF_NAME: user_input[CONF_NAME],
                        CONF_MAPPING: mapping,
                        CONF_USE_MQTT: use_mqtt,
                    },
                )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )
