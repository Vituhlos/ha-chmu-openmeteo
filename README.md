# ČHMÚ Weather – Home Assistant integrace

Integrace pro Home Assistant, která zobrazuje aktuální počasí z meteorologických stanic [ČHMÚ](https://opendata.chmi.cz) (Český hydrometeorologický ústav).

> **Tato integrace je fork** původní práce [@lipelix](https://github.com/lipelix/home-assistant-chmu-weather). Děkujeme za základ!

## Co bylo upraveno oproti originálu

- ⛅ **Stav počasí z [Open-Meteo](https://open-meteo.com)** — ikony sunny, cloudy, rainy, snowy... podle GPS polohy stanice (zdarma, bez API klíče)
- 🧭 **Oprava kardinálních směrů větru** — správné meteorologické pořadí (S, SSV, SV, VSV, V...)
- 🔧 **Oprava session lifecycle** — HTTP spojení se správně zavírá při unloadu integrace
- ⚡ **Optimalizace config flow** — seznam stanic se načte jen jednou místo dvakrát

## Funkce

- 🌡️ Teplota, vlhkost, tlak
- 🌧️ Srážky (10minutový součet)
- 💨 Rychlost a směr větru (včetně kardinálního směru)
- ⛅ Stav počasí z [Open-Meteo](https://open-meteo.com) podle GPS polohy stanice
- 📍 Automatický návrh nejbližší stanice podle polohy HA

## Instalace přes HACS

1. HACS → ⋮ → **Custom repositories**
2. URL: `https://github.com/Vituhlos/ha-chmu-openmeteo`, kategorie **Integration**
3. Stáhnout a restartovat HA
4. Nastavení → Integrace → Přidat → **ČHMÚ Weather**

## Zdroje dat

- Měření (teplota, vítr, srážky…): [ČHMÚ Open Data](https://opendata.chmi.cz/meteorology/climate)
- Stav počasí (ikona): [Open-Meteo](https://open-meteo.com) – zdarma, bez API klíče

## Kredity

Původní integrace: [@lipelix](https://github.com/lipelix/home-assistant-chmu-weather)
