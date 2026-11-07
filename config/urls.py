from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
)

urlpatterns = [
    path('booking/', include('booking.urls')),
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),
    path('', include('accounts.urls')),
    path("", include("reservations.urls")),
    path('', RedirectView.as_view(url='/accounts/login/', permanent=False)),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema',),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui',),
]