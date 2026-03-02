"""Config flow for ČHMÚ Weather integration."""

import logging
from math import atan2, cos, radians, sin, sqrt
from typing import Any, Dict, Optional

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector

from .api import get_stations_with_coords
from .const import (
    CONF_STATION_ID,
    CONF_STATION_NAME,
    CONF_STATION_LATITUDE,
    CONF_STATION_LONGITUDE,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Return distance in km between two GPS coordinates (Haversine formula)."""
    R = 6371.0
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    return R * 2 * atan2(sqrt(a), sqrt(1 - a))


def _find_nearest_station(
    home_lat: float, home_lon: float, stations: Dict[str, Dict[str, Any]]
) -> Optional[str]:
    """Return WSI of the station closest to the given coordinates."""
    if not stations:
        return None
    return min(
        stations,
        key=lambda sid: _haversine_km(
            home_lat, home_lon, stations[sid]["latitude"], stations[sid]["longitude"]
        ),
    )


class ChmuConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for ČHMÚ Weather."""

    VERSION = 1

    def __init__(self):
        self._stations_with_coords: Dict[str, Dict[str, Any]] = {}

    async def async_step_user(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors = {}

        # Load stations once and cache on self
        if not self._stations_with_coords:
            try:
                self._stations_with_coords = await self.hass.async_add_executor_job(
                    get_stations_with_coords
                )
                if not self._stations_with_coords:
                    errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Failed to fetch stations")
                errors["base"] = "cannot_connect"

        if user_input is not None and not errors:
            station_id = user_input[CONF_STATION_ID]

            # Prevent duplicate entries
            await self.async_set_unique_id(station_id)
            self._abort_if_unique_id_configured()

            station_info = self._stations_with_coords.get(station_id, {})
            station_name = station_info.get("name", f"Station {station_id}")
            latitude = station_info.get("latitude")
            longitude = station_info.get("longitude")

            return self.async_create_entry(
                title=f"{station_name} ({station_id})",
                data={
                    CONF_STATION_ID: station_id,
                    CONF_STATION_NAME: station_name,
                    CONF_STATION_LATITUDE: latitude,
                    CONF_STATION_LONGITUDE: longitude,
                },
            )

        # Determine nearest station to suggest as default
        home_lat = self.hass.config.latitude
        home_lon = self.hass.config.longitude
        suggested_station = None
        distance_km = None

        if home_lat is not None and home_lon is not None and self._stations_with_coords:
            suggested_station = _find_nearest_station(
                home_lat, home_lon, self._stations_with_coords
            )
            if suggested_station:
                info = self._stations_with_coords[suggested_station]
                distance_km = _haversine_km(
                    home_lat, home_lon, info["latitude"], info["longitude"]
                )
                _LOGGER.debug(
                    "Nearest station: %s at %.1f km", suggested_station, distance_km
                )

        # Build sorted dropdown options
        select_options = [
            selector.SelectOptionDict(value=sid, label=info["name"])
            for sid, info in sorted(
                self._stations_with_coords.items(), key=lambda x: x[1]["name"]
            )
        ]

        schema_fields: dict = {
            vol.Required(
                CONF_STATION_ID,
                **({"default": suggested_station} if suggested_station else {}),
            ): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=select_options,
                    mode=selector.SelectSelectorMode.DROPDOWN,
                    sort=False,
                )
            )
        }

        description_placeholders = {
            "stations_count": str(len(self._stations_with_coords)),
            "nearest_station": (
                self._stations_with_coords[suggested_station]["name"]
                if suggested_station and suggested_station in self._stations_with_coords
                else "N/A"
            ),
            "distance": f"{distance_km:.1f}" if distance_km is not None else "N/A",
        }

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(schema_fields),
            errors=errors,
            description_placeholders=description_placeholders,
        )
