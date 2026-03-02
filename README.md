# ČHMÚ Weather / CHMU Weather

## CZ
Integrace pro Home Assistant, která zobrazuje aktuální měření z meteorologických stanic ČHMÚ a stav + předpověď počasí z Open-Meteo podle GPS souřadnic vybrané stanice.

### Funkce
- Aktuální měření z ČHMÚ: teplota, vlhkost, tlak, srážky, rychlost a směr větru
- Weather `condition` (sunny/cloudy/rainy/...) z Open-Meteo (WMO mapping)
- Předpověď z Open-Meteo podle souřadnic stanice:
  - hourly forecast (až 168 hodin)
  - daily forecast (7 dní)
- Automatický návrh nejbližší stanice podle polohy Home Assistantu

### Instalace přes HACS
1. HACS -> Custom repositories
2. URL: `https://github.com/Vituhlos/ha-chmu-openmeteo`, kategorie `Integration`
3. Nainstalovat a restartovat Home Assistant
4. Nastavení -> Integrace -> Přidat -> `ČHMÚ Weather`

### Zdroje dat
- ČHMÚ Open Data: https://opendata.chmi.cz/meteorology/climate
- Open-Meteo: https://open-meteo.com

## EN
Home Assistant integration that provides current observations from CHMU meteorological stations and weather condition + forecast from Open-Meteo using GPS coordinates of the selected station.

### Features
- Current CHMU measurements: temperature, humidity, pressure, precipitation, wind speed and wind direction
- Weather `condition` (sunny/cloudy/rainy/...) from Open-Meteo (WMO mapping)
- Open-Meteo forecast for station coordinates:
  - hourly forecast (up to 168 hours)
  - daily forecast (7 days)
- Automatic nearest-station suggestion based on Home Assistant location

### Installation via HACS
1. HACS -> Custom repositories
2. URL: `https://github.com/Vituhlos/ha-chmu-openmeteo`, category `Integration`
3. Install and restart Home Assistant
4. Settings -> Integrations -> Add -> `ČHMÚ Weather`

### Data Sources
- CHMU Open Data: https://opendata.chmi.cz/meteorology/climate
- Open-Meteo: https://open-meteo.com

## Kredity / Credits
Původní integrace / Original integration: https://github.com/lipelix/home-assistant-chmu-weather
