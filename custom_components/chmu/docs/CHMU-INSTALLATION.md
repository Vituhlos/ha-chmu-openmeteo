# Instalace / Installation

## CZ
1. Restartuj Home Assistant po instalaci souborů integrace.
2. Otevři Settings -> Devices & Services.
3. Klikni Add Integration a vyhledej `ČHMÚ Weather`.
4. Vyber stanici (nejbližší je předvybraná).
5. Po dokončení zkontroluj entity v Developer Tools -> States.

### Vytvořené entity
- 1x weather entita
- 6x sensor entita (temperature, humidity, pressure, precipitation, wind_speed, wind_direction)

### Forecast
- Hourly forecast
- Daily forecast (7 dní)

### Troubleshooting
- Zkontroluj logy Home Assistantu
- Ověř dostupnost ČHMÚ/Open-Meteo endpointů
- Počkej na další update cyklus (10 minut)

## EN
1. Restart Home Assistant after installing integration files.
2. Open Settings -> Devices & Services.
3. Click Add Integration and search for `ČHMÚ Weather`.
4. Select station (nearest one is preselected).
5. After setup, verify entities in Developer Tools -> States.

### Created entities
- 1x weather entity
- 6x sensor entities (temperature, humidity, pressure, precipitation, wind_speed, wind_direction)

### Forecast
- Hourly forecast
- Daily forecast (7 days)

### Troubleshooting
- Check Home Assistant logs
- Verify CHMU/Open-Meteo endpoint availability
- Wait for the next update cycle (10 minutes)
