"""Station identity comparisons must not conflate WSI authorities or labels."""

from unittest.mock import patch

import pytest

from custom_components.chmu.identity import canonical_station_id, discovery_station_id


@pytest.mark.parametrize(
    ("station_id", "canonical"),
    [
        ("11450", "0-20000-0-11450"),
        ("0-20000-0-11450", "0-20000-0-11450"),
        ("0-203-0-11526", "0-203-0-11526"),
        ("0-203-0-11450", "0-203-0-11450"),
        ("0-999-0-11450", "0-999-0-11450"),
        ("1145", "1145"),
        ("011450", "011450"),
    ],
)
def test_canonical_identity(station_id, canonical):
    assert canonical_station_id(station_id) == canonical
    assert canonical_station_id(canonical) == canonical


def test_only_professional_wsi_has_a_short_discovery_alias():
    assert discovery_station_id("0-20000-0-11450") == "11450"
    assert discovery_station_id("0-203-0-11526") == "0-203-0-11526"
    assert canonical_station_id("11526") != canonical_station_id("0-203-0-11526")


def test_capability_fetch_does_not_use_approximate_fallback():
    from custom_components.chmu.api import get_stations_with_coords

    with patch(
        "custom_components.chmu.api._fetch_station_elements",
        side_effect=ConnectionError,
    ):
        with pytest.raises(ConnectionError):
            get_stations_with_coords(allow_fallback=False)
        assert get_stations_with_coords()  # the public discovery default is preserved
