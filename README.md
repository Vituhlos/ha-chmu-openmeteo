# ČHMÚ Weather – Home Assistant integrace

Integrace pro Home Assistant, která zobrazuje aktuální počasí z meteorologických stanic [ČHMÚ](https://opendata.chmi.cz) (Český hydrometeorologický ústav).

## Funkce

- 🌡️ Teplota, vlhkost, tlak
- 🌧️ Srážky (10minutový součet)
- 💨 Rychlost a směr větru (včetně kardinálního směru)
- ⛅ Stav počasí z [Open-Meteo](https://open-meteo.com) podle GPS polohy stanice
- 📍 Automatický návrh nejbližší stanice podle polohy HA

## Instalace přes HACS

1. HACS → ⋮ → **Custom repositories**
2. URL tohoto repozitáře, kategorie **Integration**
3. Stáhnout a restartovat HA
4. Nastavení → Integrace → Přidat → **ČHMÚ Weather**

## Zdroje dat

- Měření (teplota, vítr, srážky…): [ČHMÚ Open Data](https://opendata.chmi.cz/meteorology/climate)
- Stav počasí (ikona): [Open-Meteo](https://open-meteo.com) – zdarma, bez API klíče

## Verze

`1.3.0` – Oprava kardinálních směrů větru, přidání Open-Meteo condition, oprava session lifecycle.
