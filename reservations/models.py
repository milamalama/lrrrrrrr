
from django.conf import settings
from django.db import models
from django.core.validators import MinValueValidator


class Equipment(models.Model):
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=50)

    total_quantity = models.PositiveIntegerField(
        validators=[MinValueValidator(1)]
    )
    available_quantity = models.PositiveIntegerField()

    def __str__(self):
        return self.name


class Reservation(models.Model):

    class Status(models.TextChoices):
        CREATED = "created", "Создана"
        CONFIRMED = "confirmed", "Подтверждена"
        COMPLETED = "completed", "Завершена"

    equipment = models.ForeignKey(
        Equipment,
        on_delete=models.PROTECT,
        related_name="reservations"
    )

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    quantity = models.PositiveIntegerField(
        validators=[MinValueValidator(1)]
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.CREATED
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Бронирование №{self.id}"


class ReservationEvent(models.Model):
    reservation = models.ForeignKey(
        Reservation,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="events"
    )

    reservation_id_snapshot = models.PositiveIntegerField()

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True
    )

    action = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.action
