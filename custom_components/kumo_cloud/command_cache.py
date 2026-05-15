"""Optimistic command cache for Kumo Cloud device updates."""

from __future__ import annotations

from datetime import datetime, timezone
import logging
from typing import Any

_LOGGER = logging.getLogger(__name__)


class KumoCloudCommandCache:
    """Cache recently sent commands until cloud state catches up."""

    def __init__(self) -> None:
        """Initialize the command cache."""
        self.commands: dict[tuple[str, str], tuple[str, Any]] = {}

    def __len__(self) -> int:
        """Return the number of cached commands."""
        return len(self.commands)

    def cache(self, device_serial: str, command: str, value: Any) -> None:
        """Cache a command with its value and timestamp."""
        current_time = datetime.now(timezone.utc).isoformat()
        self.commands[(device_serial, command)] = (current_time, value)
        _LOGGER.debug("Cached command in device data: %s at %s", command, current_time)

    def apply(self, device_serial: str, device_detail: dict[str, Any]) -> None:
        """Cull stale commands and apply remaining cached values to device data."""
        if updated_at := device_detail.get("updatedAt"):
            self.cull(device_serial, updated_at)

        for (cached_device_serial, command), (_, command_value) in self.commands.items():
            if cached_device_serial == device_serial:
                device_detail[command] = command_value

    def cull(self, device_serial: str, updated_at: str | None) -> None:
        """Remove cached commands older than the cloud update timestamp."""
        input_date = _parse_timestamp(updated_at)
        if input_date is None:
            _LOGGER.debug("Skipping cached command cull for invalid timestamp: %s", updated_at)
            return

        to_remove = []
        for key, value in self.commands.items():
            cached_device_serial, command = key
            cached_date, _ = value
            cached_date_obj = _parse_timestamp(cached_date)
            if cached_date_obj is None:
                _LOGGER.debug(
                    "Skipping cached command with invalid timestamp: %s",
                    cached_date,
                )
                continue

            if cached_device_serial == device_serial and input_date > cached_date_obj:
                to_remove.append(key)
            else:
                _LOGGER.debug(
                    "Skipping cached command: cached_device_serial=%s, device_serial=%s, "
                    "input_date=%s, cached_date_obj=%s, date=%s, cached_date=%s",
                    cached_device_serial,
                    device_serial,
                    input_date,
                    cached_date_obj,
                    updated_at,
                    cached_date,
                )

        for key in to_remove:
            del self.commands[key]

        _LOGGER.debug(
            "Culled %d cached commands for device %s after %s. "
            "Remaining cached commands: %d",
            len(to_remove),
            device_serial,
            updated_at,
            len(self.commands),
        )


def _parse_timestamp(timestamp: str | None) -> datetime | None:
    """Parse an ISO timestamp as an aware datetime."""
    if not timestamp:
        return None

    try:
        parsed = datetime.fromisoformat(timestamp)
    except (TypeError, ValueError):
        return None

    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed
