# Legacy 1.4.2 fixture provenance

Schema is taken from `custom_components/chmu/config_flow.py` and `const.py`
at legacy commit `a4a07831ddaa0605a0d2bdaa6f89d77bc4500a90`.
The flow sets VERSION=1 (default minor version 1), unique_id=station_id,
title="name (station_id)", and stores exactly station_id, station_name,
station_latitude and station_longitude. It has no options flow or capabilities.
Coordinates/name/WSI come from the captured Rudolec meta1 fixture.
This represents the entry produced by that flow, not an export of real HA storage.

Legacy sensor unique IDs are `{station_id}_{temperature,humidity,pressure,
precipitation,wind_speed,wind_direction}`; weather is `{station_id}_weather`.
Every entity uses device identifiers `{("chmu", station_id)}`. Registry fixtures
in the harness tests use these IDs plus intentionally user-chosen entity IDs.
