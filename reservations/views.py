from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import F, Sum, Count
from django.db.models.functions import Coalesce
from django.shortcuts import render

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from rest_framework import serializers
from drf_spectacular.utils import extend_schema, inline_serializer

from .models import Equipment, Reservation, ReservationEvent
from .serializers import (
    EquipmentSerializer,
    ReservationSerializer,
    EventSerializer,
)


@login_required
def reservations_page(request):
    return render(request, "reservations/dashboard.html")

@login_required
def equipment_analytics_page(request):
    return render(request, "reservations/analytics.html")



class EquipmentViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = EquipmentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Equipment.objects.all()

        search = self.request.query_params.get("search", "").strip()
        category = self.request.query_params.get("category", "")

        if category:
            queryset = queryset.filter(category=category)

        if search:
            search_text = search.casefold()

            found_ids = [
                item.id
                for item in queryset
                if search_text in item.name.casefold()
            ]

            queryset = queryset.filter(id__in=found_ids)

        return queryset.order_by("name")


class ReservationViewSet(viewsets.ModelViewSet):
    queryset = Reservation.objects.none()
    serializer_class = ReservationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Reservation.objects.filter(
            owner=self.request.user
        ).select_related("equipment")

        status_filter = self.request.query_params.get("status")
        equipment_filter = self.request.query_params.get("equipment")

        if status_filter:
            queryset = queryset.filter(status=status_filter)

        if equipment_filter:
            queryset = queryset.filter(equipment_id=equipment_filter)

        return queryset.order_by("-created_at")

    def add_event(self, reservation, action_name):
        ReservationEvent.objects.create(
            reservation=reservation,
            reservation_id_snapshot=reservation.id,
            actor=self.request.user,
            action=action_name
        )

    def perform_create(self, serializer):
        with transaction.atomic():
            reservation = serializer.save(
                owner=self.request.user
            )

            self.add_event(
                reservation,
                "Создано бронирование"
            )

    def perform_update(self, serializer):
        with transaction.atomic():
            reservation = serializer.save()

            self.add_event(
                reservation,
                "Изменены данные бронирования"
            )

    def perform_destroy(self, instance):
        with transaction.atomic():
            reservation = self.get_queryset().select_for_update().get(
                pk=instance.pk
            )

            if reservation.status == Reservation.Status.CONFIRMED:
                raise ValidationError(
                    "Нельзя удалить подтверждённую бронь. "
                    "Сначала завершите её."
                )

            self.add_event(
                reservation,
                "Бронирование удалено"
            )

            reservation.delete()

    @action(detail=True, methods=["post"])
    def confirm(self, request, pk=None):
        with transaction.atomic():
            reservation = self.get_queryset().select_for_update().get(
                pk=self.get_object().pk
            )

            if reservation.status != Reservation.Status.CREATED:
                raise ValidationError(
                    "Подтвердить можно только созданную бронь."
                )

            updated = Equipment.objects.filter(
                pk=reservation.equipment_id,
                available_quantity__gte=reservation.quantity
            ).update(
                available_quantity=(
                    F("available_quantity") - reservation.quantity
                )
            )

            if updated == 0:
                raise ValidationError(
                    "Недостаточно доступного оборудования."
                )

            reservation.status = Reservation.Status.CONFIRMED
            reservation.save(update_fields=["status"])

            self.add_event(
                reservation,
                "Бронирование подтверждено"
            )

        return Response({
            "message": "Бронирование подтверждено."
        })

    @action(detail=True, methods=["post"])
    def complete(self, request, pk=None):
        with transaction.atomic():
            reservation = self.get_queryset().select_for_update().get(
                pk=self.get_object().pk
            )

            if reservation.status != Reservation.Status.CONFIRMED:
                raise ValidationError(
                    "Завершить можно только подтверждённую бронь."
                )

            Equipment.objects.filter(
                pk=reservation.equipment_id
            ).update(
                available_quantity=(
                    F("available_quantity") + reservation.quantity
                )
            )

            reservation.status = Reservation.Status.COMPLETED
            reservation.save(update_fields=["status"])

            self.add_event(
                reservation,
                "Оборудование возвращено"
            )

        return Response({
            "message": "Бронирование завершено."
        })

    @action(detail=True, methods=["get"])
    def history(self, request, pk=None):
        reservation = self.get_object()

        events = ReservationEvent.objects.filter(
            reservation=reservation
        ).order_by("-created_at")

        serializer = EventSerializer(events, many=True)

        return Response(serializer.data)


class EquipmentStatisticsView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={
            200: inline_serializer(
                name="EquipmentStatistics",
                fields={
                    "equipment_types": serializers.IntegerField(),
                    "total_units": serializers.IntegerField(),
                    "available_units": serializers.IntegerField(),
                    "occupied_units": serializers.IntegerField(),
                    "created_count": serializers.IntegerField(),
                    "confirmed_count": serializers.IntegerField(),
                    "completed_count": serializers.IntegerField(),
                    "popular_equipment": inline_serializer(
                        name="PopularEquipment",
                        fields={
                            "name": serializers.CharField(),
                            "count": serializers.IntegerField(),
                        },
                        many=True,
                    ),
                },
            ),
        },
    )

    def get(self, request):
        equipment = Equipment.objects.all()

        equipment_types = equipment.count()

        total_units = equipment.aggregate(
            total=Coalesce(Sum("total_quantity"), 0)
        )["total"]

        available_units = equipment.aggregate(
            total=Coalesce(Sum("available_quantity"), 0)
        )["total"]

        occupied_units = total_units - available_units

        reservations = Reservation.objects.filter(
            owner=request.user
        )

        created_count = reservations.filter(
            status=Reservation.Status.CREATED
        ).count()

        confirmed_count = reservations.filter(
            status=Reservation.Status.CONFIRMED
        ).count()

        completed_count = reservations.filter(
            status=Reservation.Status.COMPLETED
        ).count()

        popular_equipment = (
            reservations
            .values("equipment__name")
            .annotate(total=Count("id"))
            .order_by("-total", "equipment__name")[:5]
        )

        popular_list = [
            {
                "name": item["equipment__name"],
                "count": item["total"]
            }
            for item in popular_equipment
        ]

        return Response({
            "equipment_types": equipment_types,
            "total_units": total_units,
            "available_units": available_units,
            "occupied_units": occupied_units,
            "created_count": created_count,
            "confirmed_count": confirmed_count,
            "completed_count": completed_count,
            "popular_equipment": popular_list
        })
