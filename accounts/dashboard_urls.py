from django.urls import path
from . import dashboard_views

urlpatterns = [
    path('dashboard/', dashboard_views.dashboard_page, {'section': 'overview'}, name='dashboard_overview'),
    path('dashboard/departments/', dashboard_views.dashboard_page, {'section': 'departments'}, name='dashboard_departments'),
    path('dashboard/groups/', dashboard_views.dashboard_page, {'section': 'groups'}, name='dashboard_groups'),
    path('api/dashboard/', dashboard_views.dashboard_api, name='dashboard_api'),

]
