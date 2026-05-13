"""
URL Configuration for USDA Inspection System.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.urls import re_path
from django.views.static import serve

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('inspections.urls')),
    path('api/batch-description/', include('inspections.batch_description_urls')),
]

# Servir archivos media tanto en desarrollo como en producción (Render)
urlpatterns += [
    re_path(r'^media/(?P<path>.*)$', serve, {
        'document_root': settings.MEDIA_ROOT,
    }),
]
