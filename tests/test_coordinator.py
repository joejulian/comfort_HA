"""Tests for Kumo Cloud coordinator refresh behavior."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.kumo_cloud.api import KumoCloudAuthError, KumoCloudConnectionError
from custom_components.kumo_cloud.coordinator import KumoCloudDataUpdateCoordinator


@pytest.fixture
def api() -> AsyncMock:
    """Return a mocked Kumo Cloud API client."""
    client = AsyncMock()
    client.get_zones = AsyncMock(
        return_value=[
            {
                "id": "zone-1",
                "name": "Living Room",
                "adapter": {
                    "deviceSerial": "device-1",
                    "hasSensor": True,
                },
            },
            {
                "id": "zone-2",
                "name": "Office",
                "adapter": {
                    "deviceSerial": "device-2",
                    "hasSensor": False,
                },
            },
        ]
    )
    client.get_device_details = AsyncMock(
        side_effect=[
            {"serialNumber": "device-1", "updatedAt": "2026-01-01T00:00:00+00:00"},
            {"serialNumber": "device-2", "updatedAt": "2026-01-01T00:00:00+00:00"},
        ]
    )
    client.get_device_profile = AsyncMock(side_effect=[[{"hasModeHeat": True}], []])
    client.get_device_status = AsyncMock(
        side_effect=[{"firmwareVersion": "1.0.0"}, {"firmwareVersion": "1.0.1"}]
    )
    client.get_zone_notification_preferences = AsyncMock(
        side_effect=[{"filterDirtyReminderInterval": 90}, {}]
    )
    client.get_wireless_sensor = AsyncMock(
        return_value={"battery": 90, "rssi": -55, "temperature": 21.5}
    )
    client.refresh_access_token = AsyncMock()
    return client


@pytest.fixture
def coordinator(hass, api: AsyncMock) -> KumoCloudDataUpdateCoordinator:
    """Return a coordinator using a mocked API client."""
    return KumoCloudDataUpdateCoordinator(hass, api, "site-1")


async def test_refresh_assembles_zone_device_profile_and_status_data(
    coordinator: KumoCloudDataUpdateCoordinator,
    api: AsyncMock,
) -> None:
    """Zones with adapters create device, profile, status, and sensor data."""
    data = await coordinator._async_update_data()

    assert [zone["id"] for zone in data["zones"]] == ["zone-1", "zone-2"]
    assert set(data["devices"]) == {"device-1", "device-2"}
    assert data["device_profiles"]["device-1"] == [{"hasModeHeat": True}]
    assert data["device_statuses"]["device-1"] == {"firmwareVersion": "1.0.0"}
    assert data["wireless_sensors"]["device-1"] == {
        "battery": 90,
        "rssi": -55,
        "temperature": 21.5,
    }
    assert "device-2" not in data["wireless_sensors"]
    api.get_wireless_sensor.assert_awaited_once_with("device-1")


async def test_optional_endpoint_failures_do_not_fail_refresh(
    coordinator: KumoCloudDataUpdateCoordinator,
    api: AsyncMock,
) -> None:
    """Optional endpoint failures are omitted without failing the whole refresh."""
    api.get_device_status.side_effect = KumoCloudConnectionError("status failed")
    api.get_zone_notification_preferences.side_effect = KumoCloudConnectionError(
        "notifications failed"
    )

    data = await coordinator._async_update_data()

    assert set(data["devices"]) == {"device-1", "device-2"}
    assert data["device_statuses"] == {}
    assert data["zone_notifications"] == {}


async def test_auth_failure_refreshes_token_once_then_retries(
    coordinator: KumoCloudDataUpdateCoordinator,
    api: AsyncMock,
) -> None:
    """An auth failure refreshes the token once and retries the refresh."""
    retry_zones = [
        {
            "id": "zone-1",
            "name": "Living Room",
            "adapter": {"deviceSerial": "device-1", "hasSensor": False},
        }
    ]
    api.get_zones.side_effect = [KumoCloudAuthError("expired"), retry_zones]
    api.get_device_details.side_effect = [
        {"serialNumber": "device-1", "updatedAt": "2026-01-01T00:00:00+00:00"}
    ]
    api.get_device_profile.side_effect = [[]]
    api.get_device_status.side_effect = [{}]
    api.get_zone_notification_preferences.side_effect = [{}]

    data = await coordinator._async_update_data()

    api.refresh_access_token.assert_awaited_once()
    assert list(data["devices"]) == ["device-1"]


async def test_persistent_connection_failure_raises_update_failed(
    coordinator: KumoCloudDataUpdateCoordinator,
    api: AsyncMock,
) -> None:
    """Persistent API connection failures become Home Assistant UpdateFailed."""
    api.get_zones.side_effect = KumoCloudConnectionError("offline")

    with pytest.raises(UpdateFailed):
        await coordinator._async_update_data()
