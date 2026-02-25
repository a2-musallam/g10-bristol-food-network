from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    # This line connects your marketplace app to the project
    path('', include('marketplace.urls')), 
]