"""Diagnostics support for the Kumo Cloud integration."""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant

from .coordinator import KumoCloudDataUpdateCoordinator
from .const import CONF_SITE_ID, DOMAIN
from .runtime import KumoCloudRuntimeData

TO_REDACT = {
    CONF_PASSWORD,
    CONF_USERNAME,
    CONF_SITE_ID,
    "access",
    "access_token",
    "cryptoSerial",
    "deviceSerial",
    "email",
    "id",
    "refresh",
    "refresh_token",
    "routerSsid",
    "serialNumber",
    "siteId",
    "username",
}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    runtime_data: KumoCloudRuntimeData | None = hass.data.get(DOMAIN, {}).get(entry.entry_id)

    diagnostics: dict[str, Any] = {
        "entry": {
            "title": entry.title,
            "data": async_redact_data(dict(entry.data), TO_REDACT),
            "options": async_redact_data(dict(entry.options), TO_REDACT),
        },
        "coordinator": None,
    }

    if runtime_data is not None:
        diagnostics["coordinator"] = _coordinator_diagnostics(runtime_data.coordinator)

    return diagnostics


def _coordinator_diagnostics(
    coordinator: KumoCloudDataUpdateCoordinator,
) -> dict[str, Any]:
    """Return redacted coordinator diagnostics."""
    return async_redact_data(
        {
            "last_update_success": coordinator.last_update_success,
            "site_id": coordinator.site_id,
            "zone_count": len(coordinator.zones),
            "device_count": len(coordinator.devices),
            "wireless_sensor_count": len(coordinator.wireless_sensors),
            "device_status_count": len(coordinator.device_statuses),
            "zone_notification_count": len(coordinator.zone_notifications),
            "cached_command_count": len(coordinator.command_cache),
            "zones": coordinator.zones,
            "devices": coordinator.devices,
            "device_profiles": coordinator.device_profiles,
            "wireless_sensors": coordinator.wireless_sensors,
            "device_statuses": coordinator.device_statuses,
            "zone_notifications": coordinator.zone_notifications,
        },
        TO_REDACT,
    )
