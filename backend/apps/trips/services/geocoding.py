"""Server-side geocoding via the free OpenStreetMap Nominatim API.

Nominatim's usage policy caps requests at 1/sec and requires a descriptive
User-Agent. Calls happen here (server-side) rather than in the browser, both
to respect that policy with a single shared throttle and to avoid CORS
issues entirely.
"""

import time
from dataclasses import dataclass

import requests

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
HEADERS = {"User-Agent": "eld-trip-planner/1.0 (contact: cristian.svk@gmail.com)"}
MIN_INTERVAL_SEC = 1.0

_last_call_ts = 0.0


class LocationNotFoundError(Exception):
    def __init__(self, field: str, message: str):
        self.field = field
        super().__init__(message)


@dataclass
class GeoPoint:
    lat: float
    lng: float


def _throttle():
    global _last_call_ts
    elapsed = time.monotonic() - _last_call_ts
    if elapsed < MIN_INTERVAL_SEC:
        time.sleep(MIN_INTERVAL_SEC - elapsed)
    _last_call_ts = time.monotonic()


def geocode(query: str) -> GeoPoint:
    _throttle()
    resp = requests.get(
        NOMINATIM_URL,
        params={"q": query, "format": "json", "limit": 1},
        headers=HEADERS,
        timeout=10,
    )
    resp.raise_for_status()
    results = resp.json()
    if not results:
        raise LocationNotFoundError(field=query, message=f"Could not find location: '{query}'")
    return GeoPoint(lat=float(results[0]["lat"]), lng=float(results[0]["lon"]))
