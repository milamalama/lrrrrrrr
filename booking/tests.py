
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Equipment, Reservation


class ReservationAccessTests(TestCase):

    def setUp(self):
        User = get_user_model()

        self.user1 = User.objects.create_user(
            username="test_student1",
            password="TestPass123!"
        )
        self.user2 = User.objects.create_user(
            username="test_student2",
            password="TestPass456!"
        )

        self.equipment = Equipment.objects.create(
            name="Тестовый ноутбук",
            inventory_number="TEST-001",
            is_active=True
        )

        start = timezone.now() + timedelta(days=1)

        self.reservation = Reservation.objects.create(
            equipment=self.equipment,
            user=self.user1,
            start=start,
            end=start + timedelta(days=1),
            purpose="Проверка доступа",
            confirmed=True
        )

    def test_owner_can_edit(self):
        self.client.force_login(self.user1)

        url = reverse(
            "reservation_edit",
            args=[self.reservation.pk]
        )

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_other_user_cannot_edit(self):
        self.client.force_login(self.user2)

        url = reverse(
            "reservation_edit",
            args=[self.reservation.pk]
        )

        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_owner_can_cancel(self):
        self.client.force_login(self.user1)

        url = reverse(
            "reservation_cancel",
            args=[self.reservation.pk]
        )

        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)

        self.reservation.refresh_from_db()
        self.assertFalse(self.reservation.confirmed)

    def test_other_user_cannot_cancel(self):
        self.client.force_login(self.user2)

        url = reverse(
            "reservation_cancel",
            args=[self.reservation.pk]
        )

        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)

        self.reservation.refresh_from_db()
        self.assertTrue(self.reservation.confirmed)


class ReservationFunctionTests(TestCase):

    def setUp(self):
        User = get_user_model()

        self.user = User.objects.create_user(
            username="test_owner",
            password="TestPass123!"
        )
        self.other_user = User.objects.create_user(
            username="test_other",
            password="TestPass456!"
        )

        self.equipment1 = Equipment.objects.create(
            name="Ноутбук ASUS",
            inventory_number="AUTO-001"
        )
        self.equipment2 = Equipment.objects.create(
            name="Проектор Epson",
            inventory_number="AUTO-002"
        )

        self.start = (
            timezone.now()
            .replace(second=0, microsecond=0)
            + timedelta(days=10)
        )
        self.end = self.start + timedelta(hours=2)

        self.client.force_login(self.user)

    def create_reservation(
        self, equipment=None, start=None, end=None,
        user=None, confirmed=True
    ):
        return Reservation.objects.create(
            equipment=equipment or self.equipment1,
            user=user or self.user,
            start=start if start is not None else self.start,
            end=end if end is not None else self.end,
            purpose="Лабораторная работа",
            confirmed=confirmed
        )

    def form_data(self, equipment=None, start=None, end=None):
        start = start if start is not None else self.start
        end = end if end is not None else self.end

        return {
            "equipment": (equipment or self.equipment1).pk,
            "start": timezone.localtime(start).strftime(
                "%Y-%m-%dT%H:%M"
            ),
            "end": timezone.localtime(end).strftime(
                "%Y-%m-%dT%H:%M"
            ),
            "purpose": "Тест бронирования"
        }

    # 1. Корректное бронирование
    def test_valid_reservation(self):
        response = self.client.post(
            reverse("reservation_create"),
            self.form_data()
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(Reservation.objects.count(), 1)

    # 2. Конец раньше начала
    def test_end_before_start(self):
        reservation = self.create_reservation(
            start=self.end,
            end=self.start
        )

        with self.assertRaises(ValidationError):
            reservation.full_clean()

    # 3. Начало равно окончанию
    def test_equal_start_end(self):
        reservation = self.create_reservation(
            start=self.start,
            end=self.start
        )

        with self.assertRaises(ValidationError):
            reservation.full_clean()

    # 4. Пересекающаяся бронь отклоняется
    def test_overlapping_reservation(self):
        self.create_reservation()

        response = self.client.post(
            reverse("reservation_create"),
            self.form_data(
                start=self.start + timedelta(hours=1),
                end=self.end + timedelta(hours=1)
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Reservation.objects.count(), 1)
        self.assertFalse(
            response.context["form"].is_valid()
        )

    # 5. Другое оборудование на то же время
    def test_different_equipment(self):
        self.create_reservation()

        response = self.client.post(
            reverse("reservation_create"),
            self.form_data(equipment=self.equipment2)
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(Reservation.objects.count(), 2)

    # 6. Касание временных границ
    def test_touching_boundaries(self):
        self.create_reservation()

        response = self.client.post(
            reverse("reservation_create"),
            self.form_data(
                start=self.end,
                end=self.end + timedelta(hours=2)
            )
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(Reservation.objects.count(), 2)

    # 7. Редактирование без конфликта с собой
    def test_edit_without_self_conflict(self):
        reservation = self.create_reservation()

        data = self.form_data()
        data["purpose"] = "Новая цель"

        response = self.client.post(
            reverse("reservation_edit", args=[reservation.pk]),
            data
        )

        self.assertEqual(response.status_code, 302)

        reservation.refresh_from_db()
        self.assertEqual(reservation.purpose, "Новая цель")
        self.assertEqual(Reservation.objects.count(), 1)

    # 8. Отмена освобождает временной интервал
    def test_cancel_releases_equipment(self):
        reservation = self.create_reservation()

        self.client.post(
            reverse("reservation_cancel", args=[reservation.pk])
        )

        reservation.refresh_from_db()
        self.assertFalse(reservation.confirmed)

        response = self.client.post(
            reverse("reservation_create"),
            self.form_data()
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(Reservation.objects.count(), 2)

    # 9. Отмена через GET запрещена
    def test_cancel_requires_post(self):
        reservation = self.create_reservation()

        response = self.client.get(
            reverse("reservation_cancel", args=[reservation.pk])
        )

        self.assertEqual(response.status_code, 405)

        reservation.refresh_from_db()
        self.assertTrue(reservation.confirmed)

    # 10. Удаление через GET запрещено
    def test_delete_requires_post(self):
        reservation = self.create_reservation()

        response = self.client.get(
            reverse("reservation_delete", args=[reservation.pk])
        )

        self.assertEqual(response.status_code, 405)
        self.assertTrue(
            Reservation.objects.filter(pk=reservation.pk).exists()
        )

    # 11. Удаление через POST работает
    def test_delete_via_post(self):
        reservation = self.create_reservation()

        response = self.client.post(
            reverse("reservation_delete", args=[reservation.pk])
        )

        self.assertEqual(response.status_code, 302)
        self.assertFalse(
            Reservation.objects.filter(pk=reservation.pk).exists()
        )

    # 12. Фильтр не показывает чужие записи
    def test_filter_only_own_reservations(self):
        own = self.create_reservation()
        foreign = self.create_reservation(
            equipment=self.equipment2,
            user=self.other_user
        )

        response = self.client.get(
            reverse("reservation_list"),
            {"equipment": self.equipment2.pk}
        )

        self.assertEqual(response.status_code, 200)
        self.assertNotIn(
            foreign.pk,
            [item.pk for item in response.context["items"]]
        )

        response = self.client.get(
            reverse("reservation_list"),
            {"equipment": self.equipment1.pk}
        )

        self.assertEqual(
            [item.pk for item in response.context["items"]],
            [own.pk]
        )
