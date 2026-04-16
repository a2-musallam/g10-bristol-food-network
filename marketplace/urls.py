from django.urls import path
from . import views

urlpatterns = [
    path("", views.marketplace_view, name="marketplace"),
    path("products/<int:pk>/", views.product_detail_view, name="product_detail"),
    path("products/<int:product_id>/review/", views.add_review_view, name="add_review"),

    path("producer/dashboard/", views.producer_dashboard_view, name="producer_dashboard"),

    path("cart/", views.cart_view, name="cart"),
    path("cart/add/<int:product_id>/", views.add_to_cart, name="add_to_cart"),
    path("cart/update/<int:item_id>/", views.update_cart_item, name="update_cart"),
    path("cart/remove/<int:item_id>/", views.remove_cart_item, name="remove_cart"),

    path("checkout/", views.checkout_view, name="checkout"),
    path("order-success/", views.order_success_view, name="order_success"),
    path("orders/", views.orders_view, name="orders"),
    path("orders/<int:order_id>/reorder/", views.reorder_view, name="reorder"),

    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),

    path("register/producer/", views.register_producer_view, name="register_producer"),
    path("register/customer/", views.register_customer_view, name="register_customer"),
    path("register/community-group/", views.register_community_group_view, name="register_community_group"),

    path("producer/products/", views.producer_products_view, name="producer_products"),
    path("producer/products/add/", views.producer_add_product_view, name="producer_add_product"),
    path("producer/products/edit/<int:pk>/", views.producer_edit_product_view, name="producer_edit_product"),
    path("producer/products/delete/<int:pk>/", views.producer_delete_product_view, name="producer_delete_product"),

    path("producer/orders/", views.producer_orders_view, name="producer_orders"),
    path("producer/orders/<int:order_id>/", views.producer_order_detail_view, name="producer_order_detail"),
    path("producer/orders/<int:order_id>/status/", views.producer_update_order_status_view, name="producer_update_order_status"),

    path("producer/recipes/new/", views.create_recipe_view, name="create_recipe"),
    path("producer/farm-stories/new/", views.create_farm_story_view, name="create_farm_story"),
    path("recipes/<int:recipe_id>/", views.recipe_detail_view, name="recipe_detail"),

    path("producer/finances/", views.producer_finances_view, name="producer_finances"),

    # Sprint 3
    path("producer/notifications/", views.producer_notifications_view, name="producer_notifications"),
    path(
        "producer/notifications/<int:notification_id>/read/",
        views.mark_notification_read_view,
        name="mark_notification_read",
    ),
]