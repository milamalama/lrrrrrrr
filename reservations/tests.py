from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase

from rest_framework.test import APIClient

from .models import Equipment, Reservation, ReservationEvent
from .views import ReservationViewSet


class ReservationTests(TestCase):

    def setUp(self):
        User = get_user_model()

        self.user1 = User.objects.create_user(
            username="test_student1",
            password="TestPassword123!"
        )

        self.user2 = User.objects.create_user(
            username="test_student2",
            password="TestPassword123!"
        )

        self.equipment = Equipment.objects.create(
            name="Тестовый ноутбук",
            category="Компьютеры",
            total_quantity=5,
            available_quantity=5
        )

        self.other_equipment = Equipment.objects.create(
            name="Тестовый проектор",
            category="Проекторы",
            total_quantity=3,
            available_quantity=3
        )

        self.client = APIClient()
        self.client.force_authenticate(user=self.user1)

    def create_reservation(self, quantity=2):
        return self.client.post(
            "/api/reservations/",
            {
                "equipment": self.equipment.id,
                "quantity": quantity
            },
            format="json"
        )

    def test_create_reservation(self):
        response = self.create_reservation()

        self.assertEqual(response.status_code, 201)

        reservation = Reservation.objects.get(
            id=response.data["id"]
        )

        self.assertEqual(reservation.status, "created")
        self.assertEqual(reservation.owner, self.user1)

        self.assertEqual(
            ReservationEvent.objects.filter(
                reservation=reservation
            ).count(),
            1
        )

    def test_confirm_reservation(self):
        response = self.create_reservation()
        reservation_id = response.data["id"]

        response = self.client.post(
            f"/api/reservations/{reservation_id}/confirm/"
        )

        self.assertEqual(response.status_code, 200)

        self.equipment.refresh_from_db()

        reservation = Reservation.objects.get(id=reservation_id)

        self.assertEqual(self.equipment.available_quantity, 3)
        self.assertEqual(reservation.status, "confirmed")

        self.assertEqual(
            ReservationEvent.objects.filter(
                reservation=reservation
            ).count(),
            2
        )

    def test_complete_reservation(self):
        response = self.create_reservation()
        reservation_id = response.data["id"]

        self.client.post(
            f"/api/reservations/{reservation_id}/confirm/"
        )

        response = self.client.post(
            f"/api/reservations/{reservation_id}/complete/"
        )

        self.assertEqual(response.status_code, 200)

        self.equipment.refresh_from_db()

        reservation = Reservation.objects.get(id=reservation_id)

        self.assertEqual(self.equipment.available_quantity, 5)
        self.assertEqual(reservation.status, "completed")

    def test_forbidden_transition(self):
        response = self.create_reservation()
        reservation_id = response.data["id"]

        response = self.client.post(
            f"/api/reservations/{reservation_id}/complete/"
        )

        self.assertEqual(response.status_code, 400)

        reservation = Reservation.objects.get(id=reservation_id)

        self.assertEqual(reservation.status, "created")

        self.assertEqual(
            ReservationEvent.objects.filter(
                reservation=reservation
            ).count(),
            1
        )

    def test_double_confirmation(self):
        response = self.create_reservation()
        reservation_id = response.data["id"]

        url = f"/api/reservations/{reservation_id}/confirm/"

        self.client.post(url)
        response = self.client.post(url)

        self.assertEqual(response.status_code, 400)

        self.equipment.refresh_from_db()
        self.assertEqual(self.equipment.available_quantity, 3)

    def test_not_enough_equipment(self):
        response = self.create_reservation(quantity=10)
        reservation_id = response.data["id"]

        response = self.client.post(
            f"/api/reservations/{reservation_id}/confirm/"
        )

        self.assertEqual(response.status_code, 400)

        self.equipment.refresh_from_db()

        reservation = Reservation.objects.get(id=reservation_id)

        self.assertEqual(self.equipment.available_quantity, 5)
        self.assertEqual(reservation.status, "created")

    def test_other_user_access(self):
        response = self.create_reservation()
        reservation_id = response.data["id"]

        self.client.force_authenticate(user=self.user2)

        url = f"/api/reservations/{reservation_id}/"

        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

        response = self.client.patch(
            url,
            {"quantity": 3},
            format="json"
        )
        self.assertEqual(response.status_code, 404)

        response = self.client.delete(url)
        self.assertEqual(response.status_code, 404)

    def test_transaction_rollback(self):
        response = self.create_reservation()
        reservation_id = response.data["id"]

        url = f"/api/reservations/{reservation_id}/confirm/"

        with patch.object(
            ReservationViewSet,
            "add_event",
            side_effect=RuntimeError("Искусственная ошибка")
        ):
            with self.assertRaises(RuntimeError):
                self.client.post(url)

        self.equipment.refresh_from_db()

        reservation = Reservation.objects.get(id=reservation_id)

        self.assertEqual(self.equipment.available_quantity, 5)
        self.assertEqual(reservation.status, "created")

        self.assertEqual(
            ReservationEvent.objects.filter(
                reservation=reservation
            ).count(),
            1
        )

    def test_delete_reservation(self):
        response = self.create_reservation()
        reservation_id = response.data["id"]

        response = self.client.delete(
            f"/api/reservations/{reservation_id}/"
        )

        self.assertEqual(response.status_code, 204)

        self.assertFalse(
            Reservation.objects.filter(
                id=reservation_id
            ).exists()
        )

        self.assertTrue(
            ReservationEvent.objects.filter(
                reservation_id_snapshot=reservation_id,
                action="Бронирование удалено"
            ).exists()
        )

    def test_two_filters(self):
        first = self.create_reservation()

        second = self.client.post(
            "/api/reservations/",
            {
                "equipment": self.other_equipment.id,
                "quantity": 1
            },
            format="json"
        )

        self.client.post(
            f"/api/reservations/{second.data['id']}/confirm/"
        )

        response = self.client.get(
            "/api/reservations/",
            {
                "status": "created",
                "equipment": self.equipment.id
            }
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

        self.assertEqual(
            response.data[0]["id"],
            first.data["id"]
        )
