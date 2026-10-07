"""Config flow for ČHMÚ Weather integration."""

import logging
from functools import partial
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers import selector

from .api import get_stations_with_coords
from .const import (
    CONF_STATION_ELEMENTS,
    CONF_STATION_ID,
    CONF_STATION_NAME,
    DOMAIN,
)
from .identity import canonical_station_id

_LOGGER = logging.getLogger(__name__)


def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two coordinates using Haversine formula.

    Returns distance in kilometers.
    """
    from math import atan2, cos, radians, sin, sqrt

    # Earth radius in kilometers
    R = 6371.0

    lat1_rad = radians(lat1)
    lon1_rad = radians(lon1)
    lat2_rad = radians(lat2)
    lon2_rad = radians(lon2)

    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad

    a = sin(dlat / 2) ** 2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    distance = R * c
    return distance


def find_nearest_station(
    home_lat: float, home_lon: float, stations: dict[str, dict[str, Any]]
) -> str | None:
    """Find the nearest station to home coordinates.

    Most automatic stations are rain gauges reporting precipitation only, so a
    station measuring temperature is preferred as the pre-selected default and
    the raw nearest station is only used when no such station exists.

    Returns station ID of the nearest station.
    """
    if not stations:
        return None

    with_temperature = {
        station_id: info
        for station_id, info in stations.items()
        if "temperature" in info.get("elements", ["temperature"])
    }

    nearest_id = None
    nearest_distance = float("inf")

    for station_id, info in (with_temperature or stations).items():
        distance = calculate_distance(
            home_lat, home_lon, info["latitude"], info["longitude"]
        )
        if distance < nearest_distance:
            nearest_distance = distance
            nearest_id = station_id

    _LOGGER.debug(f"Nearest station: {nearest_id} at {nearest_distance:.1f} km")

    return nearest_id


def build_station_labels(stations: dict[str, dict[str, Any]]) -> dict[str, str]:
    """Build dropdown labels, disambiguating stations that share a name.

    ČHMÚ reuses the same place name for several nearby stations (e.g. two
    "Praha, Klementinum" sites), so duplicates get their station id appended.
    """
    name_counts: dict[str, int] = {}
    for info in stations.values():
        name_counts[info["name"]] = name_counts.get(info["name"], 0) + 1

    labels = {}
    for station_id, info in stations.items():
        name = info["name"]
        labels[station_id] = (
            name if name_counts[name] == 1 else f"{name} ({station_id})"
        )
    return labels


class ChmuConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for ČHMÚ Weather."""

    VERSION = 1
    MINOR_VERSION = 2

    def __init__(self) -> None:
        self._stations: dict[str, dict[str, Any]] | None = None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Handle the initial step."""
        errors = {}

        if self._stations is None:
            try:
                self._stations = await self.hass.async_add_executor_job(
                    partial(get_stations_with_coords, allow_fallback=False)
                )
                if not self._stations:
                    errors["base"] = "cannot_connect"
                    self._stations = None
            except Exception:
                _LOGGER.exception("Failed to fetch stations")
                errors["base"] = "cannot_connect"

        stations_with_coords = self._stations or {}
        if user_input is not None and not errors:
            station_id = user_input[CONF_STATION_ID]
            if station_id not in stations_with_coords:
                return self.async_abort(reason="invalid_station")
            identity = canonical_station_id(station_id)
            for entry in self._async_current_entries():
                existing_id = entry.data.get(CONF_STATION_ID) or entry.unique_id
                if existing_id and canonical_station_id(existing_id) == identity:
                    return self.async_abort(reason="already_configured")
            station_info = stations_with_coords[station_id]
            station_name = station_info.get("name", f"Station {station_id}")
            station_elements = station_info.get("elements", [])

            # Check if already configured
            await self.async_set_unique_id(identity)
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=f"{station_name} ({station_id})",
                data={
                    CONF_STATION_ID: station_id,
                    CONF_STATION_NAME: station_name,
                    CONF_STATION_ELEMENTS: station_elements,
                    "station_latitude": station_info["latitude"],
                    "station_longitude": station_info["longitude"],
                },
            )

        # Get Home Assistant location to suggest nearest station
        home_lat = self.hass.config.latitude
        home_lon = self.hass.config.longitude

        suggested_station = None
        if home_lat is not None and home_lon is not None and stations_with_coords:
            suggested_station = find_nearest_station(
                home_lat, home_lon, stations_with_coords
            )

        # Build select options sorted by name
        select_options = [
            selector.SelectOptionDict(
                value=station_id,
                label=label,
            )
            for station_id, label in sorted(
                build_station_labels(stations_with_coords).items(),
                key=lambda x: x[1],
            )
        ]

        # Build schema with suggested default if available
        if suggested_station:
            data_schema = vol.Schema(
                {
                    vol.Required(
                        CONF_STATION_ID, default=suggested_station
                    ): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=select_options,
                            mode=selector.SelectSelectorMode.DROPDOWN,
                            sort=False,
                        )
                    )
                }
            )
        else:
            data_schema = vol.Schema(
                {
                    vol.Required(CONF_STATION_ID): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=select_options,
                            mode=selector.SelectSelectorMode.DROPDOWN,
                            sort=False,
                        )
                    )
                }
            )

        # Prepare description with nearest station info
        description_placeholders = {
            "stations_count": str(len(stations_with_coords)),
        }

        if suggested_station and suggested_station in stations_with_coords:
            station_info = stations_with_coords[suggested_station]
            distance = calculate_distance(
                home_lat, home_lon, station_info["latitude"], station_info["longitude"]
            )
            description_placeholders["nearest_station"] = station_info["name"]
            description_placeholders["distance"] = f"{distance:.1f}"
        else:
            description_placeholders["nearest_station"] = "N/A"
            description_placeholders["distance"] = "N/A"

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
            description_placeholders=description_placeholders,
        )
