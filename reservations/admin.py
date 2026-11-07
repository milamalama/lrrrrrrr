from django.contrib import admin
from .models import Equipment, Reservation, ReservationEvent


@admin.register(Equipment)
class EquipmentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "category",
        "total_quantity",
        "available_quantity"
    )
    list_filter = ("category",)
    search_fields = ("name",)


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "equipment",
        "owner",
        "quantity",
        "status",
        "created_at"
    )
    list_filter = ("status", "equipment")


@admin.register(ReservationEvent)
class ReservationEventAdmin(admin.ModelAdmin):
    list_display = (
        "reservation_id_snapshot",
        "actor",
        "action",
        "created_at"
    )
