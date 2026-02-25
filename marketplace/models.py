from django.db import models
from django.contrib.auth.models import AbstractUser

# Custom User for Bristol Food Network roles
class User(AbstractUser):
    """
    Extending User model to meet TC-001 and TC-002 requirements.
    Username will be labeled as 'Contact Name' in the form.
    """
    is_producer = models.BooleanField(default=False)
    is_customer = models.BooleanField(default=False)
    
    # Generic fields for both roles
    phone = models.CharField(max_length=15, blank=True, null=True)
    
    # Merged field for Address and Postcode (Requirement change)
    address = models.TextField(blank=True, null=True)

    # TC-001: Producer Specific Fields
    business_name = models.CharField(max_length=255, blank=True, null=True)

    # TC-002: Customer Specific Fields
    # Note: Using the shared 'address' field above for delivery as well 
    # to keep the database clean and simple.

# Product model for TC-003 & TC-004
class Product(models.Model):
    # Linking the product to a specific Producer
    producer = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'is_producer': True})
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField(default=0)
    image = models.ImageField(upload_to='products/', blank=True, null=True)

# Order and 5% Commission for TC-016
class Order(models.Model):
    # Linking the order to a specific Customer
    customer = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'is_customer': True})
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def network_commission(self):
        # Calculate the 5% network fee for TC-016
        return float(self.total_amount) * 0.05