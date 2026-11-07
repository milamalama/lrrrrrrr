from django.urls import path, include
from django.views.generic import RedirectView
from rest_framework.routers import DefaultRouter

from .views import (
    EquipmentViewSet,
    ReservationViewSet,
    reservations_page,
    EquipmentStatisticsView,
    equipment_analytics_page,
)


router = DefaultRouter()

router.register(
    "equipment",
    EquipmentViewSet,
    basename="equipment"
)

router.register(
    "reservations",
    ReservationViewSet,
    basename="reservations"
)


urlpatterns = [
    path(
        "reservations/",
        RedirectView.as_view(pattern_name="booking:list", permanent=False),
        name="reservations_page"
    ),

    path("api/", include(router.urls)),

    path(
    "api/equipment-statistics/",
    EquipmentStatisticsView.as_view(),
    name="equipment_statistics"
    ),

    path(
    "equipment-analytics/",
    equipment_analytics_page,
    name="equipment_analytics_page"
    ),
]
