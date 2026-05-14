"""Mitsubishi API/UI value mappings."""

from __future__ import annotations


# The V3 API uses internal speed names that do not match what the Comfort app
# or physical remote displays. This mapping translates between the two.
API_TO_UI_FAN = {
    "auto": "auto",
    "superQuiet": "quiet",
    "quiet": "low",
    "low": "medium",
    "powerful": "high",
    "superPowerful": "powerful",
}
UI_TO_API_FAN = {
    "auto": "auto",
    "quiet": "superQuiet",
    "low": "quiet",
    "medium": "low",
    "high": "powerful",
    "powerful": "superPowerful",
}
UI_FAN_ORDER = ["auto", "quiet", "low", "medium", "high", "powerful"]


API_TO_UI_VANE = {
    "auto": "auto",
    "swing": "swing",
    "vertical": "lowest",
    "midvertical": "low",
    "midpoint": "middle",
    "midhorizontal": "high",
    "horizontal": "highest",
}
UI_TO_API_VANE = {
    "auto": "auto",
    "swing": "swing",
    "lowest": "vertical",
    "low": "midvertical",
    "middle": "midpoint",
    "high": "midhorizontal",
    "highest": "horizontal",
}
UI_VANE_ORDER = ["auto", "swing", "lowest", "low", "middle", "high", "highest"]
