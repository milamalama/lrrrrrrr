from django.urls import path
from . import views

app_name = 'booking'
urlpatterns = [
    path('', views.reservation_list, name='list'),
    path('new/', views.reservation_form, name='create'),
    path('<int:pk>/edit/', views.reservation_form, name='edit'),
    path('<int:pk>/cancel/', views.reservation_cancel, name='cancel'),
    path('<int:pk>/delete/', views.reservation_delete, name='delete'),
    path('availability/', views.availability, name='availability'),
    path('history/', views.history, name='history'),
    path('export/', views.export_csv, name='export'),
]
