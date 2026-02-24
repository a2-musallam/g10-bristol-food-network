from django.contrib import admin
from .models import User, Product, Order

# Define how User model appears in the admin area
@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    # Display these fields in the user list view
    list_display = ('username', 'email', 'is_producer', 'is_customer', 'postcode')
    list_filter = ('is_producer', 'is_customer')

# Define how Products appear (TC-004 requirement)
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'producer', 'price', 'stock')
    search_fields = ('name',)

# Define how Orders and Commissions appear (TC-016 requirement)
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    # We display 'network_commission' which is a property defined in models.py
    list_display = ('id', 'customer', 'total_amount', 'network_commission', 'created_at')