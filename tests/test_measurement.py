"""Offline UTC, row quality, partial observations and resource regressions."""

import json
from copy import deepcopy
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch
from zoneinfo import ZoneInfo

import pytest
import requests

from custom_components.chmu import api

NOW = datetime(2026, 10, 7, 12, tzinfo=UTC)
WSI = "0-203-0-11526"


@pytest.fixture
def observations():
    return json.loads(
        (Path(__file__).parent / "fixtures/rudolec/observations.json").read_text()
    )


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(api, "utcnow", lambda: NOW)
    session = MagicMock()
    monkeypatch.setattr(api, "new_session", lambda: session)
    result = api.ChmuApi(WSI)
    yield result
    result.close()


def checked(client, document):
    data = client._parse_chmu_data(document)
    client._check_freshness(data, NOW)
    return data


@pytest.mark.parametrize(
    "instant",
    [
        "2026-10-07T12:00:00+00:00",  # normal day
        "2026-07-07T00:30:00+02:00",  # Prague midnight before UTC midnight
        "2026-01-07T00:30:00+01:00",  # CET
        "2026-03-29T01:30:00+01:00",
        "2026-03-29T03:30:00+02:00",
        "2026-10-25T02:30:00+02:00",
        "2026-10-25T02:30:00+01:00",
    ],
)
def test_utc_candidates_and_filenames(client, monkeypatch, instant):
    local = datetime.fromisoformat(instant).astimezone(ZoneInfo("Europe/Prague"))
    expected = local.astimezone(UTC)
    monkeypatch.setattr(api, "utcnow", lambda: expected)
    current, previous = api._utc_day_candidates()
    assert current == expected and current.tzinfo is UTC
    assert previous == expected - timedelta(days=1)
    response = MagicMock()
    response.json.return_value = {"data": {"data": {"values": []}}}
    client.session.get.return_value = response
    assert client._fetch_10min_data(current) is None
    assert client._fetch_10min_data(previous) is None
    urls = [call.args[0] for call in client.session.get.call_args_list]
    assert urls[0].endswith(expected.strftime("%Y%m%d") + ".json")
    assert urls[1].endswith(previous.strftime("%Y%m%d") + ".json")


def response(status, payload=None):
    result = MagicMock()
    result.status_code = status
    if status >= 400:
        result.raise_for_status.side_effect = requests.HTTPError(response=result)
    result.json.return_value = payload
    return result


def test_previous_day_404_fallback(client, observations, monkeypatch):
    now = datetime(2026, 10, 8, 0, 30, tzinfo=UTC)
    monkeypatch.setattr(api, "utcnow", lambda: now)
    for row in observations["data"]["data"]["values"]:
        row[2] = "2026-10-07T23:50:00Z"
    client.session.get.side_effect = [response(404), response(200, observations)]
    data = client._fetch_10min_data_with_fallback()
    assert data["temperature"] == 18.8
    assert client.session.get.call_count == 2
    assert client.session.get.call_args_list[1].args[0].endswith("20261007.json")


@pytest.mark.parametrize(
    "failure", [requests.Timeout(), requests.ConnectionError(), requests.HTTPError()]
)
def test_transport_never_falls_back(client, failure):
    client.session.get.side_effect = failure
    with pytest.raises(type(failure)):
        client._fetch_10min_data_with_fallback()
    assert client.session.get.call_count == 1


def test_server_500_never_falls_back(client):
    client.session.get.return_value = response(500)
    with pytest.raises(requests.HTTPError):
        client._fetch_10min_data_with_fallback()
    assert client.session.get.call_count == 1


def test_malformed_json_never_falls_back(client):
    broken = response(200)
    broken.json.side_effect = requests.exceptions.JSONDecodeError("broken", "", 0)
    client.session.get.return_value = broken
    with pytest.raises(requests.exceptions.JSONDecodeError):
        client._fetch_10min_data_with_fallback()
    assert client.session.get.call_count == 1


@pytest.mark.parametrize("values", [None, {}, "wrong", 12])
def test_wrong_values_shape_is_not_a_missing_day(client, values):
    client.session.get.return_value = response(
        200, {"data": {"data": {"values": values}}}
    )
    with pytest.raises(ValueError, match="expected an array"):
        client._fetch_10min_data_with_fallback()
    assert client.session.get.call_count == 1


