import secrets
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from booking.models import Equipment

class Command(BaseCommand):
    help = 'Создать три устройства и двух обычных пользователей. Существующие пароли не меняются.'

    def handle(self, *args, **options):
        for number, name in [('LR-001', 'Ноутбук'), ('LR-002', 'Проектор'), ('LR-003', 'Камера')]:
            Equipment.objects.get_or_create(inventory_number=number, defaults={'name': name})
        for username in ('student1', 'student2'):
            user, created = get_user_model().objects.get_or_create(username=username)
            if created:
                password = secrets.token_urlsafe(12)
                user.set_password(password)
                user.save()
                self.stdout.write(f'{username}: {password}')
            else:
                self.stdout.write(f'{username}: уже существует, пароль сохранён')
