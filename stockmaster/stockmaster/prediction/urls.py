# prediction/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('predict-spends/', views.predict_next_week_spends, name='predict_next_week_spends'),
]
