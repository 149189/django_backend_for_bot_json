# anomalies/urls.py

from django.urls import path
from .views import detect_anomalies

urlpatterns = [
    path('detect-anomalies/', detect_anomalies, name='detect_anomalies'),
]
