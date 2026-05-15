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
    "accountId",
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

REDACTED = "**REDACTED**"


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    runtime_data: KumoCloudRuntimeData | None = hass.data.get(DOMAIN, {}).get(entry.entry_id)

    sensitive_values = _sensitive_values(entry, runtime_data.coordinator if runtime_data else None)

    diagnostics: dict[str, Any] = {
        "entry": {
            "title": entry.title,
            "data": _redact(dict(entry.data), sensitive_values),
            "options": _redact(dict(entry.options), sensitive_values),
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
    sensitive_values = _sensitive_values(None, coordinator)
    return _redact(
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
        sensitive_values,
    )


def _redact(data: dict[str, Any], sensitive_values: set[str]) -> dict[str, Any]:
    """Redact sensitive keys, values, and identifier map keys."""
    return _redact_sensitive_values(async_redact_data(data, TO_REDACT), sensitive_values)


def _redact_sensitive_values(value: Any, sensitive_values: set[str]) -> Any:
    """Recursively redact known sensitive string values and dictionary keys."""
    if isinstance(value, dict):
        redacted: dict[Any, Any] = {}
        for key, item in value.items():
            redacted_key = REDACTED if key in sensitive_values else key
            redacted[redacted_key] = _redact_sensitive_values(item, sensitive_values)
        return redacted

    if isinstance(value, list):
        return [_redact_sensitive_values(item, sensitive_values) for item in value]

    if isinstance(value, str) and value in sensitive_values:
        return REDACTED

    return value


def _sensitive_values(
    entry: ConfigEntry | None,
    coordinator: KumoCloudDataUpdateCoordinator | None,
) -> set[str]:
    """Return sensitive string values that should not appear in diagnostics."""
    values: set[str] = set()

    if entry is not None:
        values.update(_collect_sensitive_values(dict(entry.data)))
        values.update(_collect_sensitive_values(dict(entry.options)))

    if coordinator is not None:
        values.add(coordinator.site_id)
        values.update(coordinator.devices)
        values.update(coordinator.device_profiles)
        values.update(coordinator.wireless_sensors)
        values.update(coordinator.device_statuses)
        values.update(coordinator.zone_notifications)
        values.update(
            _collect_sensitive_values(
                {
                    "zones": coordinator.zones,
                    "devices": coordinator.devices,
                    "device_profiles": coordinator.device_profiles,
                    "wireless_sensors": coordinator.wireless_sensors,
                    "device_statuses": coordinator.device_statuses,
                    "zone_notifications": coordinator.zone_notifications,
                }
            )
        )

    return {value for value in values if value}


def _collect_sensitive_values(data: Any) -> set[str]:
    """Collect string values from sensitive identifier fields."""
    values: set[str] = set()
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(key, str) and _is_sensitive_key(key) and isinstance(value, str):
                values.add(value)
            values.update(_collect_sensitive_values(value))
    elif isinstance(data, list):
        for item in data:
            values.update(_collect_sensitive_values(item))
    return values


def _is_sensitive_key(key: str) -> bool:
    """Return True if a diagnostics key carries sensitive identity data."""
    key_lower = key.lower()
    return (
        key in TO_REDACT
        or key_lower.endswith("id")
        or "serial" in key_lower
        or "ssid" in key_lower
    )
