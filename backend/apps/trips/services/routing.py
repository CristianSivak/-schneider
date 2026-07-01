"""Server-side driving-route lookup via the free public OSRM demo server."""

from dataclasses import dataclass

import requests

from .geocoding import GeoPoint

OSRM_URL = "https://router.project-osrm.org/route/v1/driving/{coords}"
METERS_PER_MILE = 1609.34


class NoRouteFoundError(Exception):
    pass


class RoutingServiceError(Exception):
    pass


@dataclass
class Leg:
    distance_mi: float
    duration_hr: float


@dataclass
class RouteResult:
    legs: list[Leg]
    geometry: dict  # GeoJSON LineString


def get_route(points: list[GeoPoint]) -> RouteResult:
    coords = ";".join(f"{p.lng},{p.lat}" for p in points)
    try:
        resp = requests.get(
            OSRM_URL.format(coords=coords),
            params={"overview": "full", "geometries": "geojson", "steps": "false"},
            timeout=15,
        )
    except requests.RequestException as exc:
        raise RoutingServiceError(f"Could not reach routing service: {exc}") from exc

    if resp.status_code != 200:
        raise RoutingServiceError(f"OSRM returned HTTP {resp.status_code}")

    data = resp.json()
    if data.get("code") != "Ok" or not data.get("routes"):
        raise NoRouteFoundError("No drivable route found between the given locations")

    route = data["routes"][0]
    legs = [
        Leg(
            distance_mi=leg["distance"] / METERS_PER_MILE,
            duration_hr=leg["duration"] / 3600.0,
        )
        for leg in route["legs"]
    ]
    return RouteResult(legs=legs, geometry=route["geometry"])
