from datetime import timedelta
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from .models import Equipment, Reservation, ReservationEvent


@override_settings(STORAGES={'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'}})
class BookingTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user('alice')
        cls.other = get_user_model().objects.create_user('bob')
        cls.equipment = Equipment.objects.create(name='Ноутбук', inventory_number='N1')
        cls.second = Equipment.objects.create(name='Камера', inventory_number='N2')
        cls.start = timezone.now().replace(second=0, microsecond=0) + timedelta(days=1)
        cls.end = cls.start + timedelta(hours=2)

    def setUp(self):
        self.client.force_login(self.user)

    def item(self, **changes):
        data = dict(user=self.user, equipment=self.equipment, start=self.start, end=self.end, purpose='Лабораторная')
        data.update(changes)
        return Reservation.objects.create(**data)

    def data(self, **changes):
        data = dict(equipment=self.equipment.pk, start=timezone.localtime(self.start).strftime('%Y-%m-%dT%H:%M'), end=timezone.localtime(self.end).strftime('%Y-%m-%dT%H:%M'), purpose='Практика')
        data.update(changes)
        return data

    def test_create_and_server_owner(self):
        response = self.client.post(reverse('booking:create'), self.data(user=self.other.pk))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Reservation.objects.get().user, self.user)
        self.assertEqual(ReservationEvent.objects.count(), 1)

    def test_overlap_rejected_with_message(self):
        self.item()
        response = self.client.post(reverse('booking:create'), self.data())
        self.assertContains(response, 'уже забронировано')
        self.assertEqual(Reservation.objects.count(), 1)

    def test_equal_dates(self):
        response = self.client.post(reverse('booking:create'), self.data(end=self.data()['start']))
        self.assertContains(response, 'Конец должен быть позже начала')
        self.assertEqual(Reservation.objects.count(), 0)

    def test_reversed_dates(self):
        response = self.client.post(reverse('booking:create'), self.data(start=self.data()['end'], end=self.data()['start']))
        self.assertContains(response, 'Конец должен быть позже начала')
        self.assertFalse(Reservation.objects.exists())

    def test_different_device(self):
        self.item()
        self.assertEqual(self.client.post(reverse('booking:create'), self.data(equipment=self.second.pk)).status_code, 302)
        self.assertEqual(Reservation.objects.count(), 2)

    def test_touching_boundary(self):
        self.item()
        new_start = timezone.localtime(self.end).strftime('%Y-%m-%dT%H:%M')
        new_end = timezone.localtime(self.end + timedelta(hours=1)).strftime('%Y-%m-%dT%H:%M')
        self.assertEqual(self.client.post(reverse('booking:create'), self.data(start=new_start, end=new_end)).status_code, 302)
        self.assertEqual(Reservation.objects.count(), 2)

    def test_edit_self_without_conflict(self):
        item = self.item()
        self.assertEqual(self.client.post(reverse('booking:edit', args=[item.pk]), self.data(purpose='Новая цель')).status_code, 302)
        item.refresh_from_db()
        self.assertEqual(item.purpose, 'Новая цель')

    def test_other_user_operations(self):
        item = self.item(user=self.other)
        self.assertEqual(self.client.get(reverse('booking:edit', args=[item.pk])).status_code, 404)
        for action in ('edit', 'cancel', 'delete'):
            self.assertEqual(self.client.post(reverse('booking:'+action, args=[item.pk]), self.data()).status_code, 404)
        item.refresh_from_db()
        self.assertTrue(item.confirmed)

    def test_cancel_preserves_and_frees(self):
        item = self.item()
        self.client.post(reverse('booking:cancel', args=[item.pk]))
        item.refresh_from_db()
        self.assertFalse(item.confirmed)
        self.assertEqual(self.client.post(reverse('booking:create'), self.data()).status_code, 302)
        self.assertEqual(Reservation.objects.count(), 2)

    def test_cancel_and_delete_require_post(self):
        item = self.item()
        for action in ('cancel', 'delete'):
            self.assertEqual(self.client.get(reverse('booking:'+action, args=[item.pk])).status_code, 405)
        self.assertTrue(Reservation.objects.filter(pk=item.pk).exists())

    def test_csrf_enforced(self):
        from django.test import Client
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.user)
        item = self.item()
        for action in ('cancel', 'delete'):
            self.assertEqual(client.post(reverse('booking:'+action, args=[item.pk])).status_code, 403)

    def test_delete_keeps_audit(self):
        item = self.item()
        pk = item.pk
        self.client.post(reverse('booking:delete', args=[pk]))
        self.assertFalse(Reservation.objects.filter(pk=pk).exists())
        self.assertTrue(ReservationEvent.objects.filter(reservation_number=pk, reservation=None, action='Удалена').exists())

    def test_filter_and_privacy(self):
        mine = self.item()
        self.item(equipment=self.second)
        self.item(user=self.other)
        response = self.client.get(reverse('booking:list'), {'equipment':self.equipment.pk})
        self.assertEqual(list(response.context['items']), [mine])

    def test_filter_date(self):
        self.item()
        response = self.client.get(reverse('booking:list'), {'date':timezone.localtime(self.start).date().isoformat()})
        self.assertEqual(len(response.context['items']), 1)

    def test_bad_filter_is_form_error(self):
        response = self.client.get(reverse('booking:list'), {'date':'nonsense'})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['filter_form'].errors)

    def test_inactive_equipment(self):
        self.equipment.is_active = False
        self.equipment.save()
        response = self.client.post(reverse('booking:create'), self.data())
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Reservation.objects.exists())
        item = Reservation(user=self.user, equipment=self.equipment, start=self.start, end=self.end, purpose='X')
        with self.assertRaises(ValidationError):
            item.full_clean()

    def test_model_validation(self):
        self.item()
        candidate = Reservation(user=self.user, equipment=self.equipment, start=self.start, end=self.end, purpose='X')
        with self.assertRaises(ValidationError):
            candidate.full_clean()

    def test_relogin_preserves_data(self):
        item = self.item()
        self.client.logout()
        self.client.force_login(self.user)
        response = self.client.get(reverse('booking:list'))
        self.assertEqual(list(response.context['items']), [item])

    def test_anonymous_redirected(self):
        self.client.logout()
        for name in ('list', 'create', 'history', 'export', 'availability'):
            self.assertEqual(self.client.get(reverse('booking:'+name)).status_code, 302)

    def test_availability(self):
        self.item()
        response = self.client.get(reverse('booking:availability'), {'start':self.data()['start'], 'end':self.data()['end']})
        self.assertEqual(list(response.context['devices']), [self.second])

    def test_csv_private_and_formula_safe(self):
        self.item(purpose='=1+1')
        self.item(user=self.other, purpose='SECRET_OTHER')
        response = self.client.get(reverse('booking:export'))
        self.assertContains(response, "'=1+1")
        self.assertNotContains(response, 'SECRET_OTHER')

    def test_history_is_private(self):
        mine = self.item()
        theirs = self.item(user=self.other)
        for item in (mine, theirs):
            ReservationEvent.objects.create(reservation=item, reservation_number=item.pk, user=item.user, action='Создана')
        response = self.client.get(reverse('booking:history'))
        self.assertEqual(response.context['events'].count(), 1)

    def test_tickets_removed_and_navigation(self):
        for url in ('/tickets/', '/api/tickets/', '/api/categories/'):
            self.assertEqual(self.client.get(url).status_code, 404)
        self.assertNotContains(self.client.get(reverse('booking:list')), 'Заявки')

    def test_old_bookmark_redirects(self):
        self.assertRedirects(self.client.get('/reservations/'), reverse('booking:list'))
