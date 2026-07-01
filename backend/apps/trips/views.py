from django.utils import timezone
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView

from .hos.engine import plan_trip
from .models import Trip
from .serializers import TripListSerializer, TripPlanRequestSerializer, TripSerializer
from .services.geocoding import LocationNotFoundError, geocode
from .services.routing import NoRouteFoundError, RoutingServiceError, get_route


class TripPlanView(APIView):
    def post(self, request):
        req = TripPlanRequestSerializer(data=request.data)
        req.is_valid(raise_exception=True)
        d = req.validated_data

        try:
            current = geocode(d["current_location"])
        except LocationNotFoundError as exc:
            return Response({"error": "location_not_found", "field": "current_location", "message": str(exc)}, status=422)
        try:
            pickup = geocode(d["pickup_location"])
        except LocationNotFoundError as exc:
            return Response({"error": "location_not_found", "field": "pickup_location", "message": str(exc)}, status=422)
        try:
            dropoff = geocode(d["dropoff_location"])
        except LocationNotFoundError as exc:
            return Response({"error": "location_not_found", "field": "dropoff_location", "message": str(exc)}, status=422)

        try:
            route = get_route([current, pickup, dropoff])
        except NoRouteFoundError as exc:
            return Response({"error": "no_route_found", "message": str(exc)}, status=422)
        except RoutingServiceError as exc:
            return Response({"error": "upstream_service_unavailable", "message": str(exc)}, status=502)

        leg1, leg2 = route.legs[0], route.legs[1]

        plan = plan_trip(
            leg1_distance_mi=leg1.distance_mi,
            leg1_duration_hr=leg1.duration_hr,
            leg2_distance_mi=leg2.distance_mi,
            leg2_duration_hr=leg2.duration_hr,
            current_cycle_used_hr=d["current_cycle_used_hrs"],
            trip_start=timezone.now(),
            pickup_location_name=d["pickup_location"],
            dropoff_location_name=d["dropoff_location"],
            current_location_name=d["current_location"],
        )

        trip = Trip.objects.create(
            current_location=d["current_location"],
            current_location_lat=current.lat,
            current_location_lng=current.lng,
            pickup_location=d["pickup_location"],
            pickup_location_lat=pickup.lat,
            pickup_location_lng=pickup.lng,
            dropoff_location=d["dropoff_location"],
            dropoff_location_lat=dropoff.lat,
            dropoff_location_lng=dropoff.lng,
            current_cycle_used_hrs=d["current_cycle_used_hrs"],
            driver_name=d["driver_name"],
            carrier_name=d["carrier_name"],
            truck_number=d["truck_number"],
            total_distance_miles=plan.total_distance_miles,
            total_duration_hours=plan.total_duration_hours,
            route_geometry=route.geometry,
            route_summary=plan.stops_summary,
            daily_logs=plan.daily_logs_json,
            status="completed",
        )
        return Response(TripSerializer(trip).data, status=201)


class TripListView(generics.ListAPIView):
    queryset = Trip.objects.all()[:50]
    serializer_class = TripListSerializer


class TripDetailView(generics.RetrieveAPIView):
    queryset = Trip.objects.all()
    serializer_class = TripSerializer
