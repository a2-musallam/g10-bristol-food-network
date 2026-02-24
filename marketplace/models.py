from django.db import models
from django.contrib.auth.models import AbstractUser

# Custom User for Bristol Food Network roles
class User(AbstractUser):
    is_producer = models.BooleanField(default=False)
    is_customer = models.BooleanField(default=False)
    postcode = models.CharField(max_length=10, blank=True)

# Product model for TC-004
class Product(models.Model):
    producer = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'is_producer': True})
    name = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField(default=0)

# Order and 5% Commission for TC-016
class Order(models.Model):
    customer = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'is_customer': True})
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def network_commission(self):
        return float(self.total_amount) * 0.05