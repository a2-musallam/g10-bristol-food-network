from decimal import Decimal
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models import Avg


class User(AbstractUser):
    is_producer = models.BooleanField(default=False)
    is_customer = models.BooleanField(default=False)
    is_restaurant = models.BooleanField(default=False)
    is_community_group = models.BooleanField(default=False)

    phone = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    business_name = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.username


class Product(models.Model):
    CATEGORY_CHOICES = [
        ("veg", "Vegetables"),
        ("dairy_eggs", "Dairy & Eggs"),
        ("bakery", "Bakery"),
        ("preserves", "Preserves"),
        ("seasonal", "Seasonal Specialties"),
    ]

    AVAILABILITY_CHOICES = [
        ("in_season", "In Season (Available)"),
        ("year_round", "Available Year-Round"),
        ("unavailable", "Unavailable / Out of Season"),
    ]

    MONTH_CHOICES = [
        (1, "January"),
        (2, "February"),
        (3, "March"),
        (4, "April"),
        (5, "May"),
        (6, "June"),
        (7, "July"),
        (8, "August"),
        (9, "September"),
        (10, "October"),
        (11, "November"),
        (12, "December"),
    ]

    producer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        limit_choices_to={"is_producer": True},
    )

    name = models.CharField(max_length=200)
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES, default="veg")
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    unit = models.CharField(max_length=50, default="Each")

    availability = models.CharField(
        max_length=20,
        choices=AVAILABILITY_CHOICES,
        default="in_season"
    )

    stock = models.IntegerField(default=0)
    low_stock_threshold = models.PositiveIntegerField(default=5)

    harvest_date = models.DateField(blank=True, null=True)
    image = models.ImageField(upload_to="products/", blank=True, null=True)
    allergens = models.CharField(max_length=255, blank=True, null=True)

    seasonal_start_month = models.PositiveSmallIntegerField(
        choices=MONTH_CHOICES,
        blank=True,
        null=True
    )
    seasonal_end_month = models.PositiveSmallIntegerField(
        choices=MONTH_CHOICES,
        blank=True,
        null=True
    )

    def __str__(self):
        return self.name

    def season_label(self):
        if self.seasonal_start_month and self.seasonal_end_month:
            start = dict(self.MONTH_CHOICES).get(self.seasonal_start_month)
            end = dict(self.MONTH_CHOICES).get(self.seasonal_end_month)
            return f"{start} - {end}"
        return ""

    def is_currently_in_season(self, month=None):
        if self.availability == "year_round":
            return True
        if self.availability == "unavailable":
            return False
        if not self.seasonal_start_month or not self.seasonal_end_month:
            return True

        if month is None:
            from django.utils import timezone
            month = timezone.now().month

        if self.seasonal_start_month <= self.seasonal_end_month:
            return self.seasonal_start_month <= month <= self.seasonal_end_month

        return month >= self.seasonal_start_month or month <= self.seasonal_end_month

    def average_rating(self):
        result = self.reviews.aggregate(avg=Avg("rating"))
        return result["avg"] or 0

    def review_count(self):
        return self.reviews.count()


class Order(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("confirmed", "Confirmed"),
        ("ready", "Ready for Collection / Delivery"),
        ("delivered", "Delivered"),
        ("cancelled", "Cancelled"),
    ]

    customer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="customer_orders",
        limit_choices_to={"is_customer": True}
    )

    producer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="producer_orders",
        limit_choices_to={"is_producer": True},
        blank=True,
        null=True
    )

    delivery_address = models.TextField(blank=True, null=True)
    delivery_date = models.DateTimeField(blank=True, null=True)
    special_instructions = models.TextField(blank=True, null=True)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending"
    )
    status_note = models.CharField(max_length=255, blank=True, null=True)

    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    commission_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    producer_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def calculate_commission(self):
        return (self.subtotal * Decimal("0.05")).quantize(Decimal("0.01"))

    def calculate_producer_amount(self):
        return (self.subtotal * Decimal("0.95")).quantize(Decimal("0.01"))

    def next_allowed_statuses(self):
        flow = {
            "pending": ["confirmed", "cancelled"],
            "confirmed": ["ready", "cancelled"],
            "ready": ["delivered"],
            "delivered": [],
            "cancelled": [],
        }
        return flow.get(self.status, [])

    def __str__(self):
        return f"Order #{self.id} - {self.customer.username}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)

    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"Order #{self.order.id} - {self.product.name} x {self.quantity}"


class CartItem(models.Model):
    customer = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)

    def subtotal(self):
        return self.product.price * self.quantity

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"


class Notification(models.Model):
    producer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="notifications",
        limit_choices_to={"is_producer": True},
    )
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="notifications")
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.product.name} - {self.message}"


class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="reviews")
    customer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="reviews",
        limit_choices_to={"is_customer": True},
    )
    rating = models.PositiveSmallIntegerField()
    title = models.CharField(max_length=255)
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("product", "customer")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.product.name} - {self.rating} stars"