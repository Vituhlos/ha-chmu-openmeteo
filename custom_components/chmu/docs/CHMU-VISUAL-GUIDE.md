# Visual Guide / Vizuální průvodce

## CZ
Po úspěšné instalaci uvidíš v Home Assistantu:
- Integraci `ČHMÚ Weather` v Devices & Services
- Zařízení odpovídající vybrané stanici
- 6 senzorů + 1 weather entitu

### Doporučené ověření
- Otevři weather kartu a zkontroluj `condition`
- Zavolej `weather.get_forecasts` pro `hourly` a `daily`
- Ověř, že forecast odpovídá lokaci vybrané stanice

## EN
After successful installation, you should see in Home Assistant:
- `ČHMÚ Weather` integration in Devices & Services
- A device for the selected station
- 6 sensors + 1 weather entity

### Recommended validation
- Open weather card and check current `condition`
- Call `weather.get_forecasts` for `hourly` and `daily`
- Verify forecast matches the selected station location
