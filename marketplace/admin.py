from django.contrib import admin
from .models import User, Product, Order, CartItem, OrderItem


# User admin
@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = (
        "username",
        "email",
        "is_producer",
        "is_customer",
        "is_restaurant",
        "is_community_group",
        "address",
    )

    list_filter = (
        "is_producer",
        "is_customer",
        "is_restaurant",
        "is_community_group",
    )

    fieldsets = (
        (None, {"fields": ("username", "password")}),

        ("Personal info", {
            "fields": ("first_name", "last_name", "email")
        }),

        ("Permissions", {
            "fields": (
                "is_active",
                "is_staff",
                "is_superuser",
                "groups",
                "user_permissions",
            )
        }),

        ("Bristol Food Network Roles", {
            "fields": (
                "is_producer",
                "is_customer",
                "is_restaurant",
                "is_community_group",
                "business_name",
            )
        }),

        ("Contact Info", {
            "fields": ("phone", "address")
        }),

        ("Important dates", {
            "fields": ("last_login", "date_joined")
        }),
    )


# Product admin
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "producer",
        "category",
        "price",
        "unit",
        "availability",
        "stock",
    )
    search_fields = ("name", "producer__username", "producer__business_name")
    list_filter = ("category", "availability")


# Order admin
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "customer",
        "producer",
        "subtotal",
        "commission_amount",
        "producer_amount",
        "total_amount",
        "status",
        "delivery_date",
        "created_at",
    )
    search_fields = ("customer__username", "producer__username", "producer__business_name")
    list_filter = ("status", "created_at")


# Cart admin
@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ("customer", "product", "quantity")


# OrderItem admin
@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ("order", "product", "quantity", "unit_price", "subtotal")