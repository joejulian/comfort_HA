"""Tests for Kumo Cloud climate entity behavior."""

from __future__ import annotations

from unittest.mock import AsyncMock

from homeassistant.components.climate import HVACMode
from homeassistant.components.climate.const import (
    ATTR_TARGET_TEMP_HIGH,
    ATTR_TARGET_TEMP_LOW,
)
from homeassistant.const import ATTR_TEMPERATURE

from custom_components.kumo_cloud.climate import KumoCloudClimate
from custom_components.kumo_cloud.coordinator import (
    KumoCloudDataUpdateCoordinator,
    KumoCloudDevice,
)


def _entity(
    hass,
    *,
    adapter: dict[str, object] | None = None,
    device_data: dict[str, object] | None = None,
    profile: list[dict[str, object]] | None = None,
) -> KumoCloudClimate:
    """Return a climate entity backed by synthetic coordinator data."""
    api = AsyncMock()
    coordinator = KumoCloudDataUpdateCoordinator(hass, api, "site-1")
    coordinator.data = {}
    coordinator.zones = [
        {
            "id": "zone-1",
            "name": "Living Room",
            "adapter": {
                "deviceSerial": "device-1",
                "connected": True,
                "power": 1,
                "roomTemp": 21.0,
                "operationMode": "cool",
                "spCool": 22.5,
                "spHeat": 19.0,
                "fanSpeed": "superQuiet",
                "airDirection": "vertical",
                **(adapter or {}),
            },
        }
    ]
    coordinator.devices = {
        "device-1": {
            "connected": True,
            **(device_data or {}),
        }
    }
    coordinator.device_profiles = {
        "device-1": profile
        or [
            {
                "numberOfFanSpeeds": 5,
                "hasVaneDir": True,
                "hasVaneSwing": True,
                "hasModeHeat": True,
                "hasModeCool": True,
                "hasModeAuto": True,
                "maximumSetPoints": {"heat": 30, "cool": 30, "auto": 30},
                "minimumSetPoints": {"heat": 16, "cool": 16},
            }
        ]
    }
    device = KumoCloudDevice(coordinator, "zone-1", "device-1")
    entity = KumoCloudClimate(device)
    entity.async_write_ha_state = lambda: None
    device.send_command = AsyncMock()
    return entity


def test_current_temperature_uses_mitsubishi_display_conversion(hass) -> None:
    """Current temperature uses Mitsubishi's C-to-F display conversion."""
    entity = _entity(hass, adapter={"roomTemp": 21.0})

    assert entity.current_temperature == 69


def test_current_humidity_uses_v3_adapter_or_device_payload(hass) -> None:
    """Current humidity exposes V3 humidity from device detail or zone adapter data."""
    adapter_humidity = _entity(hass, adapter={"humidity": 36.96875})
    device_humidity = _entity(
        hass,
        adapter={"humidity": 36.96875},
        device_data={"humidity": 41},
    )

    assert adapter_humidity.current_humidity == 36.96875
    assert device_humidity.current_humidity == 41


def test_heat_and_cool_target_temperatures_use_correct_setpoint_fields(hass) -> None:
    """Heat and cool modes expose their matching target setpoint."""
    cool = _entity(
        hass,
        adapter={"operationMode": "cool", "spCool": 22.5, "spHeat": 19.0},
    )
    heat = _entity(
        hass,
        adapter={"operationMode": "heat", "spCool": 22.5, "spHeat": 19.0},
    )

    assert cool.hvac_mode is HVACMode.COOL
    assert cool.target_temperature == 72
    assert heat.hvac_mode is HVACMode.HEAT
    assert heat.target_temperature == 67


def test_heat_cool_range_and_auto_mode_mapping(hass) -> None:
    """Auto heat/cool modes expose low and high range setpoints."""
    entity = _entity(
        hass,
        adapter={"operationMode": "autoCool", "spCool": 22.5, "spHeat": 19.0},
    )

    assert entity.hvac_mode is HVACMode.HEAT_COOL
    assert entity.target_temperature_low == 67
    assert entity.target_temperature_high == 72

    entity = _entity(hass, adapter={"operationMode": "autoHeat"})
    assert entity.hvac_mode is HVACMode.HEAT_COOL


def test_fan_and_vane_labels_map_to_comfort_app_labels(hass) -> None:
    """Fan and vane values use Comfort app labels."""
    entity = _entity(
        hass,
        adapter={"fanSpeed": "superQuiet", "airDirection": "vertical"},
    )

    assert entity.fan_mode == "quiet"
    assert entity.swing_mode == "lowest"
    assert entity.fan_modes == ["auto", "quiet", "low", "medium", "high", "powerful"]
    assert entity.swing_modes == [
        "auto",
        "swing",
        "lowest",
        "low",
        "middle",
        "high",
        "highest",
    ]


async def test_service_calls_send_expected_api_commands_in_celsius(hass) -> None:
    """Temperature, fan, and vane service calls send Kumo API values in Celsius."""
    entity = _entity(
        hass,
        adapter={"operationMode": "cool", "spCool": 22.5, "spHeat": 19.0},
    )

    await entity.async_set_temperature(**{ATTR_TEMPERATURE: 70})
    entity.device.send_command.assert_awaited_with({"spCool": 21.5, "spHeat": 19.0})

    await entity.async_set_temperature(
        **{ATTR_TARGET_TEMP_LOW: 69, ATTR_TARGET_TEMP_HIGH: 72}
    )
    entity.device.send_command.assert_awaited_with({"spHeat": 21.0, "spCool": 22.5})

    await entity.async_set_fan_mode("high")
    entity.device.send_command.assert_awaited_with({"fanSpeed": "powerful"})

    await entity.async_set_swing_mode("middle")
    entity.device.send_command.assert_awaited_with({"airDirection": "midpoint"})
