"""Upgrade legacy entries and real registries, without touching HA storage."""

import json
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

pytest.importorskip("pytest_homeassistant_custom_component")

from homeassistant.config_entries import SOURCE_USER  # noqa: E402
from homeassistant.data_entry_flow import FlowResultType  # noqa: E402
from homeassistant.helpers import device_registry as dr  # noqa: E402
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry  # noqa: E402

from custom_components.chmu import async_migrate_entry  # noqa: E402
from custom_components.chmu.const import DOMAIN  # noqa: E402

WSI = "0-203-0-11526"
KEYS = {"temperature", "humidity", "precipitation", "wind_speed", "wind_direction"}


@pytest.fixture(autouse=True)
def enable_custom_integrations(enable_custom_integrations):
    return enable_custom_integrations


@pytest.fixture
def legacy_entry(hass):
    fixture = Path(__file__).parent / "fixtures/legacy/rudolec-entry.json"
    entry = MockConfigEntry(domain=DOMAIN, **json.loads(fixture.read_text()))
    entry.add_to_hass(hass)
    return entry


@pytest.fixture(autouse=True)
def offline_measurements():
    with (
        patch(
            "custom_components.chmu.api.ChmuApi.get_current_data",
            return_value={
                "temperature": 18.8,
                "humidity": 58,
                "precipitation": 0.0,
                "wind_speed": 0.5,
                "wind_direction": 43,
            },
        ),
        patch(
            "custom_components.chmu.forecast.ChmuForecastApi.get_forecast",
            return_value=None,
        ),
    ):
        yield


def seed_legacy_registries(hass, entry):
    device = dr.async_get(hass).async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, entry.data["station_id"])},
        name=entry.data["station_name"],
    )
    registry = er.async_get(hass)
    records = {}
    for key in sorted(KEYS | {"pressure", "weather"}):
        record = registry.async_get_or_create(
            "weather" if key == "weather" else "sensor",
            DOMAIN,
            f"{entry.data['station_id']}_{key}",
            config_entry=entry,
            device_id=device.id,
            suggested_object_id=f"my_custom_rudolec_{key}",
        )
        records[key] = (record.id, record.entity_id, record.unique_id, record.device_id)
    return device, records


async def test_legacy_upgrade_preserves_registries_and_pressure(
    hass, legacy_entry, rudolec_session
):
    entry = legacy_entry
    original_data = dict(entry.data)
    original_options = dict(entry.options)
    device, records = seed_legacy_registries(hass, entry)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done(wait_background_tasks=True)
    assert entry.minor_version == 2
    assert entry.version == 1
    assert entry.unique_id == WSI
    assert set(entry.data["station_elements"]) == KEYS
    assert {k: entry.data[k] for k in original_data} == original_data
    assert dict(entry.options) == original_options
    assert hass.config_entries.async_entries(DOMAIN) == [entry]
    registry = er.async_get(hass)
    for expected in records.values():
        record = registry.async_get(expected[1])
        assert record is not None
        assert (
            record.id,
            record.entity_id,
            record.unique_id,
            record.device_id,
        ) == expected
    devices = dr.async_entries_for_config_entry(dr.async_get(hass), entry.entry_id)
    assert [item.id for item in devices] == [device.id]
    entities = er.async_entries_for_config_entry(registry, entry.entry_id)
    assert len(entities) == 8  # seven legacy records plus new text forecast
    for key in KEYS:
        state = hass.states.get(records[key][1])
        assert state is not None and state.state not in ("unknown", "unavailable")
    await hass.async_start()
    await hass.async_block_till_done()
    pressure = registry.async_get(records["pressure"][1])
    assert pressure is not None and pressure.disabled_by is None
    assert pressure.config_entry_id == entry.entry_id
    state = hass.states.get(pressure.entity_id)
    assert state is not None and state.state == "unavailable"
    assert state.attributes["restored"] is True
    # Reload is idempotent and retains the exact registry IDs/user entity IDs.
    data_after = dict(entry.data)
    assert await async_migrate_entry(hass, entry)
    assert await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done(wait_background_tasks=True)
    assert dict(entry.data) == data_after
    for expected in records.values():
        record = registry.async_get(expected[1])
        assert record is not None
        assert (
            record.id,
            record.entity_id,
            record.unique_id,
            record.device_id,
        ) == expected
    assert len(er.async_entries_for_config_entry(registry, entry.entry_id)) == 8
    assert (
        len(dr.async_entries_for_config_entry(dr.async_get(hass), entry.entry_id)) == 1
    )
    assert await hass.config_entries.async_unload(entry.entry_id)


