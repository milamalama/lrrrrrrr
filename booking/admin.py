from django.contrib import admin
from .models import Equipment, Reservation


@admin.register(Equipment)
class EquipmentAdmin(admin.ModelAdmin):
    list_display = ("name", "inventory_number", "is_active")
    search_fields = ("name", "inventory_number")
    list_filter = ("is_active",)


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ("equipment", "user", "start", "end", "confirmed")
    list_filter = ("confirmed", "equipment")
    search_fields = ("equipment__name", "user__username")
