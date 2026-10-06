"""Offline regression coverage for the upstream automatic-station baseline."""

from custom_components.chmu import api

WSI = "0-203-0-11526"
CAPABILITIES = {
    "temperature",
    "humidity",
    "precipitation",
    "wind_speed",
    "wind_direction",
}


def test_meta1_identifies_rudolec_and_its_coordinates(rudolec_metadata):
    """Keep the real meta1 layout, including longitude before latitude."""
    rows = api._metadata_values(rudolec_metadata["meta1"])
    assert len(rows) == 1
    assert rows[0][:6] == [
        WSI,
        "P3NRUD01",
        "Nedrahovice, Rudolec",
        14.440088,
        49.631723,
        348.0,
    ]


def test_meta2_maps_supported_10m_elements(rudolec_session, rudolec_metadata):
    """Unmapped 10M elements and hourly vapor pressure are not air pressure."""
    rows = api._metadata_values(rudolec_metadata["meta2"])
    assert {row[1] for row in rows} == {WSI}
    assert "P" not in {row[2] for row in rows}
    assert any(row[0] == "1H" and row[2] == "E" for row in rows)
    assert any(row[0] == "10M" and row[2] == "Fmax" for row in rows)
    elements = api._fetch_station_elements(rudolec_session)
    assert set(elements) == {WSI}
    assert set(elements[WSI]) == CAPABILITIES
    assert len(elements[WSI]) == 5
    assert "pressure" not in elements[WSI]


def test_discovery_offers_rudolec_with_full_wsi(rudolec_session):
    """The public discovery path offers this small automatic station."""
    stations = api.get_stations_with_coords()
    assert set(stations) == {WSI}
    station = stations[WSI]
    assert station["name"] == "Nedrahovice, Rudolec"
    assert station["latitude"] == 49.631723
    assert station["longitude"] == 14.440088
    assert set(station["elements"]) == CAPABILITIES
    assert "pressure" not in station["elements"]
    urls = [call.args[0] for call in rudolec_session.get.call_args_list]
    assert len(urls) == 2
    assert "/meta2-" in urls[0]
    assert "/meta1-" in urls[1]


def test_automatic_wsi_is_preserved():
    """An automatic station must never be reduced to its numeric suffix."""
    assert api.wsi_to_station_id(WSI) == WSI
    assert api.station_id_to_wsi(WSI) == WSI
