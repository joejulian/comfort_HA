"""Tests for Kumo Cloud diagnostics redaction."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock

from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.kumo_cloud.api import KumoCloudAPI
from custom_components.kumo_cloud.const import CONF_SITE_ID, DOMAIN
from custom_components.kumo_cloud.coordinator import KumoCloudDataUpdateCoordinator
from custom_components.kumo_cloud.diagnostics import async_get_config_entry_diagnostics
from custom_components.kumo_cloud.runtime import KumoCloudRuntimeData


async def test_diagnostics_redacts_credentials_and_identifiers(hass) -> None:
    """Diagnostics redact account, site, token, device, and router identifiers."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        entry_id="entry-1",
        title="Kumo Cloud - Home",
        data={
            CONF_USERNAME: "user@example.invalid",
            CONF_PASSWORD: "account-password",
            CONF_SITE_ID: "site-sensitive",
            "access_token": "access-token-sensitive",
            "refresh_token": "refresh-token-sensitive",
        },
    )
    coordinator = KumoCloudDataUpdateCoordinator(hass, AsyncMock(), "site-sensitive")
    coordinator.data = {}
    coordinator.zones = [
        {
            "id": "zone-sensitive",
            "siteId": "site-sensitive",
            "name": "Living Room",
            "adapter": {
                "deviceSerial": "device-sensitive",
                "hasSensor": True,
            },
        }
    ]
    coordinator.devices = {
        "device-sensitive": {
            "serialNumber": "device-serial-sensitive",
            "accountId": "account-sensitive",
        }
    }
    coordinator.device_profiles = {"device-sensitive": [{"id": "profile-sensitive"}]}
    coordinator.wireless_sensors = {
        "device-sensitive": {"id": "sensor-sensitive", "rssi": -55}
    }
    coordinator.device_statuses = {
        "device-sensitive": {
            "routerSsid": "private-wifi",
            "cryptoSerial": "crypto-sensitive",
        }
    }
    coordinator.zone_notifications = {
        "zone-sensitive": {"id": "notification-sensitive", "filterDirty": True}
    }
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = KumoCloudRuntimeData(
        api=AsyncMock(spec=KumoCloudAPI),
        coordinator=coordinator,
    )

    diagnostics = await async_get_config_entry_diagnostics(hass, entry)

    assert diagnostics["coordinator"]["zone_count"] == 1
    assert diagnostics["coordinator"]["device_count"] == 1
    assert diagnostics["coordinator"]["wireless_sensor_count"] == 1

    flattened = list(_flatten_strings(diagnostics))
    for sensitive_value in {
        "user@example.invalid",
        "account-password",
        "access-token-sensitive",
        "refresh-token-sensitive",
        "site-sensitive",
        "zone-sensitive",
        "device-sensitive",
        "device-serial-sensitive",
        "private-wifi",
        "crypto-sensitive",
        "account-sensitive",
        "profile-sensitive",
        "sensor-sensitive",
        "notification-sensitive",
    }:
        assert sensitive_value not in flattened


def _flatten_strings(value: Any) -> list[str]:
    """Return all string keys and values in a nested diagnostics payload."""
    if isinstance(value, dict):
        strings: list[str] = []
        for key, item in value.items():
            if isinstance(key, str):
                strings.append(key)
            strings.extend(_flatten_strings(item))
        return strings

    if isinstance(value, list):
        strings = []
        for item in value:
            strings.extend(_flatten_strings(item))
        return strings

    if isinstance(value, str):
        return [value]

    return []
