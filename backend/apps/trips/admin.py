from django.contrib import admin

from .models import Trip


@admin.register(Trip)
class TripAdmin(admin.ModelAdmin):
    list_display = ["id", "pickup_location", "dropoff_location", "status", "created_at"]
    list_filter = ["status"]
    readonly_fields = [f.name for f in Trip._meta.fields]
