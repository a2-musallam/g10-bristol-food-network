from rest_framework import viewsets
from .models import Product, Order, User
from .serializers import ProductSerializer, OrderSerializer, UserSerializer

# API endpoint for Users
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

# API endpoint for Products
class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

# API endpoint for Orders
class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
