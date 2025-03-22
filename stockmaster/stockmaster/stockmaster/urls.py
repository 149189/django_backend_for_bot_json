# stockmaster/urls.py

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('backend.urls')),
       path('api/', include('prediction.urls')),
       path('api/', include('api.urls')),
       path('api/', include('recommendation_system.urls')),
          # Include the backend app URLs
]
