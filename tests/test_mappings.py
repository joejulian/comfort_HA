"""Tests for Mitsubishi API/UI mappings."""

from __future__ import annotations

from custom_components.kumo_cloud import mappings


def test_fan_speed_mappings() -> None:
    """Fan speeds map between Kumo API values and UI labels."""
    assert mappings.API_TO_UI_FAN["superQuiet"] == "quiet"
    assert mappings.API_TO_UI_FAN["quiet"] == "low"
    assert mappings.UI_TO_API_FAN["high"] == "powerful"
    assert mappings.UI_TO_API_FAN["powerful"] == "superPowerful"


def test_vane_mappings() -> None:
    """Vane positions map between Kumo API values and UI labels."""
    assert mappings.API_TO_UI_VANE["vertical"] == "lowest"
    assert mappings.API_TO_UI_VANE["horizontal"] == "highest"
    assert mappings.UI_TO_API_VANE["middle"] == "midpoint"
    assert mappings.UI_TO_API_VANE["high"] == "midhorizontal"


def test_orderings_are_stable() -> None:
    """Ordered UI modes preserve expected progression."""
    assert mappings.UI_FAN_ORDER == [
        "auto",
        "quiet",
        "low",
        "medium",
        "high",
        "powerful",
    ]
    assert mappings.UI_VANE_ORDER == [
        "auto",
        "swing",
        "lowest",
        "low",
        "middle",
        "high",
        "highest",
    ]
