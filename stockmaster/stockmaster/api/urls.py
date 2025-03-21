from django.urls import path
from .views import financial_query

urlpatterns = [
    path('financial_query/', financial_query, name='financial_query'),
]
