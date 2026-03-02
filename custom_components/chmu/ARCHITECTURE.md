# Architecture / Architektura

## CZ

### Komponenty
- `config_flow.py`: výběr stanice, návrh nejbližší stanice podle GPS
- `__init__.py`: coordinator a periodické obnovování dat
- `api.py`: načítání dat z ČHMÚ + Open-Meteo condition/forecast
- `sensor.py`: 6 senzorů
- `weather.py`: weather entita včetně hourly/daily forecast

### Datový tok
1. Uživatel vybere stanici v config flow.
2. Coordinator každých 10 minut zavolá API vrstvu.
3. API vrstva načte aktuální data ČHMÚ a Open-Meteo condition/forecast.
4. Sensor a weather entity se aktualizují z coordinator dat.

### Endpointy
- ČHMÚ metadata: `/now/metadata/meta1-{yyyymmdd}.json`
- ČHMÚ 10min data: `/now/data/10m-{wsi}-{yyyymmdd}.json`
- ČHMÚ hodinový fallback: `/recent/data/1h-{wsi}-{yyyymmdd}.json`
- Open-Meteo: `https://api.open-meteo.com/v1/forecast`

## EN

### Components
- `config_flow.py`: station selection and nearest-station suggestion by GPS
- `__init__.py`: coordinator and periodic refresh
- `api.py`: CHMU data loading + Open-Meteo condition/forecast
- `sensor.py`: 6 sensors
- `weather.py`: weather entity including hourly/daily forecast

### Data flow
1. User selects a station in config flow.
2. Coordinator calls API layer every 10 minutes.
3. API layer fetches current CHMU data and Open-Meteo condition/forecast.
4. Sensor and weather entities are updated from coordinator data.

### Endpoints
- CHMU metadata: `/now/metadata/meta1-{yyyymmdd}.json`
- CHMU 10-minute data: `/now/data/10m-{wsi}-{yyyymmdd}.json`
- CHMU hourly fallback: `/recent/data/1h-{wsi}-{yyyymmdd}.json`
- Open-Meteo: `https://api.open-meteo.com/v1/forecast`
