"""Tests for Mitsubishi temperature conversion helpers."""

from __future__ import annotations

from custom_components.kumo_cloud import temperature


def test_fahrenheit_setpoints_use_mitsubishi_lookup() -> None:
    """Setpoints use Mitsubishi's non-standard F to C table."""
    assert temperature.f_to_c(69) == 21.0
    assert temperature.f_to_c(70) == 21.5
    assert temperature.f_to_c(71) == 22.0
    assert temperature.f_to_c(72) == 22.5


def test_celsius_display_uses_mitsubishi_lookup() -> None:
    """Displayed temperatures use the measured Mitsubishi C to F table."""
    assert temperature.c_to_f(20.5) == 69
    assert temperature.c_to_f(21.0) == 69
    assert temperature.c_to_f(22.0) == 71
    assert temperature.c_to_f(22.5) == 72


def test_unknown_values_fall_back_to_standard_rounding() -> None:
    """Values outside the lookup table use standard rounded conversion."""
    assert temperature.c_to_f(22.22223) == 72
    assert temperature.f_to_c(81) == 27.0


def test_none_passthrough() -> None:
    """Missing API values remain missing."""
    assert temperature.c_to_f(None) is None
    assert temperature.f_to_c(None) is None
