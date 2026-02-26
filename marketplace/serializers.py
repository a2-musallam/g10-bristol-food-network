from rest_framework import serializers
from .models import Product, Order, User

# Serializer for User model
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'is_producer', 'is_customer']

# Serializer for Product model
class ProductSerializer(serializers.ModelSerializer):
    allergen_warning = serializers.SerializerMethodField()
    class Meta:
        model = Product
        fields = '__all__'
        
    def get_allergen_warning(self, obj):
        if obj.allergens:
            return f"⚠ Contains: {obj.allergens}"
        return "No allergens declared"

# Serializer for Order model
class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = '__all__'
        read_only_fields = ['network_commission'] # Commission is calculated on server side
