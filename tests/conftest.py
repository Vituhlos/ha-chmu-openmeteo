"""Shared test setup.

The full development requirements install Home Assistant and its real harness.
When Home Assistant is absent, a minimal stub lets the logic tests run from a
bare virtualenv; real-harness modules skip themselves. Each test module used
to build its own stub, which made the result depend on collection order.
"""

import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType
from typing import Any
from unittest.mock import MagicMock

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


class _ConfigEntry:
    """Stub for ConfigEntry."""

    def __class_getitem__(cls, item):
        """Accept the ConfigEntry[RuntimeData] annotation form."""
        return cls


class _Platform:
    """Stub for Platform."""

    SENSOR = "sensor"
    WEATHER = "weather"


class _HomeAssistant:
    """Stub for HomeAssistant."""


class _DataUpdateCoordinator:
    """Stub for DataUpdateCoordinator."""

    def __class_getitem__(cls, item):
        """Accept the DataUpdateCoordinator[T] annotation form."""
        return cls


class _UpdateFailed(Exception):
    """Stub for UpdateFailed."""


def _install_homeassistant_stub() -> None:
    """Register stub Home Assistant modules, unless the real ones are present.

    Checked with find_spec rather than sys.modules: the real package is only in
    sys.modules once something has imported it, so a stub installed here would
    win purely by running first.
    """
    if importlib.util.find_spec("homeassistant") is not None:
        return

    for module_path, attrs in [
        ("homeassistant", {}),
        ("homeassistant.config_entries", {"ConfigEntry": _ConfigEntry}),
        ("homeassistant.const", {"Platform": _Platform}),
        ("homeassistant.core", {"HomeAssistant": _HomeAssistant}),
        ("homeassistant.helpers", {}),
        (
            "homeassistant.helpers.update_coordinator",
            {
                "DataUpdateCoordinator": _DataUpdateCoordinator,
                "UpdateFailed": _UpdateFailed,
            },
        ),
    ]:
        module = ModuleType(module_path)
        for name, value in attrs.items():
            setattr(module, name, value)
        sys.modules[module_path] = module


_install_homeassistant_stub()


@pytest.fixture
def rudolec_metadata() -> dict[str, Any]:
    """Load reduced, captured public metadata without contacting ČHMÚ."""
    directory = ROOT / "tests" / "fixtures" / "rudolec"
    return {
        prefix: json.loads((directory / f"{prefix}.json").read_text(encoding="utf-8"))
        for prefix in ("meta1", "meta2")
    }


@pytest.fixture
def rudolec_session(monkeypatch, rudolec_metadata) -> MagicMock:
    """Serve only static metadata; fail on any unexpected endpoint."""
    from custom_components.chmu import api

    session = MagicMock()

    def get(url: str, **kwargs) -> MagicMock:
        for prefix in ("meta1", "meta2"):
            if f"/{prefix}-" in url:
                response = MagicMock()
                response.status_code = 200
                response.json.return_value = rudolec_metadata[prefix]
                return response
        raise AssertionError(f"Unexpected request in offline Rudolec test: {url}")

    session.get.side_effect = get
    monkeypatch.setattr(api, "new_session", lambda: session)
    return session


@pytest.fixture
def rudolec_station(rudolec_session) -> dict[str, Any]:
    """Discover the reference station using the actual upstream parser."""
    from custom_components.chmu.api import get_stations_with_coords

    return get_stations_with_coords()["0-203-0-11526"]
