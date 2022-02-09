"""Tests for the Roku select platform."""
from unittest.mock import MagicMock

import pytest
from rokuecp import Application, Device as RokuDevice, RokuError

from homeassistant.components.roku.coordinator import SCAN_INTERVAL
from homeassistant.components.select import DOMAIN as SELECT_DOMAIN
from homeassistant.components.select.const import ATTR_OPTION, ATTR_OPTIONS
from homeassistant.const import (
    ATTR_ENTITY_ID,
    ATTR_ICON,
    SERVICE_SELECT_OPTION,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
import homeassistant.util.dt as dt_util

from tests.common import MockConfigEntry, async_fire_time_changed


async def test_application_state(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    mock_device: RokuDevice,
    mock_roku: MagicMock,
) -> None:
    """Test the creation and values of the Roku selects."""
    entity_registry = er.async_get(hass)

    state = hass.states.get("select.my_roku_3_application")
    assert state
    assert state.attributes.get(ATTR_ICON) == "mdi:application"
    assert state.attributes.get(ATTR_OPTIONS) == [
        "Home",
        "Amazon Video on Demand",
        "Free FrameChannel Service",
        "MLB.TV" + "\u00AE",
        "Mediafly",
        "Netflix",
        "Pandora",
        "Pluto TV - It's Free TV",
        "Roku Channel Store",
    ]
    assert state.state == "Home"

    entry = entity_registry.async_get("select.my_roku_3_application")
    assert entry
    assert entry.unique_id == "1GU48T017973_application"

    await hass.services.async_call(
        SELECT_DOMAIN,
        SERVICE_SELECT_OPTION,
        {
            ATTR_ENTITY_ID: "select.my_roku_3_application",
            ATTR_OPTION: "Netflix",
        },
        blocking=True,
    )

    assert mock_roku.launch.call_count == 1
    mock_roku.launch.assert_called_with("12")
    mock_device.app = mock_device.apps[1]

    async_fire_time_changed(hass, dt_util.utcnow() + SCAN_INTERVAL)
    await hass.async_block_till_done()

    state = hass.states.get("select.my_roku_3_application")
    assert state

    assert state.state == "Netflix"

    await hass.services.async_call(
        SELECT_DOMAIN,
        SERVICE_SELECT_OPTION,
        {
            ATTR_ENTITY_ID: "select.my_roku_3_application",
            ATTR_OPTION: "Home",
        },
        blocking=True,
    )

    assert mock_roku.remote.call_count == 1
    mock_roku.remote.assert_called_with("home")
    mock_device.app = Application(
        app_id=None, name="Roku", version=None, screensaver=None
    )
    async_fire_time_changed(hass, dt_util.utcnow() + (SCAN_INTERVAL * 2))
    await hass.async_block_till_done()

    state = hass.states.get("select.my_roku_3_application")
    assert state
    assert state.state == "Home"


async def test_application_select_error(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    mock_roku: MagicMock,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test error handling of the Roku selects."""
    mock_roku.launch.side_effect = RokuError

    await hass.services.async_call(
        SELECT_DOMAIN,
        SERVICE_SELECT_OPTION,
        {
            ATTR_ENTITY_ID: "select.my_roku_3_application",
            ATTR_OPTION: "Netflix",
        },
        blocking=True,
    )

    state = hass.states.get("select.my_roku_3_application")
    assert state
    assert state.state == "Home"
    assert "Invalid response from API" in caplog.text
    assert mock_roku.launch.call_count == 1
    mock_roku.launch.assert_called_with("12")
