"""Real HA availability and entry-owned HTTP session lifecycle."""

import json
from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import requests

pytest.importorskip("pytest_homeassistant_custom_component")

from homeassistant.helpers import entity_registry as er  # noqa: E402
from pytest_homeassistant_custom_component.common import MockConfigEntry  # noqa: E402

from custom_components.chmu import api  # noqa: E402
from custom_components.chmu.const import DOMAIN  # noqa: E402

WSI = "0-203-0-11526"
NOW = datetime(2026, 10, 7, 12, tzinfo=UTC)
KEYS = ["temperature", "humidity", "precipitation", "wind_speed", "wind_direction"]


@pytest.fixture(autouse=True)
def enable_custom_integrations(enable_custom_integrations):
    return enable_custom_integrations


@pytest.fixture
def http(monkeypatch):
    document = json.loads(
        (Path(__file__).parent / "fixtures/rudolec/observations.json").read_text()
    )
    sessions = []

    def session_factory():
        session = MagicMock()
        session.headers = {}

        def get(url, **kwargs):
            assert "/now/data/10m-" in url, url
            if document.get("transport_failure"):
                raise requests.Timeout("synthetic failed setup")
            result = MagicMock()
            result.json.return_value = deepcopy(document)
            return result

        session.get.side_effect = get
        sessions.append(session)
        return session

    monkeypatch.setattr(api.requests, "Session", session_factory)
    monkeypatch.setattr(api, "utcnow", lambda: NOW)
    with (
        patch(
            "custom_components.chmu.api.ChmuApi._fetch_latest_cr_text_forecast",
            return_value={},
        ),
        patch(
            "custom_components.chmu.forecast.ChmuForecastApi.get_forecast",
            return_value=None,
        ),
    ):
        yield document, sessions


def new_entry(hass):
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=WSI,
        minor_version=2,
        data={
            "station_id": WSI,
            "station_name": "Nedrahovice, Rudolec",
            "station_elements": KEYS,
        },
    )
    entry.add_to_hass(hass)
    return entry


def sensor_state(hass, key):
    entity_id = er.async_get(hass).async_get_entity_id("sensor", DOMAIN, f"{WSI}_{key}")
    assert entity_id is not None
    state = hass.states.get(entity_id)
    assert state is not None
    return state


@pytest.mark.parametrize(
    ("element", "key", "stamp", "expected"),
    [
        ("F", "wind_speed", "2026-10-07T08:00:00Z", "stale"),
        ("T", "temperature", "2026-10-07T08:00:00Z", "stale"),
        ("F", "wind_speed", "2026-10-07T04:00:00Z", "unusable"),
    ],
)
async def test_partial_observations_and_measured_at(
    hass, http, element, key, stamp, expected
):
    document, sessions = http
    for row in document["data"]["data"]["values"]:
        if row[1] == element:
            row[2] = stamp
    entry = new_entry(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done(wait_background_tasks=True)
    assert entry.runtime_data.coordinator.last_update_success
    state = sensor_state(hass, key)
    entity = hass.data["sensor"].get_entity(state.entity_id)
    assert entity is not None
    attributes = entity.extra_state_attributes
    assert attributes is not None
    assert attributes["measurement_state"] == expected
    assert attributes["measured_at"] == stamp
    if expected == "unusable":
        # Core only publishes extra_state_attributes when an entity is available.
        assert "measurement_state" not in state.attributes
    else:
        assert state.attributes["measurement_state"] == expected
        assert state.attributes["measured_at"] == stamp
    assert (state.state == "unavailable") is (expected == "unusable")
    humidity = sensor_state(hass, "humidity")
    assert humidity.state not in ("unknown", "unavailable")
    assert humidity.attributes["measured_at"] == "2026-10-07T11:50:00Z"
    assert humidity.attributes["quality"] == 5
    assert await hass.config_entries.async_unload(entry.entry_id)
    assert len(sessions) == 2
    for session in sessions:
        session.close.assert_called_once()


async def test_missing_element_and_zero_are_per_element(hass, http):
    document, _ = http
    document["data"]["data"]["values"] = [
        row for row in document["data"]["data"]["values"] if row[1] != "H"
    ]
    entry = new_entry(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done(wait_background_tasks=True)
    assert entry.runtime_data.coordinator.last_update_success
    assert sensor_state(hass, "humidity").state == "unavailable"
    humidity = sensor_state(hass, "humidity")
    entity = hass.data["sensor"].get_entity(humidity.entity_id)
    assert entity is not None
    assert entity.extra_state_attributes == {"measurement_state": "missing"}
    assert "measurement_state" not in humidity.attributes
    assert float(sensor_state(hass, "precipitation").state) == 0
    assert float(sensor_state(hass, "wind_speed").state) == 0
    assert await hass.config_entries.async_unload(entry.entry_id)


async def test_transport_failure_is_failed_poll(hass, http):
    _, sessions = http
    entry = new_entry(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done(wait_background_tasks=True)
    sessions[0].get.side_effect = requests.Timeout
    await entry.runtime_data.coordinator.async_request_refresh()
    await hass.async_block_till_done()
    assert not entry.runtime_data.coordinator.last_update_success
    assert sensor_state(hass, "temperature").state == "unavailable"
    assert await hass.config_entries.async_unload(entry.entry_id)


@pytest.mark.parametrize("failure", ["transport", "missing", "all_unusable"])
async def test_failed_setup_closes_sessions(hass, http, failure):
    document, sessions = http
    if failure == "all_unusable":
        for row in document["data"]["data"]["values"]:
            row[2] = "2026-10-07T00:00:00Z"
    elif failure == "missing":
        document["data"]["data"]["values"] = []
    else:
        document["transport_failure"] = True
    entry = new_entry(hass)
    assert not await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done(wait_background_tasks=True)
    assert len(sessions) == 2
    for session in sessions:
        session.close.assert_called_once()
    assert not er.async_entries_for_config_entry(er.async_get(hass), entry.entry_id)


async def test_reload_and_repeated_setup_do_not_leak_sessions(hass, http):
    _, sessions = http
    entry = new_entry(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done(wait_background_tasks=True)
    assert len(sessions) == 2
    assert await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done(wait_background_tasks=True)
    assert len(sessions) == 4
    for session in sessions[:2]:
        session.close.assert_called_once()
    assert await hass.config_entries.async_unload(entry.entry_id)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done(wait_background_tasks=True)
    assert len(sessions) == 6
    assert await hass.config_entries.async_unload(entry.entry_id)
    for session in sessions:
        session.close.assert_called_once()
