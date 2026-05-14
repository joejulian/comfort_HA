"""Tests for Mitsubishi temperature conversion helpers."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest

TEMPERATURE_MODULE = (
    Path(__file__).resolve().parents[1]
    / "custom_components"
    / "kumo_cloud"
    / "temperature.py"
)
spec = importlib.util.spec_from_file_location("kumo_temperature", TEMPERATURE_MODULE)
assert spec is not None
temperature = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(temperature)


class TemperatureConversionTest(unittest.TestCase):
    """Verify Mitsubishi-specific Fahrenheit/Celsius mapping."""

    def test_fahrenheit_setpoints_use_mitsubishi_lookup(self) -> None:
        """Setpoints use Mitsubishi's non-standard F to C table."""
        self.assertEqual(temperature.f_to_c(69), 21.0)
        self.assertEqual(temperature.f_to_c(70), 21.5)
        self.assertEqual(temperature.f_to_c(71), 22.0)
        self.assertEqual(temperature.f_to_c(72), 22.5)

    def test_celsius_display_uses_mitsubishi_lookup(self) -> None:
        """Displayed temperatures use the measured Mitsubishi C to F table."""
        self.assertEqual(temperature.c_to_f(20.5), 69)
        self.assertEqual(temperature.c_to_f(21.0), 69)
        self.assertEqual(temperature.c_to_f(22.0), 71)
        self.assertEqual(temperature.c_to_f(22.5), 72)

    def test_unknown_values_fall_back_to_standard_rounding(self) -> None:
        """Values outside the lookup table use standard rounded conversion."""
        self.assertEqual(temperature.c_to_f(22.22223), 72)
        self.assertEqual(temperature.f_to_c(81), 27.0)

    def test_none_passthrough(self) -> None:
        """Missing API values remain missing."""
        self.assertIsNone(temperature.c_to_f(None))
        self.assertIsNone(temperature.f_to_c(None))


if __name__ == "__main__":
    unittest.main()
