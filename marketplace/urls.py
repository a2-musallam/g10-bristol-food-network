from django.urls import path
from . import views
from .views import notifications_view
urlpatterns = [
    path("", views.marketplace_view, name="marketplace"),
    path("register/restaurant/", views.register_restaurant_view, name="register_restaurant"),
    path("notifications/", notifications_view, name="notifications"),
    path("recurring/modify/<int:order_id>/", views.modify_next_order, name="modify_recurring"),
    path("recurring/update-item/<int:item_id>/", views.update_recurring_item, name="update_recurring_item"),
    path("recurring/cancel/<int:order_id>/", views.cancel_recurring_order, name="cancel_recurring"),
    path("recurring/pause/<int:order_id>/", views.pause_recurring_order, name="pause_recurring"),
    path("recurring/resume/<int:order_id>/", views.resume_recurring_order, name="resume_recurring"),
    path("recurring-orders/", views.recurring_orders_view, name="recurring_orders"),
    path("products/<int:pk>/", views.product_detail_view, name="product_detail"),
    path("products/<int:product_id>/review/", views.add_review_view, name="add_review"),
    path("producer/dashboard/", views.producer_dashboard_view, name="producer_dashboard"),
    path("producer/farm-stories/edit/<int:pk>/", views.edit_farm_story_view, name="edit_farm_story"),
    path("producer/farm-stories/delete/<int:pk>/", views.delete_farm_story_view, name="delete_farm_story"),
    path("cart/", views.cart_view, name="cart"),
    path("cart/add/<int:product_id>/", views.add_to_cart, name="add_to_cart"),
    path("cart/update/<int:item_id>/", views.update_cart_item, name="update_cart"),
    path("cart/remove/<int:item_id>/", views.remove_cart_item, name="remove_cart"),
    path("checkout/", views.checkout_view, name="checkout"),
    path("create-checkout-session/", views.create_checkout_session, name="create_checkout_session"),
    path("farm-stories/", views.farm_stories_view, name="farm_stories"),
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
    path("producer/orders/<int:order_id>/advance/", views.producer_advance_order_status, name="producer_advance_order"),

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

    # Food Miles Feature
    path("api/product/<int:product_id>/food-miles/", views.product_food_miles_api, name="product_food_miles_api"),

    #TC-019 (Surplus Produce/Discounts) and TC-025 (Network Commission)
    path("producer/products/<int:pk>/surplus/", views.producer_mark_surplus_view, name="producer_mark_surplus"),
    path("surplus-deals/", views.surplus_deals_view, name="surplus_deals"),
    path("network-commission/", views.admin_commission_report_view, name="admin_commission_report"),
]
