import uuid

from django.db import models


class Trip(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("completed", "Completed"),
        ("failed", "Failed"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)

    current_location = models.CharField(max_length=255)
    current_location_lat = models.FloatField(null=True, blank=True)
    current_location_lng = models.FloatField(null=True, blank=True)

    pickup_location = models.CharField(max_length=255)
    pickup_location_lat = models.FloatField(null=True, blank=True)
    pickup_location_lng = models.FloatField(null=True, blank=True)

    dropoff_location = models.CharField(max_length=255)
    dropoff_location_lat = models.FloatField(null=True, blank=True)
    dropoff_location_lng = models.FloatField(null=True, blank=True)

    current_cycle_used_hrs = models.FloatField()

    driver_name = models.CharField(max_length=100, default="Driver")
    carrier_name = models.CharField(max_length=100, default="N/A")
    truck_number = models.CharField(max_length=50, default="N/A")

    total_distance_miles = models.FloatField(null=True, blank=True)
    total_duration_hours = models.FloatField(null=True, blank=True)

    route_geometry = models.JSONField(null=True, blank=True)
    route_summary = models.JSONField(null=True, blank=True)
    daily_logs = models.JSONField(null=True, blank=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    error_message = models.TextField(blank=True, default="")

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.pickup_location} -> {self.dropoff_location} ({self.created_at:%Y-%m-%d})"
