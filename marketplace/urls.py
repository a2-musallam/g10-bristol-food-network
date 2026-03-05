from django.urls import path
from . import views

urlpatterns = [

    # Marketplace
    path("", views.marketplace_view, name="marketplace"),
    path("products/<int:pk>/", views.product_detail_view, name="product_detail"),

    # Authentication
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),

    # Registration
    path("register/producer/", views.register_producer_view, name="register_producer"),
    path("register/customer/", views.register_customer_view, name="register_customer"),

    # Producer product management (TC-003)
    path("producer/products/", views.producer_products_view, name="producer_products"),
    path("producer/products/add/", views.producer_add_product_view, name="producer_add_product"),
    path("producer/products/edit/<int:pk>/", views.producer_edit_product_view, name="producer_edit_product"),
    path("producer/products/delete/<int:pk>/", views.producer_delete_product_view, name="producer_delete_product"),
]