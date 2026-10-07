# Phase 3 offline observations

`observations.json` uses the actual ČHMÚ 10M header and WSI/element structure
verified against `10m-0-203-0-11526-20261007.json` on 2026-10-07.
Values and timestamps are synthetic, including deliberate zero precipitation
and zero wind. They are not presented as recorded meteorological observations.
Tests vary copies into stale/missing/previous-day/quality scenarios.

Official `meta3-20261007.json` describes element-specific FLAG meanings;
`meta4-20261007.json` lists quality codes: 0 good, 1 suspect, 2 poor/do not use yet,
3 estimated, 4 missing, 5 unknown. Unknown quality is retained; it is not evidence
of either bad measurements or high confidence. Unrecognised codes/flags are kept
raw, without invented meteorological interpretation.
