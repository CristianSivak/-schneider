from django.urls import path

from . import views

urlpatterns = [
    path("trips/plan/", views.TripPlanView.as_view()),
    path("trips/", views.TripListView.as_view()),
    path("trips/<uuid:pk>/", views.TripDetailView.as_view()),
]
