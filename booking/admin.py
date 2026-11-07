from django.contrib import admin
from .models import Equipment, Reservation, ReservationEvent


@admin.register(Equipment)
class EquipmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'inventory_number', 'is_active')
    search_fields = ('name', 'inventory_number')
    list_filter = ('is_active',)


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ('equipment', 'user', 'start', 'end', 'confirmed')
    list_filter = ('confirmed', 'equipment')
    search_fields = ('equipment__name', 'equipment__inventory_number', 'user__username')

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        ReservationEvent.objects.create(reservation=obj, reservation_number=obj.pk, user=obj.user, action='Изменена в админке' if change else 'Создана в админке')


@admin.register(ReservationEvent)
class EventAdmin(admin.ModelAdmin):
    list_display = ('reservation_number', 'user', 'action', 'created_at')
    readonly_fields = ('reservation', 'reservation_number', 'user', 'action', 'created_at')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
