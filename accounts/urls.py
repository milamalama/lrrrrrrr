from django.urls import path, include
from . import views

urlpatterns = [
    path('profile/', views.profile, name='profile'),

    path('departments/', views.department_list, name='department_list'),
    path('departments/add/', views.department_create, name='department_create'),
    path('departments/<int:pk>/edit/', views.department_update, name='department_update'),
    path('departments/<int:pk>/delete/', views.department_delete, name='department_delete'),

    path('groups/', views.academic_group_list, name='academic_group_list'),
    path('groups/add/', views.academic_group_create, name='academic_group_create'),
    path('groups/<int:pk>/edit/', views.academic_group_update, name='academic_group_update'),
    path('groups/<int:pk>/delete/', views.academic_group_delete, name='academic_group_delete'),

    path('courses/', views.course_list, name='course_list'),
    path('courses/add/', views.course_create, name='course_create'),
    path('courses/<int:pk>/edit/', views.course_update, name='course_update'),
    path('courses/<int:pk>/delete/', views.course_delete, name='course_delete'),
]
from .dashboard_urls import urlpatterns as dashboard_patterns

urlpatterns += dashboard_patterns