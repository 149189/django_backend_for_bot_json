from django.urls import path
from . import views

urlpatterns = [

    
    # Financial Insights (with prediction/anomaly integration)
    path('financial-insight/', views.financial_insight, name='financial_insight'),
    
    
]