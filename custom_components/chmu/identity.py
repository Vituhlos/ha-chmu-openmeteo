"""Compare station identities without rewriting stored registry identifiers."""

import re

from .const import WMO_WSI_PREFIX


def canonical_station_id(station_id: str) -> str:
    """Expand only the documented five-digit professional WMO alias.

    Automatic and other WSI authorities are distinct, even with the same tail.
    This comparison key is never substituted into existing entity unique IDs.
    """
    if re.fullmatch(r"[0-9]{5}", station_id):
        return f"{WMO_WSI_PREFIX}{station_id}"
    return station_id


def discovery_station_id(wsi: str) -> str:
    """Keep upstream's professional short IDs and all other full WSIs."""
    match = re.fullmatch(r"0-20000-0-([0-9]{5})", wsi)
    return match[1] if match else wsi
