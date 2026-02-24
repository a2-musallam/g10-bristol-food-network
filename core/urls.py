from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from marketplace.views import ProductViewSet, OrderViewSet, UserViewSet

router = DefaultRouter()
router.register(r'products', ProductViewSet)
router.register(r'orders', OrderViewSet)
router.register(r'users', UserViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)), # All API endpoints start with /api/
]
