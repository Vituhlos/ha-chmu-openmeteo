"""Constants for ČHMÚ Weather integration."""

DOMAIN = "chmu"

CONF_STATION_ID = "station_id"
CONF_STATION_NAME = "station_name"
CONF_STATION_LATITUDE = "station_latitude"
CONF_STATION_LONGITUDE = "station_longitude"

# ČHMÚ API endpoints
API_BASE_URL = "https://opendata.chmi.cz/meteorology/climate"
API_NOW_PATH = "/now/data"
API_METADATA_PATH = "/now/metadata"
API_RECENT_PATH = "/recent/data"

# Open-Meteo API (free, no key required)
OPENMETEO_BASE_URL = "https://api.open-meteo.com/v1/forecast"

# WMO Weather Interpretation Codes → Home Assistant condition strings
# https://open-meteo.com/en/docs#weathervariables
# https://developers.home-assistant.io/docs/core/entity/weather/#recommended-values-for-state
WMO_CODE_TO_HA_CONDITION: dict[int, str] = {
    0: "sunny",           # Clear sky
    1: "sunny",           # Mainly clear
    2: "partlycloudy",    # Partly cloudy
    3: "cloudy",          # Overcast
    45: "fog",            # Fog
    48: "fog",            # Depositing rime fog
    51: "rainy",          # Drizzle: light
    53: "rainy",          # Drizzle: moderate
    55: "rainy",          # Drizzle: dense
    56: "snowy-rainy",    # Freezing drizzle: light
    57: "snowy-rainy",    # Freezing drizzle: heavy
    61: "rainy",          # Rain: slight
    63: "rainy",          # Rain: moderate
    65: "pouring",        # Rain: heavy
    66: "snowy-rainy",    # Freezing rain: light
    67: "snowy-rainy",    # Freezing rain: heavy
    71: "snowy",          # Snow fall: slight
    73: "snowy",          # Snow fall: moderate
    75: "snowy",          # Snow fall: heavy
    77: "snowy",          # Snow grains
    80: "rainy",          # Rain showers: slight
    81: "rainy",          # Rain showers: moderate
    82: "pouring",        # Rain showers: violent
    85: "snowy",          # Snow showers: slight
    86: "snowy",          # Snow showers: heavy
    95: "lightning-rainy", # Thunderstorm: slight or moderate
    96: "lightning-rainy", # Thunderstorm with slight hail
    99: "lightning-rainy", # Thunderstorm with heavy hail
}
