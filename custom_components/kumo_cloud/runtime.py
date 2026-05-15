"""Runtime data for the Kumo Cloud integration."""

from __future__ import annotations

from dataclasses import dataclass

from .api import KumoCloudAPI
from .coordinator import KumoCloudDataUpdateCoordinator


@dataclass(slots=True)
class KumoCloudRuntimeData:
    """Runtime objects associated with a Kumo Cloud config entry."""

    api: KumoCloudAPI
    coordinator: KumoCloudDataUpdateCoordinator
