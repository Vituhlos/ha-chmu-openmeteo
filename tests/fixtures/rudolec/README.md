# Nedrahovice, Rudolec — static baseline fixture

WSI: `0-203-0-11526`; latitude `49.631723`, longitude `14.440088`, elevation `348 m`.

`meta1.json` and `meta2.json` are reduced public ČHMÚ responses captured during
the read-only audit on 2026-10-06. Only this station's rows were retained; source
record UUIDs and unrelated envelope fields were removed. Row order, values,
headers, timestamps and the `data.data.values` nesting remain unchanged.

Sources:

- https://opendata.chmi.cz/meteorology/climate/now/metadata/meta1-20261006.json
- https://opendata.chmi.cz/meteorology/climate/now/metadata/meta2-20261006.json

The meta2 fixture deliberately retains all 22 station rows, including hourly
vapor pressure `E` and unmapped 10-minute variables. The five mapped 10M
elements are `T`, `H`, `SRA10M`, `F`, `D`; the station supplies no `P`.
Vapor pressure must not create an atmospheric-pressure sensor.

Tests serve these files through mocked HTTP and never download live metadata.
The HA platform test's numeric measurements are explicitly synthetic; they do
not establish precipitation semantics, freshness or forecast accuracy.

These tests describe the pinned upstream baseline. No state-class, forecast,
registry migration or other Phase 2 change is implemented or expected here.
