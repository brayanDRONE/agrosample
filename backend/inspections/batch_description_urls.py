"""
batch_description_urls.py - URLs para el módulo de planilla de descripción
"""

from django.urls import path
from . import batch_description_views

urlpatterns = [
    path('parse-ins/', batch_description_views.parse_ins_file, name='parse-ins'),
    path('generate/', batch_description_views.generate_batch_description, name='generate-batch'),
    path('export/', batch_description_views.export_batch_description, name='export-batch'),
    path('save-batch/', batch_description_views.save_batch_description, name='save-batch'),
]
