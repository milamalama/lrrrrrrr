from django.contrib.auth.models import User
from django.db import models

from django.conf import settings

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class Ticket(models.Model):
    class Status(models.TextChoices):
        NEW = "new", "Новая"
        PROGRESS = "progress", "В работе"
        DONE = "done", "Выполнена"

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)

    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="tickets"
    )

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="tickets"
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.NEW
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class Department(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Course(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    department = models.ForeignKey(
        Department, on_delete=models.CASCADE, related_name='courses'
    )

    def __str__(self):
        return self.title


class AcademicGroup(models.Model):
    name = models.CharField(max_length=50)
    department = models.ForeignKey(
        Department, on_delete=models.CASCADE, related_name='groups'
    )

    def __str__(self):
        return self.name


class StudentProfile(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='student_profile'
    )
    department = models.ForeignKey(
        Department, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='students'
    )
    academic_group = models.ForeignKey(
        AcademicGroup, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='students'
    )
    courses = models.ManyToManyField(
        Course, blank=True, related_name='students'
    )

    def __str__(self):
        return self.user.username