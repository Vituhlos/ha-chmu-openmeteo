"""API client for ČHMÚ Weather."""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

import requests

from .const import (
    API_BASE_URL,
    API_METADATA_PATH,
    API_NOW_PATH,
    API_RECENT_PATH,
    OPENMETEO_BASE_URL,
    OPENMETEO_FORECAST_DAYS,
    OPENMETEO_FORECAST_HOURS,
    WMO_CODE_TO_HA_CONDITION,
)

_LOGGER = logging.getLogger(__name__)


def _create_session() -> requests.Session:
    session = requests.Session()
    session.headers.update({"User-Agent": "Home-Assistant-CHMU-Integration/1.2"})
    return session


def _fetch_metadata_with_fallback(
    session: requests.Session, log_context: str
) -> Dict[str, Any]:
    """Fetch today's metadata or fall back to previous day when necessary."""
    for days_back in (0, 1):
        date_str = (datetime.now() - timedelta(days=days_back)).strftime("%Y%m%d")
        filename = f"meta1-{date_str}.json"
        url = f"{API_BASE_URL}{API_METADATA_PATH}/{filename}"
        _LOGGER.info("Fetching %s from: %s", log_context, url)
        try:
            response = session.get(url, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as err:
            if err.response.status_code == 404 and days_back == 0:
                _LOGGER.info("Today's metadata not found, trying yesterday.")
                continue
            raise
    raise RuntimeError("Could not fetch metadata for today or yesterday.")


def get_stations() -> Dict[str, str]:
    """Fetch available stations from ČHMÚ metadata."""
    session = _create_session()
    try:
        metadata = _fetch_metadata_with_fallback(session, "stations")
        stations = {}
        values = metadata.get("data", {}).get("data", {}).get("values", [])
        _LOGGER.info("Got %d total entries from metadata", len(values))
        for station in values:
            if len(station) < 3:
                continue
            wsi, full_name = station[0], station[2]
            if wsi and full_name:
                stations[wsi] = full_name
        _LOGGER.info("Found %d stations", len(stations))
        return stations
    except Exception:
        _LOGGER.exception("Failed to fetch stations")
        return {
            "0-20000-0-11450": "Plzeň, Mikulka",
            "0-20000-0-11518": "Praha-Ruzyně",
            "0-20000-0-11782": "Brno-Tuřany",
        }
    finally:
        session.close()


def get_stations_with_coords() -> Dict[str, Dict[str, Any]]:
    """Fetch available stations with coordinates from ČHMÚ metadata.

    Returns:
        Dict mapping full WSI to station info with name, latitude, longitude.
    """
    session = _create_session()
    try:
        metadata = _fetch_metadata_with_fallback(session, "stations with coordinates")
        stations = {}
        values = metadata.get("data", {}).get("data", {}).get("values", [])
        _LOGGER.info("Got %d total entries from metadata", len(values))

        for station in values:
            # Format: [WSI, GH_ID, FULL_NAME, GEOGR1(lon), GEOGR2(lat), ELEVATION, BEGIN_DATE]
            if len(station) < 5:
                continue
            wsi = station[0]
            full_name = station[2]
            longitude = station[3]
            latitude = station[4]
            if not wsi or not full_name or not longitude or not latitude:
                continue
            stations[wsi] = {
                "name": full_name,
                "latitude": float(latitude),
                "longitude": float(longitude),
            }

        _LOGGER.info("Found %d stations with coordinates", len(stations))
        return stations
    except Exception:
        _LOGGER.exception("Failed to fetch stations with coordinates")
        return {
            "0-20000-0-11450": {"name": "Plzeň, Mikulka", "latitude": 49.764722, "longitude": 13.378889},
            "0-20000-0-11518": {"name": "Praha-Ruzyně", "latitude": 50.1008, "longitude": 14.26},
            "0-20000-0-11782": {"name": "Brno-Tuřany", "latitude": 49.1513, "longitude": 16.6944},
        }
    finally:
        session.close()


def fetch_openmeteo_condition(latitude: float, longitude: float) -> Optional[str]:
    """Fetch current weather condition from Open-Meteo API.

    Uses the free Open-Meteo API (no key required) to get the WMO weather
    interpretation code, which is then mapped to a HA weather condition string.

    Args:
        latitude: Station latitude
        longitude: Station longitude

    Returns:
        HA condition string (e.g. "rainy", "cloudy") or None on failure.
    """
    session = _create_session()
    try:
        url = (
            f"{OPENMETEO_BASE_URL}"
            f"?latitude={latitude}"
            f"&longitude={longitude}"
            f"&current=weather_code"
            f"&timezone=auto"
        )
        _LOGGER.debug("Fetching Open-Meteo condition from: %s", url)
        response = session.get(url, timeout=15)
        response.raise_for_status()
        data = response.json()
        wmo_code = data.get("current", {}).get("weather_code")
        if wmo_code is None:
            _LOGGER.warning("Open-Meteo response missing weather_code")
            return None
        condition = WMO_CODE_TO_HA_CONDITION.get(int(wmo_code))
        _LOGGER.debug("Open-Meteo WMO code %s -> HA condition '%s'", wmo_code, condition)
        return condition
    except Exception:
        _LOGGER.warning("Failed to fetch Open-Meteo condition", exc_info=True)
        return None
    finally:
        session.close()


def _coerce_float(value: Any) -> Optional[float]:
    """Convert value to float or return None."""
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _coerce_int(value: Any) -> Optional[int]:
    """Convert value to int or return None."""
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _format_daily_datetime(date_str: str) -> Optional[str]:
    """Convert YYYY-MM-DD string to RFC3339 UTC datetime."""
    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        return date_obj.replace(tzinfo=timezone.utc).isoformat()
    except ValueError:
        return None


def fetch_openmeteo_forecasts(latitude: float, longitude: float) -> Dict[str, list[Dict[str, Any]]]:
    """Fetch Open-Meteo hourly and daily forecasts for HA weather entity."""
    session = _create_session()
    try:
        url = (
            f"{OPENMETEO_BASE_URL}"
            f"?latitude={latitude}"
            f"&longitude={longitude}"
            f"&timezone=UTC"
            f"&forecast_days={OPENMETEO_FORECAST_DAYS}"
            f"&hourly=temperature_2m,relative_humidity_2m,pressure_msl,"
            f"precipitation,precipitation_probability,weather_code,wind_speed_10m,wind_direction_10m"
            f"&daily=weather_code,temperature_2m_max,temperature_2m_min,"
            f"precipitation_sum,precipitation_probability_max,wind_speed_10m_max,wind_direction_10m_dominant"
        )
        _LOGGER.debug("Fetching Open-Meteo forecasts from: %s", url)
        response = session.get(url, timeout=20)
        response.raise_for_status()
        payload = response.json()
    except Exception:
        _LOGGER.warning("Failed to fetch Open-Meteo forecasts", exc_info=True)
        return {"forecast_hourly": [], "forecast_daily": []}
    finally:
        session.close()

    now_utc = datetime.now(timezone.utc)
    hourly = payload.get("hourly", {})
    daily = payload.get("daily", {})

    forecast_hourly: list[Dict[str, Any]] = []
    hour_times = hourly.get("time", [])
    for idx, dt_str in enumerate(hour_times):
        try:
            dt = datetime.fromisoformat(dt_str).replace(tzinfo=timezone.utc)
        except ValueError:
            continue

        if dt < now_utc:
            continue

        wmo_code = _coerce_int(hourly.get("weather_code", [None])[idx] if idx < len(hourly.get("weather_code", [])) else None)
        item: Dict[str, Any] = {"datetime": dt.isoformat()}

        condition = WMO_CODE_TO_HA_CONDITION.get(wmo_code) if wmo_code is not None else None
        if condition is not None:
            item["condition"] = condition

        temperature = _coerce_float(hourly.get("temperature_2m", [None])[idx] if idx < len(hourly.get("temperature_2m", [])) else None)
        humidity = _coerce_float(hourly.get("relative_humidity_2m", [None])[idx] if idx < len(hourly.get("relative_humidity_2m", [])) else None)
        pressure = _coerce_float(hourly.get("pressure_msl", [None])[idx] if idx < len(hourly.get("pressure_msl", [])) else None)
        precipitation = _coerce_float(hourly.get("precipitation", [None])[idx] if idx < len(hourly.get("precipitation", [])) else None)
        precipitation_probability = _coerce_int(hourly.get("precipitation_probability", [None])[idx] if idx < len(hourly.get("precipitation_probability", [])) else None)
        wind_speed = _coerce_float(hourly.get("wind_speed_10m", [None])[idx] if idx < len(hourly.get("wind_speed_10m", [])) else None)
        wind_bearing = _coerce_float(hourly.get("wind_direction_10m", [None])[idx] if idx < len(hourly.get("wind_direction_10m", [])) else None)

        if temperature is not None:
            item["temperature"] = temperature
        if humidity is not None:
            item["humidity"] = humidity
        if pressure is not None:
            item["pressure"] = pressure
        if precipitation is not None:
            item["precipitation"] = precipitation
        if precipitation_probability is not None:
            item["precipitation_probability"] = precipitation_probability
        if wind_speed is not None:
            item["wind_speed"] = wind_speed
        if wind_bearing is not None:
            item["wind_bearing"] = wind_bearing

        forecast_hourly.append(item)
        if len(forecast_hourly) >= OPENMETEO_FORECAST_HOURS:
            break

    forecast_daily: list[Dict[str, Any]] = []
    day_times = daily.get("time", [])
    for idx, day_str in enumerate(day_times):
        day_dt = _format_daily_datetime(day_str)
        if day_dt is None:
            continue

        wmo_code = _coerce_int(daily.get("weather_code", [None])[idx] if idx < len(daily.get("weather_code", [])) else None)
        item: Dict[str, Any] = {"datetime": day_dt}

        condition = WMO_CODE_TO_HA_CONDITION.get(wmo_code) if wmo_code is not None else None
        if condition is not None:
            item["condition"] = condition

        temp_max = _coerce_float(daily.get("temperature_2m_max", [None])[idx] if idx < len(daily.get("temperature_2m_max", [])) else None)
        temp_min = _coerce_float(daily.get("temperature_2m_min", [None])[idx] if idx < len(daily.get("temperature_2m_min", [])) else None)
        precipitation_sum = _coerce_float(daily.get("precipitation_sum", [None])[idx] if idx < len(daily.get("precipitation_sum", [])) else None)
        precipitation_probability_max = _coerce_int(daily.get("precipitation_probability_max", [None])[idx] if idx < len(daily.get("precipitation_probability_max", [])) else None)
        wind_speed_max = _coerce_float(daily.get("wind_speed_10m_max", [None])[idx] if idx < len(daily.get("wind_speed_10m_max", [])) else None)
        wind_direction_dominant = _coerce_float(daily.get("wind_direction_10m_dominant", [None])[idx] if idx < len(daily.get("wind_direction_10m_dominant", [])) else None)

        if temp_max is not None:
            item["temperature"] = temp_max
        if temp_min is not None:
            item["templow"] = temp_min
        if precipitation_sum is not None:
            item["precipitation"] = precipitation_sum
        if precipitation_probability_max is not None:
            item["precipitation_probability"] = precipitation_probability_max
        if wind_speed_max is not None:
            item["wind_speed"] = wind_speed_max
        if wind_direction_dominant is not None:
            item["wind_bearing"] = wind_direction_dominant

        forecast_daily.append(item)
        if len(forecast_daily) >= OPENMETEO_FORECAST_DAYS:
            break

    return {"forecast_hourly": forecast_hourly, "forecast_daily": forecast_daily}


class ChmuApi:
    """API client for ČHMÚ weather data."""

    def __init__(
        self,
        station_id: str,
        station_name: Optional[str] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
    ):
        """Initialize the API client.

        Args:
            station_id: Full WSI identifier, e.g. '0-20000-0-11450'
            station_name: Human-readable station name
            latitude: Station latitude (used for Open-Meteo condition lookup)
            longitude: Station longitude (used for Open-Meteo condition lookup)
        """
        self.station_id = station_id
        self.station_name = station_name or f"Station {station_id}"
        self.latitude = latitude
        self.longitude = longitude
        self._session: Optional[requests.Session] = None

    def _get_session(self) -> requests.Session:
        if self._session is None:
            self._session = _create_session()
        return self._session

    def close(self) -> None:
        """Explicitly close the HTTP session."""
        if self._session is not None:
            self._session.close()
            self._session = None

    def get_current_data(self) -> Dict[str, Any]:
        """Get current weather data from ČHMÚ.

        Tries 10-minute data first, falls back to hourly if unavailable.
        Also handles the midnight edge case by trying yesterday's file.
        Enriches data with Open-Meteo weather condition when coordinates are known.
        """
        now = datetime.now()

        # Try today's 10-minute data, then yesterday (midnight edge case)
        data = self._fetch_10min_data(now) or self._fetch_10min_data(now - timedelta(days=1))

        # Fall back to hourly data
        if not data:
            data = self._fetch_hourly_data(now)

        if not data:
            raise ValueError(f"No data available for station {self.station_id}")

        # Enrich with Open-Meteo condition
        if self.latitude is not None and self.longitude is not None:
            condition = fetch_openmeteo_condition(self.latitude, self.longitude)
            data["condition"] = condition
            forecasts = fetch_openmeteo_forecasts(self.latitude, self.longitude)
            data["forecast_hourly"] = forecasts["forecast_hourly"]
            data["forecast_daily"] = forecasts["forecast_daily"]
        else:
            data["condition"] = None
            data["forecast_hourly"] = []
            data["forecast_daily"] = []

        return data

    def _fetch_10min_data(self, date: datetime) -> Optional[Dict[str, Any]]:
        """Fetch 10-minute interval data for a specific date."""
        date_str = date.strftime("%Y%m%d")
        filename = f"10m-{self.station_id}-{date_str}.json"
        url = f"{API_BASE_URL}{API_NOW_PATH}/{filename}"
        _LOGGER.debug("Fetching 10min data from: %s", url)
        try:
            response = self._get_session().get(url, timeout=30)
            response.raise_for_status()
            return self._parse_chmu_data(response.json())
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                _LOGGER.debug("10min data file not found: %s", filename)
                return None
            raise
        except ValueError as e:
            _LOGGER.warning("Failed to parse 10min data: %s", e)
            return None

    def _fetch_hourly_data(self, date: datetime) -> Optional[Dict[str, Any]]:
        """Fetch hourly data as fallback when 10-minute data is unavailable."""
        date_str = date.strftime("%Y%m%d")
        filename = f"1h-{self.station_id}-{date_str}.json"
        url = f"{API_BASE_URL}{API_RECENT_PATH}/{filename}"
        _LOGGER.debug("Fetching hourly fallback data from: %s", url)
        try:
            response = self._get_session().get(url, timeout=30)
            response.raise_for_status()
            return self._parse_chmu_data(response.json())
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                _LOGGER.debug("Hourly data file not found: %s", filename)
                return None
            raise
        except ValueError as e:
            _LOGGER.warning("Failed to parse hourly data: %s", e)
            return None

    def _parse_chmu_data(self, json_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse CHMU JSON data format.

        Data format:
        Array of [WSI, element, timestamp, value, flag, quality]

        Elements:
        T (temp), H (humidity), P (pressure), SRA10M (precip),
        F (wind speed), D (wind dir)
        """
        values = json_data.get("data", {}).get("data", {}).get("values", [])

        if not values:
            raise ValueError("No data values found in response")

        latest_values: Dict[str, Any] = {}
        for row in values:
            if len(row) < 4:
                continue
            row_wsi, element, timestamp, value = row[0], row[1], row[2], row[3]

            if row_wsi != self.station_id:
                continue

            if (
                element not in latest_values
                or timestamp > latest_values[element]["timestamp"]
            ):
                latest_values[element] = {"value": value, "timestamp": timestamp}

        if not latest_values:
            raise ValueError(f"No data found for station {self.station_id}")

        timestamp = latest_values.get("T", {}).get("timestamp", datetime.now().isoformat())

        result = {
            "temperature": latest_values.get("T", {}).get("value"),
            "humidity": latest_values.get("H", {}).get("value"),
            "pressure": latest_values.get("P", {}).get("value"),
            # SRA10M is a 10-minute sum, not cumulative
            "precipitation": latest_values.get("SRA10M", {}).get("value", 0),
            "wind_speed": latest_values.get("F", {}).get("value"),
            "wind_direction": latest_values.get("D", {}).get("value"),
            "station_name": self.station_name,
            "timestamp": timestamp,
        }

        _LOGGER.debug("Parsed ČHMÚ data: %s", result)
        return result
