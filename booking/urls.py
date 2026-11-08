from django.urls import path
from . import views

urlpatterns = [
    path(
        "",
        views.reservation_list,
        name="reservation_list"
    ),
    path(
        "new/",
        views.reservation_create,
        name="reservation_create"
    ),
    path(
        "<int:pk>/edit/",
        views.reservation_edit,
        name="reservation_edit"
    ),
    path(
        "<int:pk>/delete/",
        views.reservation_delete,
        name="reservation_delete"
    ),
    path(
        "<int:pk>/cancel/",
        views.reservation_cancel,
        name="reservation_cancel"
    ),
]
