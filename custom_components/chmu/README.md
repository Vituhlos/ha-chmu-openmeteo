# ČHMÚ Weather Integration / CHMU Weather Integration

## CZ
Custom integrace pro Home Assistant.

### Co integrace dělá
- Načítá aktuální data z ČHMÚ pro vybranou stanici
- Přidává `weather` entitu
- Přidává 6 senzorů: teplota, vlhkost, tlak, srážky, rychlost větru, směr větru
- Doplňuje `condition` z Open-Meteo podle GPS stanice
- Poskytuje forecast:
  - hourly (`FORECAST_HOURLY`)
  - daily (`FORECAST_DAILY`, 7 dní)

### Nastavení
1. Zkopíruj `custom_components/chmu` do Home Assistantu
2. Restartuj HA
3. Settings -> Devices & Services -> Add Integration -> `ČHMÚ Weather`
4. Vyber stanici (nejbližší je předvybrána)

### Poznámky
- Entity ID vždy ověř v Developer Tools -> States
- Polling interval je 10 minut
- Fallback dat: dnešní 10min soubor -> včerejší 10min soubor -> dnešní hodinový soubor

## EN
Custom Home Assistant integration.

### What the integration does
- Loads current CHMU data for the selected station
- Creates one `weather` entity
- Creates 6 sensors: temperature, humidity, pressure, precipitation, wind speed, wind direction
- Enriches current `condition` from Open-Meteo using station GPS coordinates
- Provides forecast:
  - hourly (`FORECAST_HOURLY`)
  - daily (`FORECAST_DAILY`, 7 days)

### Setup
1. Copy `custom_components/chmu` into your Home Assistant config
2. Restart HA
3. Settings -> Devices & Services -> Add Integration -> `ČHMÚ Weather`
4. Select station (nearest one is preselected)

### Notes
- Always confirm entity IDs in Developer Tools -> States
- Polling interval is 10 minutes
- Data fallback: today 10-minute file -> yesterday 10-minute file -> today hourly file
