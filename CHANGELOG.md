# Changelog

Všechny důležité změny v tomto projektu jsou popsány v tomto souboru.  
All notable changes to this project are documented in this file.

## [1.4.0] - 2026-03-02

### Přidáno / Added
- Integrace předpovědi počasí z Open-Meteo pro souřadnice vybrané stanice ČHMÚ / Open-Meteo weather forecast integration for the selected CHMU station coordinates:
  - hodinová předpověď (až 168 hodin / 7 dní) / hourly forecast (up to 168 hours / 7 days)
  - denní předpověď (7 dní) / daily forecast (7 days)
- Podpora forecastu u weather entity v Home Assistantu / Home Assistant weather entity forecast support:
  - `FORECAST_HOURLY`
  - `FORECAST_DAILY`

### Změněno / Changed
- Mapování podmínek z Open-Meteo zůstává zdrojem pro aktuální stav počasí (`sunny`, `cloudy`, `rainy`, atd.) a nově se používá i pro forecast / Open-Meteo condition mapping remains the source for current weather condition (`sunny`, `cloudy`, `rainy`, etc.) and is now also used for forecast conditions.
- Verze integrace v manifestu navýšena na `1.4.0` / Integration manifest version bumped to `1.4.0`.
- Dokumentace aktualizována podle aktuálního runtime chování, API cest a doporučení pro entity ID / Documentation updated to match current runtime behavior, API paths, and entity ID guidance.
- `state_class` senzoru směru větru změněna na `measurement_angle` / Wind direction sensor state class updated to `measurement_angle`.
- Kontrola nejbližší stanice v config flow upravena pro platné souřadnice `0.0` / Config flow nearest-station check made robust for valid `0.0` coordinates.

### Opraveno / Fixed
- URL dokumentace a issue trackeru v manifestu nyní míří na tento repozitář / Manifest documentation and issue tracker URLs now point to this repository.
- Nesoulady v dokumentaci kolem fallback chování a ukázkových entity ID / Documentation inconsistencies around fallback behavior and sample entity IDs.

## [1.3.0] - 2025-11-09

### Přidáno / Added
- První vydání forku integrace CHMU OpenMeteo / Initial release of the CHMU OpenMeteo integration fork.
