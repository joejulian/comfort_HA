"""Tests for Mitsubishi API/UI mappings."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest

MAPPINGS_MODULE = (
    Path(__file__).resolve().parents[1]
    / "custom_components"
    / "kumo_cloud"
    / "mappings.py"
)
spec = importlib.util.spec_from_file_location("kumo_mappings", MAPPINGS_MODULE)
assert spec is not None
mappings = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(mappings)


class MappingsTest(unittest.TestCase):
    """Verify Comfort app label translations."""

    def test_fan_speed_mappings(self) -> None:
        """Fan speeds map between Kumo API values and UI labels."""
        self.assertEqual(mappings.API_TO_UI_FAN["superQuiet"], "quiet")
        self.assertEqual(mappings.API_TO_UI_FAN["quiet"], "low")
        self.assertEqual(mappings.UI_TO_API_FAN["high"], "powerful")
        self.assertEqual(mappings.UI_TO_API_FAN["powerful"], "superPowerful")

    def test_vane_mappings(self) -> None:
        """Vane positions map between Kumo API values and UI labels."""
        self.assertEqual(mappings.API_TO_UI_VANE["vertical"], "lowest")
        self.assertEqual(mappings.API_TO_UI_VANE["horizontal"], "highest")
        self.assertEqual(mappings.UI_TO_API_VANE["middle"], "midpoint")
        self.assertEqual(mappings.UI_TO_API_VANE["high"], "midhorizontal")

    def test_orderings_are_stable(self) -> None:
        """Ordered UI modes preserve expected progression."""
        self.assertEqual(
            mappings.UI_FAN_ORDER,
            ["auto", "quiet", "low", "medium", "high", "powerful"],
        )
        self.assertEqual(
            mappings.UI_VANE_ORDER,
            ["auto", "swing", "lowest", "low", "middle", "high", "highest"],
        )


if __name__ == "__main__":
    unittest.main()
