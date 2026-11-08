from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class Equipment(models.Model):
    name = models.CharField(max_length=120)
    inventory_number = models.CharField(max_length=30, unique=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.inventory_number})"


class Reservation(models.Model):
    equipment = models.ForeignKey(
        Equipment,
        on_delete=models.PROTECT,
        related_name="reservations"
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    start = models.DateTimeField()
    end = models.DateTimeField()
    confirmed = models.BooleanField(default=True)
    purpose = models.CharField(max_length=300)

    def clean(self):
        super().clean()

        if self.start and self.end and self.start >= self.end:
            raise ValidationError({
                "end": "Конец должен быть позже начала."
            })

        if self.equipment_id and self.confirmed:
            if not self.equipment.is_active:
                raise ValidationError(
                    "Нельзя бронировать неактивное оборудование."
                )

            if self.start and self.end:
                conflicts = Reservation.objects.filter(
                    equipment_id=self.equipment_id,
                    confirmed=True,
                    start__lt=self.end,
                    end__gt=self.start
                )

                if self.pk:
                    conflicts = conflicts.exclude(pk=self.pk)

                if conflicts.exists():
                    raise ValidationError(
                        "Выбранное оборудование уже забронировано "
                        "на указанный период. Выберите другое время."
                    )

    def __str__(self):
        return f"{self.equipment} / {self.start} - {self.end}"
