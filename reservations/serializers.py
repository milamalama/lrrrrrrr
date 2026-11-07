from rest_framework import serializers
from .models import Equipment, Reservation, ReservationEvent


class EquipmentSerializer(serializers.ModelSerializer):

    class Meta:
        model = Equipment
        fields = [
            "id",
            "name",
            "category",
            "total_quantity",
            "available_quantity",
        ]


class ReservationSerializer(serializers.ModelSerializer):

    equipment_name = serializers.CharField(
        source="equipment.name",
        read_only=True
    )

    class Meta:
        model = Reservation

        fields = [
            "id",
            "equipment",
            "equipment_name",
            "owner",
            "quantity",
            "status",
            "created_at",
        ]

        read_only_fields = [
            "id",
            "owner",
            "status",
            "created_at",
        ]

    def validate_quantity(self, value):
        if value < 1:
            raise serializers.ValidationError(
                "Количество должно быть больше нуля."
            )
        return value

    def validate(self, attrs):
        if self.instance:
            if self.instance.status != Reservation.Status.CREATED:
                raise serializers.ValidationError(
                    "Редактировать можно только созданную бронь."
                )

        return attrs


class EventSerializer(serializers.ModelSerializer):

    actor_name = serializers.CharField(
        source="actor.username",
        read_only=True,
        default=None
    )

    class Meta:
        model = ReservationEvent

        fields = [
            "id",
            "reservation_id_snapshot",
            "actor_name",
            "action",
            "created_at",
        ]
