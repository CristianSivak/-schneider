"""Server-side geocoding for the ELD Trip Planner.

Two different free OSM-backed services are used for two different jobs:

- Nominatim's `/search` only matches complete words (no prefix matching --
  querying "Chicag" returns zero results, only "Chicago" does), which makes
  it a poor fit for typeahead but a fine, precise resolver for the complete
  address strings submitted when a trip is planned. Its usage policy caps
  requests at 1/sec and requires a descriptive User-Agent; both are handled
  server-side here to respect that policy with a single shared throttle and
  to avoid CORS issues entirely.
- Photon (photon.komoot.io, built on the same OSM data, free, no API key)
  supports real prefix/typeahead matching, so it powers the location
  autocomplete suggestions as the user types.
"""

import time
from dataclasses import dataclass

import requests

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
PHOTON_URL = "https://photon.komoot.io/api/"
HEADERS = {"User-Agent": "eld-trip-planner/1.0 (contact: cristian.svk@gmail.com)"}
MIN_INTERVAL_SEC = 1.0
PHOTON_MIN_INTERVAL_SEC = 0.3

_last_call_ts = 0.0
_last_photon_call_ts = 0.0


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


def _throttle_photon():
    global _last_photon_call_ts
    elapsed = time.monotonic() - _last_photon_call_ts
    if elapsed < PHOTON_MIN_INTERVAL_SEC:
        time.sleep(PHOTON_MIN_INTERVAL_SEC - elapsed)
    _last_photon_call_ts = time.monotonic()


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


def search_locations(query: str, limit: int = 6) -> list[dict]:
    """Return up to `limit` candidate US cities/towns for a partial/typeahead query.

    Backed by Photon rather than Nominatim, since Nominatim's `/search` needs
    a complete word to match anything. `osm_tag=place` restricts results to
    populated places (city/town/village/...) so suggestions read as "City,
    State" instead of businesses or addresses that happen to contain the
    query text.
    """
    _throttle_photon()
    resp = requests.get(
        PHOTON_URL,
        params={"q": query, "limit": limit * 3, "osm_tag": "place"},
        headers=HEADERS,
        timeout=10,
    )
    resp.raise_for_status()
    results = []
    seen = set()
    for feature in resp.json().get("features", []):
        props = feature.get("properties", {})
        if props.get("countrycode") != "US":
            continue
        name = props.get("name")
        state = props.get("state")
        if not name or not state:
            continue
        label = f"{name}, {state}"
        if label in seen:
            continue
        seen.add(label)
        lng, lat = feature["geometry"]["coordinates"]
        results.append({"display_name": label, "lat": float(lat), "lng": float(lng)})
        if len(results) >= limit:
            break
    return results
