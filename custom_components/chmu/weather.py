"""Weather platform for ČHMÚ Weather integration."""

from typing import Any

from homeassistant.components.weather import WeatherEntity, WeatherEntityFeature
from homeassistant.const import UnitOfPressure, UnitOfSpeed, UnitOfTemperature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_STATION_ID, CONF_STATION_NAME, DOMAIN


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up ČHMÚ weather entity from a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    station_id = entry.data[CONF_STATION_ID]
    station_name = entry.data.get(CONF_STATION_NAME, f"Station {station_id}")

    async_add_entities([ChmuWeather(coordinator, entry, station_id, station_name)])


class ChmuWeather(CoordinatorEntity, WeatherEntity):
    """ČHMÚ weather entity backed by DataUpdateCoordinator.

    Weather condition is sourced from Open-Meteo (free, no key required)
    using the GPS coordinates of the selected ČHMÚ station.
    All other measurements come directly from ČHMÚ open data.
    """

    _attr_has_entity_name = True
    _attr_native_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_native_pressure_unit = UnitOfPressure.HPA
    _attr_native_wind_speed_unit = UnitOfSpeed.METERS_PER_SECOND
    _attr_supported_features = (
        WeatherEntityFeature.FORECAST_HOURLY | WeatherEntityFeature.FORECAST_DAILY
    )

    def __init__(self, coordinator, entry, station_id, station_name):
        """Initialize the weather entity."""
        super().__init__(coordinator)
        self._station_id = station_id
        self._station_name = station_name
        self._attr_name = station_name

    @property
    def unique_id(self) -> str:
        return f"{self._station_id}_weather"

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._station_id)},
            "name": self._station_name,
            "manufacturer": "ČHMÚ",
            "model": f"Weather Station {self._station_id}",
            "configuration_url": "https://opendata.chmi.cz",
            "suggested_area": "Outdoors",
        }

    def _get(self, key: str):
        """Safely retrieve a value from coordinator data."""
        if not self.coordinator.data:
            return None
        value = self.coordinator.data.get(key)
        return value if value not in (None, "", []) else None

    @property
    def native_temperature(self):
        return self._get("temperature")

    @property
    def humidity(self):
        return self._get("humidity")

    @property
    def native_pressure(self):
        return self._get("pressure")

    @property
    def native_wind_speed(self):
        return self._get("wind_speed")

    @property
    def wind_bearing(self):
        return self._get("wind_direction")

    @property
    def condition(self) -> str | None:
        """Return current weather condition from Open-Meteo.

        Falls back to a best-effort guess from ČHMÚ measurements
        when Open-Meteo data is unavailable (e.g. network error).
        """
        # Primary: Open-Meteo WMO-based condition
        om_condition = self._get("condition")
        if om_condition is not None:
            return om_condition

        # Fallback: derive from ČHMÚ measurements
        temperature = self._get("temperature")
        precip = self._get("precipitation")
        wind_speed = self._get("wind_speed")

        if precip is not None and float(precip) > 0:
            # Snow when temperature is at or below 0 °C
            if temperature is not None and float(temperature) <= 0:
                return "snowy"
            return "rainy"

        if wind_speed is not None and float(wind_speed) > 10:
            return "windy"

        # Cannot determine cloudy vs clear without cloud cover data
        return "cloudy"

    async def async_forecast_hourly(self) -> list[dict[str, Any]] | None:
        """Return hourly forecast from Open-Meteo for the selected station."""
        forecast = self._get("forecast_hourly")
        return forecast if isinstance(forecast, list) else None

    async def async_forecast_daily(self) -> list[dict[str, Any]] | None:
        """Return daily 7-day forecast from Open-Meteo for the selected station."""
        forecast = self._get("forecast_daily")
        return forecast if isinstance(forecast, list) else None