async def test_metadata_outage_then_refresh(hass, legacy_entry, rudolec_station):
    entry = legacy_entry
    device, records = seed_legacy_registries(hass, entry)
    with patch(
        "custom_components.chmu.get_stations_with_coords", side_effect=ConnectionError
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done(wait_background_tasks=True)
    assert entry.minor_version == 2
    assert entry.unique_id == WSI and entry.data["station_id"] == WSI
    assert "station_elements" not in entry.data
    state = hass.states.get(records["pressure"][1])
    assert state is not None and state.state == "unknown"
    with patch(
        "custom_components.chmu.get_stations_with_coords",
        return_value={WSI: rudolec_station},
    ):
        await entry.runtime_data.coordinator.async_request_refresh()
        await hass.async_block_till_done(wait_background_tasks=True)
    assert set(entry.data["station_elements"]) == KEYS
    assert len(hass.config_entries.async_entries(DOMAIN)) == 1
    current_device = dr.async_get(hass).async_get_device_by_identifier(
        (DOMAIN, WSI), entry.entry_id
    )
    assert current_device is not None and current_device.id == device.id
    pressure = er.async_get(hass).async_get(records["pressure"][1])
    assert pressure is not None and pressure.id == records["pressure"][0]
    state = hass.states.get(pressure.entity_id)
    assert state is not None and state.state == "unavailable"
    assert await hass.config_entries.async_unload(entry.entry_id)


async def test_offline_schema_migration_is_idempotent(hass, legacy_entry):
    entry = legacy_entry
    original = (entry.entry_id, entry.unique_id, dict(entry.data), dict(entry.options))
    with patch(
        "custom_components.chmu.get_stations_with_coords",
        side_effect=AssertionError("no network"),
    ):
        assert await async_migrate_entry(hass, entry)
        assert await async_migrate_entry(hass, entry)
    assert entry.minor_version == 2
    assert (
        entry.entry_id,
        entry.unique_id,
        dict(entry.data),
        dict(entry.options),
    ) == original


@pytest.mark.parametrize(
    ("stored", "offered"),
    [
        (WSI, WSI),
        ("0-20000-0-11450", "11450"),
        ("11450", "0-20000-0-11450"),
    ],
)
async def test_duplicate_aliases(hass, rudolec_station, stored, offered):
    entry = MockConfigEntry(
        domain=DOMAIN, unique_id=stored, data={"station_id": stored}
    )
    entry.add_to_hass(hass)
    with patch(
        "custom_components.chmu.config_flow.get_stations_with_coords",
        return_value={offered: rudolec_station},
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"station_id": offered}
        )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"
    assert hass.config_entries.async_entries(DOMAIN) == [entry]


async def test_same_names_are_distinct_and_discovery_is_cached(hass, rudolec_station):
    other = "0-203-0-11527"
    stations = {WSI: rudolec_station, other: dict(rudolec_station)}
    with (
        patch(
            "custom_components.chmu.config_flow.get_stations_with_coords",
            return_value=stations,
        ) as discovery,
        patch(
            "custom_components.chmu.async_setup_entry", new=AsyncMock(return_value=True)
        ),
    ):
        for station_id in (WSI, other):
            result = await hass.config_entries.flow.async_init(
                DOMAIN, context={"source": SOURCE_USER}
            )
            before = discovery.call_count
            result = await hass.config_entries.flow.async_configure(
                result["flow_id"], {"station_id": station_id}
            )
            assert result["type"] is FlowResultType.CREATE_ENTRY
            assert discovery.call_count == before  # no submit-time refetch
        await hass.async_block_till_done()
    assert {entry.unique_id for entry in hass.config_entries.async_entries(DOMAIN)} == {
        WSI,
        other,
    }


async def test_zero_coordinate_default(hass, rudolec_station):
    hass.config.latitude = 0
    hass.config.longitude = 0
    stations = {WSI: {**rudolec_station, "latitude": 0, "longitude": 0}}
    with patch(
        "custom_components.chmu.config_flow.get_stations_with_coords",
        return_value=stations,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}
        )
    assert next(iter(result["data_schema"].schema)).default() == WSI


async def test_forged_selection_is_rejected(hass, rudolec_station):
    from custom_components.chmu.config_flow import ChmuConfigFlow

    flow = ChmuConfigFlow()
    flow.hass = hass
    with patch(
        "custom_components.chmu.config_flow.get_stations_with_coords",
        return_value={WSI: rudolec_station},
    ) as discovery:
        await flow.async_step_user()
        result = await flow.async_step_user({"station_id": "0-203-0-99999"})
    assert (
        result.get("type") is FlowResultType.ABORT
        and result.get("reason") == "invalid_station"
    )
    discovery.assert_called_once()
    assert not hass.config_entries.async_entries(DOMAIN)


async def test_professional_full_id_keeps_existing_registry_identity(
    hass, rudolec_station
):
    station_id = "0-20000-0-11450"
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=station_id,
        data={
            "station_id": station_id,
            "station_name": "Professional station",
        },
    )
    entry.add_to_hass(hass)
    device, records = seed_legacy_registries(hass, entry)
    with patch(
        "custom_components.chmu.get_stations_with_coords",
        return_value={"11450": rudolec_station},
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done(wait_background_tasks=True)
    assert entry.data["station_id"] == entry.unique_id == station_id
    assert set(entry.data["station_elements"]) == KEYS
    for expected in records.values():
        record = er.async_get(hass).async_get(expected[1])
        assert record is not None
        assert (
            record.id,
            record.entity_id,
            record.unique_id,
            record.device_id,
        ) == expected
    assert [
        item.id
        for item in dr.async_entries_for_config_entry(
            dr.async_get(hass), entry.entry_id
        )
    ] == [device.id]
    assert await hass.config_entries.async_unload(entry.entry_id)


async def test_future_schema_is_not_downgraded(hass):
    entry = MockConfigEntry(domain=DOMAIN, version=2, data={"station_id": WSI})
    entry.add_to_hass(hass)
    assert not await async_migrate_entry(hass, entry)
    assert entry.version == 2
