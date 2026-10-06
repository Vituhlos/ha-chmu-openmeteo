# Phase 1 development baseline

This checkout starts at upstream commit
`86b51d5e48f8af19b9bb8890b35038589c43c2e5` (version 1.8.0), on the local branch
`phase1/upstream-base`. `upstream` points to lipelix's repository; `legacy`
points to Vituhlos's original fork. Their histories remain separate.

No runtime integration, manifest, license, attribution, provider, state class,
registry migration or installed Home Assistant configuration changes belong to
Phase 1. The original checkout and its backup are not development directories.

## Exact upstream test profile — Linux

Use an isolated Python 3.13 environment, as the existing CI does:

```sh
python3.13 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python -m pytest -ra
.venv/bin/ruff check .
.venv/bin/ruff format --check .
.venv/bin/pyright
PATH="$PWD/.venv/bin:$PATH" bash ./validate-hacs.sh
```

The pinned harness `pytest-homeassistant-custom-component==0.13.316` installs
HA Core `2026.2.3`. This profile does not prove compatibility with HA 2026.9.
Keep the existing requirements, pyright rules, CI and release workflow intact.
The local HACS shell script is only a structural/JSON check; it is not the HACS
GitHub action or hassfest. Those gates remain in the original CI.

## Optional current-Core probe

`.github/workflows/ha-current.yml` is a manual Linux-only test job for HA
`2026.9.4`, Python `3.14.2`, and harness `0.13.367`. It builds a temporary copy
of the upstream requirements, replacing only the harness pin, asserts the Core
version and runs every test. It leaves `requirements-dev.txt` unchanged.
Nothing is published or deployed, and there is no release trigger.

PyPI metadata checked on 2026-10-06 shows that Core 2026.9.4 requires Python
`>=3.14.2` and harness 0.13.367 pins exactly that Core. A 3.13 environment cannot
test this target. This optional probe is preparation, not a tested declaration
of compatibility. Run it once publishing this branch is separately authorized,
or reproduce its steps locally on Linux. The supported minimum and final
compatibility matrix are intentionally undecided.

## Windows unit-only environment

The exact upstream requirements could not be installed here: `lru-dict==1.3.0`
needs MSVC to build for CPython 3.13 on Windows. The checkout's `.venv` therefore
contains only isolated unit/lint tooling:

```powershell
uv venv --python 3.13 .venv
uv --system-certs pip install --python .venv\Scripts\python.exe `
  'ruff==0.16.3' 'pyright==1.1.411' 'pytest>=8.3.0' `
  'pre-commit>=3.5.0' 'requests>=2.31.0' tzdata
.venv\Scripts\python.exe -m pytest -ra
.venv\Scripts\ruff.exe check --no-cache .
.venv\Scripts\ruff.exe format --check --no-cache .
```

This profile deliberately skips real HA modules and cannot produce a valid
whole-project pyright result without HA type dependencies. `tzdata` supplies
the IANA time zone database that Windows lacks. The base 145 unit tests and
four new Rudolec unit tests run here; skipped modules must be reported.

A separate diagnostic environment outside this checkout installed all harness
dependencies with `lru-dict==1.4.1` as a Windows-only override. This is not the
exact upstream dependency baseline. Pytest then failed loading the HA plugin
because `homeassistant.runner` imports Unix-only `fcntl`, before collecting
any tests. Do not replace `fcntl` with a fake implementation or present a
stubbed test as a real HA runtime test. Use Linux for that verification.

The attempted Docker Desktop startup failed before providing an engine; its
WSL distribution reported a read-only mount fallback. No Docker/WSL recovery,
reset, dependency downgrade or global compiler installation was performed.

## Test boundaries and Rudolec fixtures

The shared `tests/conftest.py` installs a small HA module stub **only when HA
is absent**. API, statistics aggregation, forecast/GRIB, builder and entity
translation tests are primarily logic tests; they do not boot HA.

`test_weather_ha.py` and `test_statistics_ha.py` use the real HA fixture,
config-entry/platform setup, forecast service contract and recorder queue.
The new `test_rudolec_ha.py` also requires the real harness. Its config-flow
test mocks entry setup to isolate selection; its second test loads the real
sensor and weather platforms and checks their registered unique IDs/states.
It uses synthetic measurements and mocks external providers, while metadata
discovery consumes the static captured JSON through the actual API parser.

`tests/fixtures/rudolec/` contains one real meta1 station row and all 22 real
meta2 station rows, plus provenance. Tests verify the full WSI
`0-203-0-11526`, coordinates, discovery, five mapped capabilities and no `P`.
The HA tests verify selection/capability-aware sensor creation when run on a
working Linux harness. Do not claim that these two tests ran on Windows.

No Phase 2 behavior is encoded as an expected fix. In particular, interval
rainfall, angle state classes, cardinal direction, cache expiry and session
cleanup retain the exact upstream implementation.

The inherited pre-commit ruff hooks use `--fix` and formatting; install/run
them deliberately. Its isolated pytest hook declares only pytest/requests,
so it skips HA harness tests and can lack time zone data on Windows. Full CI
or the Linux profile above remains the runtime gate; a green hook is not one.

## Primary sources

- [HA integration testing](https://developers.home-assistant.io/docs/creating_integration_tests/)
- [HA config-flow test coverage](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/config-flow-test-coverage/)
- [Exact upstream harness metadata](https://pypi.org/pypi/pytest-homeassistant-custom-component/0.13.316/json)
- [Current-Core harness metadata](https://pypi.org/pypi/pytest-homeassistant-custom-component/0.13.367/json)
- [Core 2026.9.4 metadata](https://pypi.org/pypi/homeassistant/2026.9.4/json)
