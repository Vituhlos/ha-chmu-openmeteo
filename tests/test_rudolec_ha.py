"""Rudolec selection and capability filtering in a real, offline HA harness."""

from unittest.mock import AsyncMock, patch

import pytest

pytest.importorskip(
    "pytest_homeassistant_custom_component",
    reason="The real Home Assistant harness is not installed",
)

from homeassistant.config_entries import SOURCE_USER  # noqa: E402
from homeassistant.data_entry_flow import FlowResultType  # noqa: E402
from homeassistant.helpers import entity_registry  # noqa: E402
from pytest_homeassistant_custom_component.common import MockConfigEntry  # noqa: E402

from custom_components.chmu.const import DOMAIN  # noqa: E402

WSI = "0-203-0-11526"
CAPABILITIES = {
    "temperature",
    "humidity",
    "precipitation",
    "wind_speed",
    "wind_direction",
}


@pytest.fixture(autouse=True)
def enable_custom_integrations(enable_custom_integrations):
    """Use this checkout's integration in the test Home Assistant."""
    return enable_custom_integrations


async def test_config_flow_selects_rudolec(hass, rudolec_session):
    """Exercise the real form and creation result, with static discovery HTTP."""
    with patch(
        "custom_components.chmu.async_setup_entry", new=AsyncMock(return_value=True)
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}
        )
        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "user"
        assert result["errors"] == {}
        schema = result["data_schema"]
        assert schema is not None
        selector = next(iter(schema.schema.values()))
        assert {option["value"] for option in selector.config["options"]} == {WSI}

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"station_id": WSI}
        )
        await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == f"Nedrahovice, Rudolec ({WSI})"
    assert result["data"]["station_id"] == WSI
    assert result["data"]["station_name"] == "Nedrahovice, Rudolec"
    assert set(result["data"]["station_elements"]) == CAPABILITIES
    assert "pressure" not in result["data"]["station_elements"]
    assert result["result"].unique_id == WSI


async def test_capability_aware_entry_creates_no_pressure_sensor(hass, rudolec_station):
    """Load actual sensor/weather platforms and inspect the entity registry."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=WSI,
        title="Nedrahovice, Rudolec",
        data={
            "station_id": WSI,
            "station_name": rudolec_station["name"],
            "station_elements": rudolec_station["elements"],
        },
    )
    entry.add_to_hass(hass)
    # These values are synthetic. The test checks creation/IDs, not meteorology.
    measured = {
        "temperature": 18.8,
        "humidity": 58,
        "precipitation": 0.0,
        "wind_speed": 0.5,
        "wind_direction": 43,
        "station_name": rudolec_station["name"],
        "timestamp": "2026-10-06T09:50:00Z",
    }
    with (
        patch(
            "custom_components.chmu.api.ChmuApi.get_current_data", return_value=measured
        ),
        patch(
            "custom_components.chmu.forecast.ChmuForecastApi.get_forecast",
            return_value=None,
        ),
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done(wait_background_tasks=True)

    registry = entity_registry.async_get(hass)
    entities = entity_registry.async_entries_for_config_entry(registry, entry.entry_id)
    sensors = {
        entity.unique_id: entity
        for entity in entities
        if entity.entity_id.startswith("sensor.")
    }
    assert set(sensors) == {
        *(f"{WSI}_{key}" for key in CAPABILITIES),
        f"{WSI}_weather_description",
    }
    assert f"{WSI}_pressure" not in sensors
    for key in CAPABILITIES:
        state = hass.states.get(sensors[f"{WSI}_{key}"].entity_id)
        assert state is not None
        assert state.state not in ("unavailable", "unknown")
    assert entry.data["station_id"] == WSI
    assert (
        len([entity for entity in entities if entity.entity_id.startswith("weather.")])
        == 1
    )
    assert await hass.config_entries.async_unload(entry.entry_id)
