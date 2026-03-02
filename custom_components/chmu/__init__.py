"""ČHMÚ Weather Integration."""

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import CONF_STATION_ID, CONF_STATION_NAME, CONF_STATION_LATITUDE, CONF_STATION_LONGITUDE, DOMAIN
from .api import ChmuApi

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.SENSOR, Platform.WEATHER]
SCAN_INTERVAL = timedelta(minutes=10)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up ČHMÚ Weather from a config entry."""
    station_id = entry.data[CONF_STATION_ID]
    station_name = entry.data.get(CONF_STATION_NAME, f"Station {station_id}")
    latitude = entry.data.get(CONF_STATION_LATITUDE)
    longitude = entry.data.get(CONF_STATION_LONGITUDE)

    api = ChmuApi(station_id, station_name, latitude=latitude, longitude=longitude)

    async def async_update_data():
        """Fetch data from API."""
        try:
            return await hass.async_add_executor_job(api.get_current_data)
        except Exception as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=f"ČHMÚ {station_id}",
        update_method=async_update_data,
        update_interval=SCAN_INTERVAL,
    )

    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "coordinator": coordinator,
        "api": api,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        entry_data = hass.data[DOMAIN].pop(entry.entry_id)
        # Explicitly close the session
        await hass.async_add_executor_job(entry_data["api"].close)

    return unload_ok
