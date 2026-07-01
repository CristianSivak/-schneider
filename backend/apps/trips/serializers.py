from rest_framework import serializers

from .models import Trip


class TripPlanRequestSerializer(serializers.Serializer):
    current_location = serializers.CharField(max_length=255)
    pickup_location = serializers.CharField(max_length=255)
    dropoff_location = serializers.CharField(max_length=255)
    current_cycle_used_hrs = serializers.FloatField(min_value=0, max_value=70)
    driver_name = serializers.CharField(max_length=100, required=False, default="Driver")
    carrier_name = serializers.CharField(max_length=100, required=False, default="N/A")
    truck_number = serializers.CharField(max_length=50, required=False, default="N/A")


class TripSerializer(serializers.ModelSerializer):
    class Meta:
        model = Trip
        fields = "__all__"


class TripListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Trip
        fields = [
            "id", "created_at", "current_location", "pickup_location",
            "dropoff_location", "total_distance_miles", "total_duration_hours", "status",
        ]
