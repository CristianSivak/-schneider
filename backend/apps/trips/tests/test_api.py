from unittest.mock import patch

import pytest
from rest_framework.test import APIClient

from apps.trips.models import Trip
from apps.trips.services.geocoding import GeoPoint, LocationNotFoundError
from apps.trips.services.routing import Leg, NoRouteFoundError, RouteResult

pytestmark = pytest.mark.django_db


def _fake_geocode(query):
    points = {
        "Chicago, IL": GeoPoint(lat=41.8781, lng=-87.6298),
        "Indianapolis, IN": GeoPoint(lat=39.7684, lng=-86.1581),
    }
    if query not in points:
        raise LocationNotFoundError(field=query, message=f"not found: {query}")
    return points[query]


def _fake_get_route(points):
    return RouteResult(
        legs=[Leg(distance_mi=0.0, duration_hr=0.0), Leg(distance_mi=185.0, duration_hr=3.0)],
        geometry={"type": "LineString", "coordinates": [[-87.6298, 41.8781], [-86.1581, 39.7684]]},
    )


@patch("apps.trips.views.get_route", side_effect=_fake_get_route)
@patch("apps.trips.views.geocode", side_effect=_fake_geocode)
def test_plan_trip_success(mock_geocode, mock_route):
    client = APIClient()
    payload = {
        "current_location": "Chicago, IL",
        "pickup_location": "Chicago, IL",
        "dropoff_location": "Indianapolis, IN",
        "current_cycle_used_hrs": 10.0,
    }
    resp = client.post("/api/trips/plan/", payload, format="json")

    assert resp.status_code == 201
    data = resp.json()
    assert data["status"] == "completed"
    assert len(data["daily_logs"]) == 1
    assert data["total_distance_miles"] == 185.0
    assert Trip.objects.count() == 1


@patch("apps.trips.views.geocode", side_effect=_fake_geocode)
def test_plan_trip_location_not_found(mock_geocode):
    client = APIClient()
    payload = {
        "current_location": "Nowhereville, XX",
        "pickup_location": "Chicago, IL",
        "dropoff_location": "Indianapolis, IN",
        "current_cycle_used_hrs": 10.0,
    }
    resp = client.post("/api/trips/plan/", payload, format="json")

    assert resp.status_code == 422
    assert resp.json()["error"] == "location_not_found"
    assert Trip.objects.count() == 0


@patch("apps.trips.views.get_route", side_effect=NoRouteFoundError("no route"))
@patch("apps.trips.views.geocode", side_effect=_fake_geocode)
def test_plan_trip_no_route_found(mock_geocode, mock_route):
    client = APIClient()
    payload = {
        "current_location": "Chicago, IL",
        "pickup_location": "Chicago, IL",
        "dropoff_location": "Indianapolis, IN",
        "current_cycle_used_hrs": 10.0,
    }
    resp = client.post("/api/trips/plan/", payload, format="json")

    assert resp.status_code == 422
    assert resp.json()["error"] == "no_route_found"


def test_trip_list_empty():
    client = APIClient()
    resp = client.get("/api/trips/")
    assert resp.status_code == 200
    assert resp.json() == []