@pytest.mark.parametrize(
    ("element", "key"), [("F", "wind_speed"), ("T", "temperature")]
)
def test_per_element_age_and_source_time(client, observations, element, key):
    for row in observations["data"]["data"]["values"]:
        if row[1] == element:
            row[2] = "2026-10-07T08:00:00Z"
    data = checked(client, observations)
    assert data["measurements"][key].state == "stale"
    assert data["measurements"][key].measured_at == NOW - timedelta(hours=4)
    assert data["measurements"]["humidity"].state == "fresh"
    assert data[key] is not None


def test_unusable_wind_does_not_drop_fresh_temperature(client, observations):
    for row in observations["data"]["data"]["values"]:
        if row[1] == "F":
            row[2] = "2026-10-07T04:00:00Z"
    data = checked(client, observations)
    assert data["temperature"] == 18.8
    assert data["wind_speed"] is None
    assert data["measurements"]["wind_speed"].state == "unusable"


def test_zero_values_and_quality_5_are_usable(client, observations):
    data = checked(client, observations)
    assert data["precipitation"] == 0.0 and data["wind_speed"] == 0.0
    assert all(row.usable and row.quality == 5 for row in data["measurements"].values())


@pytest.mark.parametrize(
    ("quality", "state", "usable"),
    [
        (0, "fresh", True),
        (1, "fresh", True),
        (2, "invalid_quality", False),
        (3, "fresh", True),
        (4, "missing", False),
        (5, "fresh", True),
        (99, "fresh", True),
    ],
)
def test_raw_quality_policy(client, observations, quality, state, usable):
    observations["data"]["data"]["values"][0][5] = quality
    data = checked(client, observations)
    row = data["measurements"]["temperature"]
    assert row.quality == quality and row.state == state and row.usable is usable
    assert (data["temperature"] is not None) is usable
    assert ("temperature" in data["history"]) is usable


@pytest.mark.parametrize("value", [None, "", "bad", float("nan"), float("inf"), True])
def test_missing_or_invalid_value_is_local(client, observations, value):
    observations["data"]["data"]["values"][0][3] = value
    data = checked(client, observations)
    assert data["temperature"] is None
    assert data["measurements"]["temperature"].state == "missing"
    assert data["humidity"] == 58


@pytest.mark.parametrize(
    "stamp", ["bad", "2026-10-07T11:50:00", "2026-10-07T13:00:00Z"]
)
def test_invalid_or_future_time_is_not_current(client, observations, stamp):
    observations["data"]["data"]["values"][0][2] = stamp
    data = checked(client, observations)
    assert not data["measurements"]["temperature"].usable
    assert data["temperature"] is None
    assert "temperature" not in data["history"]


def test_missing_element_does_not_make_station_fail(client, observations):
    observations["data"]["data"]["values"] = observations["data"]["data"]["values"][:1]
    data = checked(client, observations)
    assert data["temperature"] == 18.8
    assert "humidity" not in data["measurements"]


def test_all_elements_unusable(client, observations):
    for row in observations["data"]["data"]["values"]:
        row[2] = "2026-10-07T00:00:00Z"
    with pytest.raises(api.MeasurementUnusable):
        checked(client, observations)


@pytest.mark.parametrize(
    ("age", "state"),
    [(120, "fresh"), (121, "stale"), (360, "stale"), (361, "unusable")],
)
def test_freshness_boundaries(client, observations, age, state):
    observations["data"]["data"]["values"][0][2] = (
        NOW - timedelta(minutes=age)
    ).isoformat()
    data = checked(client, observations)
    assert data["measurements"]["temperature"].state == state


def test_latest_row_is_ordered_by_utc_instant(client, observations):
    older = deepcopy(observations["data"]["data"]["values"][0])
    older[2], older[3] = "2026-10-07T13:00:00+02:00", 99
    observations["data"]["data"]["values"].append(older)
    data = checked(client, observations)
    assert data["temperature"] == 18.8
    assert data["measurements"]["temperature"].measured_at.tzinfo is UTC


def test_discovery_closes_session_on_failure_and_success(client):
    with (
        patch(
            "custom_components.chmu.api._fetch_station_elements",
            side_effect=ConnectionError,
        ),
        pytest.raises(ConnectionError),
    ):
        api.get_stations_with_coords(allow_fallback=False)
    client.session.close.assert_called_once()
    client.session.close.reset_mock()
    with (
        patch("custom_components.chmu.api._fetch_station_elements", return_value={}),
        patch(
            "custom_components.chmu.api._fetch_metadata_with_fallback", return_value={}
        ),
    ):
        assert api.get_stations_with_coords(allow_fallback=False) == {}
    client.session.close.assert_called_once()
