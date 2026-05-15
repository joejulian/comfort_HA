"""Import smoke tests for the Home Assistant integration modules."""

from __future__ import annotations

import importlib

import pytest


@pytest.mark.parametrize(
    "module",
    [
        "custom_components.kumo_cloud",
        "custom_components.kumo_cloud.api",
        "custom_components.kumo_cloud.climate",
        "custom_components.kumo_cloud.config_flow",
        "custom_components.kumo_cloud.coordinator",
        "custom_components.kumo_cloud.diagnostics",
        "custom_components.kumo_cloud.sensor",
    ],
)
def test_integration_modules_import(module: str) -> None:
    """Integration modules import under the Home Assistant test environment."""
    importlib.import_module(module)
