# backend/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('upload_url', views.upload_url, name='upload_url'),
    path('api/finance-chat', views.finance_chat, name='finance_chat'),
    
]
