# Implementation Summary / Souhrn implementace

## CZ
Integrace je implementovaná jako Home Assistant custom component s config flow.

### Implementováno
- Výběr stanice přes UI
- Návrh nejbližší stanice podle GPS Home Assistantu
- Coordinator refresh každých 10 minut
- Aktuální data z ČHMÚ
- `condition` z Open-Meteo
- Forecast z Open-Meteo:
  - hourly forecast
  - daily forecast (7 dní)

## EN
The integration is implemented as a Home Assistant custom component with config flow.

### Implemented
- Station selection via UI
- Nearest station suggestion based on Home Assistant GPS
- Coordinator refresh every 10 minutes
- Current data from CHMU
- `condition` from Open-Meteo
- Forecast from Open-Meteo:
  - hourly forecast
  - daily forecast (7 days)
