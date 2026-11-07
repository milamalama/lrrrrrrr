from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class Equipment(models.Model):
    name = models.CharField('Название', max_length=100)
    inventory_number = models.CharField('Инвентарный номер', max_length=50, unique=True)
    is_active = models.BooleanField('Доступно для бронирования', default=True)

    class Meta:
        ordering = ('name', 'inventory_number')
        verbose_name = 'устройство'
        verbose_name_plural = 'Устройства для бронирования'

    def __str__(self):
        return f'{self.name} ({self.inventory_number})'


class Reservation(models.Model):
    equipment = models.ForeignKey(Equipment, on_delete=models.PROTECT, verbose_name='Устройство')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name='Владелец', related_name='timed_bookings')
    start = models.DateTimeField('Начало')
    end = models.DateTimeField('Конец')
    purpose = models.CharField('Цель', max_length=300)
    confirmed = models.BooleanField('Действует', default=True)

    class Meta:
        ordering = ('-start',)
        verbose_name = 'бронь по времени'
        verbose_name_plural = 'Брони по времени'
        constraints = [models.CheckConstraint(condition=models.Q(end__gt=models.F('start')), name='booking_end_after_start')]
        indexes = [models.Index(fields=['equipment', 'confirmed', 'start', 'end'], name='booking_interval_idx')]

    def clean(self):
        super().clean()
        if self.start and self.end and self.end <= self.start:
            raise ValidationError({'end': 'Конец должен быть позже начала.'})
        if self.equipment_id and self.confirmed:
            if not self.equipment.is_active:
                raise ValidationError({'equipment': 'Нельзя бронировать неактивное оборудование.'})
            if self.start and self.end:
                conflicts = Reservation.objects.filter(equipment_id=self.equipment_id, confirmed=True, start__lt=self.end, end__gt=self.start)
                if self.pk:
                    conflicts = conflicts.exclude(pk=self.pk)
                if conflicts.exists():
                    raise ValidationError('Выбранное оборудование уже забронировано на указанный период. Выберите другое время.')

    def __str__(self):
        return f'Бронь №{self.pk}: {self.equipment}'


class ReservationEvent(models.Model):
    reservation = models.ForeignKey(Reservation, null=True, blank=True, on_delete=models.SET_NULL)
    reservation_number = models.PositiveBigIntegerField()
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="timed_booking_events")
    action = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-created_at',)
        verbose_name_plural = 'История бронирований по времени'
