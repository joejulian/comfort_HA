"""Tests for Kumo Cloud config entry setup and unload."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from homeassistant.const import CONF_USERNAME
from homeassistant.exceptions import ConfigEntryNotReady
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.kumo_cloud import PLATFORMS
from custom_components.kumo_cloud import async_setup_entry, async_unload_entry
from custom_components.kumo_cloud.api import KumoCloudConnectionError
from custom_components.kumo_cloud.const import CONF_SITE_ID, DOMAIN


@pytest.fixture
def config_entry() -> MockConfigEntry:
    """Return a token-based Kumo Cloud config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        title="Kumo Cloud - Home",
        data={
            CONF_USERNAME: "user@example.invalid",
            CONF_SITE_ID: "site-1",
            "access_token": "access-token",
            "refresh_token": "refresh-token",
        },
    )


@pytest.fixture
def mock_api() -> AsyncMock:
    """Return a mocked Kumo Cloud API client."""
    api = AsyncMock()
    api.access_token = None
    api.refresh_token = None
    api.get_account_info = AsyncMock(return_value={"id": "account-1"})
    api.login = AsyncMock()
    return api


@pytest.fixture
def mock_coordinator() -> AsyncMock:
    """Return a mocked data update coordinator."""
    coordinator = AsyncMock()
    coordinator.async_config_entry_first_refresh = AsyncMock()
    return coordinator


async def test_token_based_setup_stores_coordinator_and_forwards_platforms(
    hass,
    monkeypatch: pytest.MonkeyPatch,
    config_entry: MockConfigEntry,
    mock_api: AsyncMock,
    mock_coordinator: AsyncMock,
) -> None:
    """Token-based setup verifies the token, stores runtime data, and forwards platforms."""
    config_entry.add_to_hass(hass)
    forward_setups = AsyncMock()
    monkeypatch.setattr(
        "custom_components.kumo_cloud.KumoCloudAPI",
        lambda hass_arg: mock_api,
    )
    monkeypatch.setattr(
        "custom_components.kumo_cloud.KumoCloudDataUpdateCoordinator",
        lambda hass_arg, api_arg, site_id_arg: mock_coordinator,
    )
    monkeypatch.setattr(hass.config_entries, "async_forward_entry_setups", forward_setups)

    assert await async_setup_entry(hass, config_entry)

    assert mock_api.username == "user@example.invalid"
    assert mock_api.access_token == "access-token"
    assert mock_api.refresh_token == "refresh-token"
    mock_api.get_account_info.assert_awaited_once()
    mock_api.login.assert_not_awaited()
    mock_coordinator.async_config_entry_first_refresh.assert_awaited_once()
    assert hass.data[DOMAIN][config_entry.entry_id] is mock_coordinator
    forward_setups.assert_awaited_once_with(config_entry, PLATFORMS)


async def test_unload_entry_removes_runtime_data(
    hass,
    monkeypatch: pytest.MonkeyPatch,
    config_entry: MockConfigEntry,
    mock_coordinator: AsyncMock,
) -> None:
    """Unload removes the stored coordinator when platforms unload successfully."""
    config_entry.add_to_hass(hass)
    hass.data.setdefault(DOMAIN, {})[config_entry.entry_id] = mock_coordinator
    unload_platforms = AsyncMock(return_value=True)
    monkeypatch.setattr(hass.config_entries, "async_unload_platforms", unload_platforms)

    assert await async_unload_entry(hass, config_entry)

    unload_platforms.assert_awaited_once_with(config_entry, PLATFORMS)
    assert config_entry.entry_id not in hass.data[DOMAIN]


async def test_transient_connection_failure_raises_config_entry_not_ready(
    hass,
    monkeypatch: pytest.MonkeyPatch,
    config_entry: MockConfigEntry,
    mock_api: AsyncMock,
    mock_coordinator: AsyncMock,
) -> None:
    """Transient API connection failures are retryable setup failures."""
    config_entry.add_to_hass(hass)
    mock_api.get_account_info.side_effect = KumoCloudConnectionError("DNS failure")
    monkeypatch.setattr(
        "custom_components.kumo_cloud.KumoCloudAPI",
        lambda hass_arg: mock_api,
    )
    monkeypatch.setattr(
        "custom_components.kumo_cloud.KumoCloudDataUpdateCoordinator",
        lambda hass_arg, api_arg, site_id_arg: mock_coordinator,
    )

    with pytest.raises(ConfigEntryNotReady):
        await async_setup_entry(hass, config_entry)

    mock_coordinator.async_config_entry_first_refresh.assert_not_awaited()
    assert DOMAIN not in hass.data
