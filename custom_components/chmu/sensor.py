"""Sensor platform for ČHMÚ Weather integration."""

import logging

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    UnitOfPressure,
    UnitOfSpeed,
    UnitOfTemperature,
    UnitOfPrecipitationDepth,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_STATION_ID, CONF_STATION_NAME, DOMAIN

_LOGGER = logging.getLogger(__name__)

# Cardinal direction labels in correct meteorological order.
# Index 0 = North (0°), each step = 22.5°, clockwise.
_CARDINAL_DIRECTIONS = [
    "S", "SSV", "SV", "VSV",
    "V", "VJV", "JV", "JJV",
    "J", "JJZ", "JZ", "ZJZ",
    "Z", "ZSZ", "SZ", "SSZ",
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up ČHMÚ sensors from a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    station_id = entry.data[CONF_STATION_ID]
    station_name = entry.data.get(CONF_STATION_NAME, f"Station {station_id}")

    sensors = [
        ChmuTemperatureSensor(coordinator, entry, station_id, station_name),
        ChmuHumiditySensor(coordinator, entry, station_id, station_name),
        ChmuPressureSensor(coordinator, entry, station_id, station_name),
        ChmuPrecipitationSensor(coordinator, entry, station_id, station_name),
        ChmuWindSpeedSensor(coordinator, entry, station_id, station_name),
        ChmuWindDirectionSensor(coordinator, entry, station_id, station_name),
    ]

    async_add_entities(sensors)


class ChmuSensorBase(CoordinatorEntity, SensorEntity):
    """Base class for ČHMÚ sensors."""

    def __init__(self, coordinator, entry, station_id, station_name):
        super().__init__(coordinator)
        self._station_id = station_id
        self._station_name = station_name
        self._attr_has_entity_name = True

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

    def _get_value(self, key: str):
        """Safely retrieve a value from coordinator data."""
        if not self.coordinator.data:
            return None
        value = self.coordinator.data.get(key)
        return value if value not in (None, "", []) else None


class ChmuTemperatureSensor(ChmuSensorBase):
    """Temperature sensor."""

    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_translation_key = "temperature"
    _attr_icon = "mdi:thermometer"

    @property
    def unique_id(self):
        return f"{self._station_id}_temperature"

    @property
    def native_value(self):
        return self._get_value("temperature")


class ChmuHumiditySensor(ChmuSensorBase):
    """Humidity sensor."""

    _attr_device_class = SensorDeviceClass.HUMIDITY
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_translation_key = "humidity"
    _attr_icon = "mdi:water-percent"

    @property
    def unique_id(self):
        return f"{self._station_id}_humidity"

    @property
    def native_value(self):
        return self._get_value("humidity")


class ChmuPressureSensor(ChmuSensorBase):
    """Pressure sensor."""

    _attr_device_class = SensorDeviceClass.PRESSURE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfPressure.HPA
    _attr_translation_key = "pressure"
    _attr_icon = "mdi:gauge"

    @property
    def unique_id(self):
        return f"{self._station_id}_pressure"

    @property
    def native_value(self):
        return self._get_value("pressure")


class ChmuPrecipitationSensor(ChmuSensorBase):
    """Precipitation sensor (10-minute interval sum — SRA10M)."""

    _attr_device_class = SensorDeviceClass.PRECIPITATION
    # MEASUREMENT because SRA10M resets each interval, not a cumulative counter
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfPrecipitationDepth.MILLIMETERS
    _attr_translation_key = "precipitation"
    _attr_icon = "mdi:weather-rainy"

    @property
    def unique_id(self):
        return f"{self._station_id}_precipitation"

    @property
    def native_value(self):
        return self._get_value("precipitation")


class ChmuWindSpeedSensor(ChmuSensorBase):
    """Wind speed sensor."""

    _attr_device_class = SensorDeviceClass.WIND_SPEED
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfSpeed.METERS_PER_SECOND
    _attr_translation_key = "wind_speed"
    _attr_icon = "mdi:weather-windy"

    @property
    def unique_id(self):
        return f"{self._station_id}_wind_speed"

    @property
    def native_value(self):
        return self._get_value("wind_speed")


class ChmuWindDirectionSensor(ChmuSensorBase):
    """Wind direction sensor with corrected cardinal direction labels."""

    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "°"
    _attr_translation_key = "wind_direction"
    _attr_icon = "mdi:compass"

    @property
    def unique_id(self):
        return f"{self._station_id}_wind_direction"

    @property
    def native_value(self):
        return self._get_value("wind_direction")

    @property
    def extra_state_attributes(self):
        """Return cardinal direction as extra attribute.

        Uses the standard meteorological convention: North = 0°,
        clockwise, 16 sectors of 22.5° each.
        """
        degrees = self._get_value("wind_direction")
        if degrees is None:
            return {}
        idx = round(float(degrees) / 22.5) % 16
        return {"cardinal_direction": _CARDINAL_DIRECTIONS[idx]}
