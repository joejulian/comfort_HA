"""Manifest and metadata tests for the Kumo Cloud custom component."""

from __future__ import annotations

import json
from pathlib import Path

from custom_components.kumo_cloud.const import DOMAIN


MANIFEST = (
    Path(__file__).resolve().parents[1]
    / "custom_components"
    / DOMAIN
    / "manifest.json"
)


def test_manifest_declares_custom_component_metadata() -> None:
    """Manifest exposes the metadata Home Assistant expects."""
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))

    assert manifest["domain"] == DOMAIN
    assert manifest["name"] == "Mitsubishi Comfort"
    assert manifest["config_flow"] is True
    assert manifest["integration_type"] == "hub"
    assert manifest["iot_class"] == "cloud_polling"
    assert manifest["requirements"] == ["aiohttp>=3.8.0"]
