from django.urls import path
from . import views # This looks for views.py inside the marketplace folder

urlpatterns = [
    # TC-001: Producer Registration (Jane Smith / Bristol Valley Farm)
    path('register/producer/', views.register_producer_view, name='register_producer'),
    
    # TC-002: Customer Registration (Robert Johnson)
    path('register/customer/', views.register_customer_view, name='register_customer'),
    
    # TC-022: Secure Login System
    path('login/', views.login_view, name='login'),
    
    # Logout System
    path('logout/', views.logout_view, name='logout'),
    
    # TC-003 Producer Product Management
    path('producer/products/', views.producer_products_view, name='producer_products'),
    path('producer/products/add/', views.producer_add_product_view, name='producer_add_product'),
]