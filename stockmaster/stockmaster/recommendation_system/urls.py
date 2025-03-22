from django.urls import path
from .views import recommend_investment_plan

urlpatterns = [
    path('recommend/', recommend_investment_plan, name='recommend_investment_plan'),
]
