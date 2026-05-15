"""Tests for Kumo Cloud optimistic command cache behavior."""

from __future__ import annotations

from custom_components.kumo_cloud.command_cache import KumoCloudCommandCache


def test_cached_command_applies_optimistically_before_cloud_catches_up() -> None:
    """Cached values are applied while cloud updatedAt is older than the command."""
    cache = KumoCloudCommandCache()
    cache.commands[("device-1", "spCool")] = (
        "2026-01-01T12:00:00+00:00",
        21.5,
    )
    device_detail = {"updatedAt": "2026-01-01T11:59:59+00:00", "spCool": 20.0}

    cache.apply("device-1", device_detail)

    assert device_detail["spCool"] == 21.5
    assert ("device-1", "spCool") in cache.commands


def test_cached_command_is_culled_only_after_cloud_timestamp_is_newer() -> None:
    """Cached values remain until cloud updatedAt is newer than the cache timestamp."""
    cache = KumoCloudCommandCache()
    cache.commands[("device-1", "spCool")] = (
        "2026-01-01T12:00:00+00:00",
        21.5,
    )

    cache.cull("device-1", "2026-01-01T12:00:00+00:00")
    assert ("device-1", "spCool") in cache.commands

    cache.cull("device-1", "2026-01-01T12:00:01+00:00")
    assert ("device-1", "spCool") not in cache.commands


def test_unrelated_devices_and_properties_are_not_affected() -> None:
    """Cull and apply only affect the matching device and property."""
    cache = KumoCloudCommandCache()
    cache.commands[("device-1", "spCool")] = (
        "2026-01-01T12:00:00+00:00",
        21.5,
    )
    cache.commands[("device-2", "spHeat")] = (
        "2026-01-01T12:00:00+00:00",
        18.0,
    )
    device_detail = {"updatedAt": "2026-01-01T11:59:59+00:00", "spHeat": 17.0}

    cache.apply("device-1", device_detail)
    cache.cull("device-1", "2026-01-01T12:00:01+00:00")

    assert device_detail == {
        "updatedAt": "2026-01-01T11:59:59+00:00",
        "spHeat": 17.0,
        "spCool": 21.5,
    }
    assert ("device-1", "spCool") not in cache.commands
    assert ("device-2", "spHeat") in cache.commands


def test_invalid_or_missing_timestamps_do_not_crash_refresh() -> None:
    """Invalid cloud and cache timestamps are ignored without raising."""
    cache = KumoCloudCommandCache()
    cache.commands[("device-1", "spCool")] = ("not-a-date", 21.5)
    device_detail = {"updatedAt": "not-a-date", "spCool": 20.0}

    cache.apply("device-1", device_detail)
    cache.cull("device-1", None)

    assert device_detail["spCool"] == 21.5
    assert ("device-1", "spCool") in cache.commands
