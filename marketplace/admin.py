from django.contrib import admin
from .models import User, Product, Order

# Define how User model appears in the admin area
@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    # Fixed: Removed 'postcode' and added 'address' to match the new model
    list_display = ('username', 'email', 'is_producer', 'is_customer', 'address')
    list_filter = ('is_producer', 'is_customer')
    
    # Adding fieldsets so you can edit the new fields inside the user profile
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Bristol Food Network Roles', {'fields': ('is_producer', 'is_customer', 'business_name')}),
        ('Contact Info', {'fields': ('phone', 'address')}), # Address and Phone are here
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )

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