from django.contrib import admin
from .models import User, Product, Order


# Define how User model appears in the admin area
@admin.register(User)
class UserAdmin(admin.ModelAdmin):

    # show roles in user list
    list_display = (
        'username',
        'email',
        'is_producer',
        'is_customer',
        'is_restaurant',
        'is_community_group',
        'address'
    )

    # filters in sidebar
    list_filter = (
        'is_producer',
        'is_customer',
        'is_restaurant',
        'is_community_group'
    )

    # edit user fields
    fieldsets = (
        (None, {'fields': ('username', 'password')}),

        ('Personal info', {
            'fields': ('first_name', 'last_name', 'email')
        }),

        ('Permissions', {
            'fields': (
                'is_active',
                'is_staff',
                'is_superuser',
                'groups',
                'user_permissions'
            )
        }),

        ('Bristol Food Network Roles', {
            'fields': (
                'is_producer',
                'is_customer',
                'is_restaurant',
                'is_community_group',
                'business_name'
            )
        }),

        ('Contact Info', {
            'fields': ('phone', 'address')
        }),

        ('Important dates', {
            'fields': ('last_login', 'date_joined')
        }),
    )


# Define how Products appear (TC-004 requirement)
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'producer', 'price', 'stock')
    search_fields = ('name',)


# Define how Orders and Commissions appear (TC-016 requirement)
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer', 'total_amount', 'network_commission', 'created_at')