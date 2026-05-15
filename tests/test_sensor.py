"""Tests for Kumo Cloud sensor entity behavior."""

from __future__ import annotations

from unittest.mock import AsyncMock, Mock

from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.const import (
    EntityCategory,
    PERCENTAGE,
    SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
    UnitOfTemperature,
)
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.kumo_cloud.api import KumoCloudAPI
from custom_components.kumo_cloud.const import DOMAIN
from custom_components.kumo_cloud.coordinator import (
    KumoCloudDataUpdateCoordinator,
    KumoCloudDevice,
)
from custom_components.kumo_cloud.runtime import KumoCloudRuntimeData
from custom_components.kumo_cloud.sensor import (
    KumoCloudFilterReminderSensor,
    KumoCloudFirmwareSensor,
    KumoCloudHumiditySensor,
    KumoCloudTemperatureSensor,
    KumoCloudWiFiSignalSensor,
    KumoCloudWirelessBatterySensor,
    KumoCloudWirelessHumiditySensor,
    KumoCloudWirelessSignalSensor,
    KumoCloudWirelessTemperatureSensor,
    async_setup_entry,
)


def _coordinator(hass) -> KumoCloudDataUpdateCoordinator:
    """Return a coordinator with synthetic sensor data."""
    coordinator = KumoCloudDataUpdateCoordinator(hass, AsyncMock(), "site-1")
    coordinator.data = {}
    coordinator.zones = [
        {
            "id": "zone-1",
            "name": "Living Room",
            "adapter": {
                "deviceSerial": "device-1",
                "hasSensor": True,
                "connected": True,
                "roomTemp": 21.5,
                "humidity": 45,
            },
        }
    ]
    coordinator.devices = {"device-1": {"connected": True, "humidity": 46}}
    coordinator.wireless_sensors = {
        "device-1": {
            "battery": 88,
            "rssi": -51,
            "temperature": 20.56,
            "humidity": 44.44,
        }
    }
    coordinator.device_statuses = {
        "device-1": {
            "firmwareVersion": "1.2.3",
            "routerRssi": -62,
            "routerSsid": "Example WiFi",
        }
    }
    coordinator.zone_notifications = {
        "zone-1": {
            "filterDirtyReminderLastSent": "2026-01-01T00:00:00Z",
            "filterDirtyReminderInterval": 90,
            "filterDirty": True,
        }
    }
    return coordinator


def _device(coordinator: KumoCloudDataUpdateCoordinator) -> KumoCloudDevice:
    """Return a synthetic Kumo Cloud device wrapper."""
    return KumoCloudDevice(coordinator, "zone-1", "device-1")


async def test_sensor_platform_adds_zone_and_wireless_sensor_entities(hass) -> None:
    """Sensor setup adds indoor, diagnostic, and wireless entities."""
    coordinator = _coordinator(hass)
    entry = MockConfigEntry(domain=DOMAIN, entry_id="entry-1")
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = KumoCloudRuntimeData(
        api=AsyncMock(spec=KumoCloudAPI),
        coordinator=coordinator,
    )
    async_add_entities = Mock()

    await async_setup_entry(hass, entry, async_add_entities)

    entities = async_add_entities.call_args.args[0]
    assert len(entities) == 9
    assert {entity.unique_id for entity in entities} == {
        "device-1_temperature",
        "device-1_humidity",
        "device-1_firmware",
        "device-1_wifi_rssi",
        "device-1_filter_reminder",
        "device-1_wireless_battery",
        "device-1_wireless_rssi",
        "device-1_wireless_temperature",
        "device-1_wireless_humidity",
    }


def test_zone_temperature_and_humidity_sensors(hass) -> None:
    """Indoor zone temperature and humidity sensors expose expected metadata."""
    device = _device(_coordinator(hass))
    temperature = KumoCloudTemperatureSensor(device.coordinator, device)
    humidity = KumoCloudHumiditySensor(device.coordinator, device)

    assert temperature.native_value == 21.5
    assert temperature.native_unit_of_measurement is UnitOfTemperature.CELSIUS
    assert temperature.device_class is SensorDeviceClass.TEMPERATURE
    assert temperature.state_class is SensorStateClass.MEASUREMENT
    assert temperature.unique_id == "device-1_temperature"

    assert humidity.native_value == 46
    assert humidity.native_unit_of_measurement == PERCENTAGE
    assert humidity.device_class is SensorDeviceClass.HUMIDITY
    assert humidity.state_class is SensorStateClass.MEASUREMENT
    assert humidity.unique_id == "device-1_humidity"


def test_wireless_sensor_entities(hass) -> None:
    """Wireless sensor entities expose battery, RSSI, temperature, and humidity."""
    device = _device(_coordinator(hass))
    battery = KumoCloudWirelessBatterySensor(device.coordinator, device)
    signal = KumoCloudWirelessSignalSensor(device.coordinator, device)
    temperature = KumoCloudWirelessTemperatureSensor(device.coordinator, device)
    humidity = KumoCloudWirelessHumiditySensor(device.coordinator, device)

    assert battery.native_value == 88
    assert battery.device_class is SensorDeviceClass.BATTERY
    assert battery.entity_category is EntityCategory.DIAGNOSTIC
    assert signal.native_value == -51
    assert signal.native_unit_of_measurement == SIGNAL_STRENGTH_DECIBELS_MILLIWATT
    assert temperature.native_value == 20.6
    assert temperature.native_unit_of_measurement is UnitOfTemperature.CELSIUS
    assert humidity.native_value == 44.4
    assert humidity.native_unit_of_measurement == PERCENTAGE


def test_firmware_wifi_and_filter_diagnostic_sensors(hass) -> None:
    """Diagnostic sensors expose firmware, WiFi, and filter metadata."""
    device = _device(_coordinator(hass))
    firmware = KumoCloudFirmwareSensor(device.coordinator, device)
    wifi = KumoCloudWiFiSignalSensor(device.coordinator, device)
    filter_reminder = KumoCloudFilterReminderSensor(device.coordinator, device)

    assert firmware.native_value == "1.2.3"
    assert firmware.entity_category is EntityCategory.DIAGNOSTIC
    assert wifi.native_value == -62
    assert wifi.device_class is SensorDeviceClass.SIGNAL_STRENGTH
    assert wifi.entity_category is EntityCategory.DIAGNOSTIC
    assert wifi.extra_state_attributes == {"router_ssid": "Example WiFi"}
    assert filter_reminder.native_value.isoformat() == "2026-01-01T00:00:00+00:00"
    assert filter_reminder.entity_category is EntityCategory.DIAGNOSTIC
    assert filter_reminder.extra_state_attributes == {
        "reminder_interval_days": 90,
        "reminders_enabled": True,
    }


def test_unavailable_optional_data_returns_none_without_setup_failure(hass) -> None:
    """Missing optional endpoint data returns None instead of failing."""
    coordinator = _coordinator(hass)
    coordinator.wireless_sensors = {}
    coordinator.device_statuses = {}
    coordinator.zone_notifications = {}
    device = _device(coordinator)

    assert KumoCloudWirelessBatterySensor(coordinator, device).native_value is None
    assert KumoCloudWirelessSignalSensor(coordinator, device).native_value is None
    assert KumoCloudWirelessTemperatureSensor(coordinator, device).native_value is None
    assert KumoCloudWirelessHumiditySensor(coordinator, device).native_value is None
    assert KumoCloudFirmwareSensor(coordinator, device).native_value is None
    assert KumoCloudWiFiSignalSensor(coordinator, device).native_value is None
    assert KumoCloudFilterReminderSensor(coordinator, device).native_value is None
