from decimal import Decimal

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import HttpResponseForbidden

from .forms import (
    ProducerRegistrationForm,
    CustomerRegistrationForm,
    LoginForm,
    ProductForm,
)

from .models import User, Product, CartItem, Order, OrderItem


# =========================
# REGISTRATION
# =========================

def register_producer_view(request):
    if request.method == "POST":
        form = ProducerRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_producer = True
            user.save()

            messages.success(
                request,
                f"Welcome {user.business_name}! Account created successfully. You can now log in using your email and password."
            )
            return redirect("login")
    else:
        form = ProducerRegistrationForm()

    return render(request, "register_producer.html", {"form": form})


def register_customer_view(request):
    if request.method == "POST":
        form = CustomerRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_customer = True
            user.save()
            messages.success(request, "Customer account created successfully! You can now log in.")
            return redirect("login")
    else:
        form = CustomerRegistrationForm()

    return render(request, "register_customer.html", {"form": form})


# =========================
# AUTH
# =========================

def login_view(request):
    if request.method == "POST":
        form = LoginForm(request.POST)

        if form.is_valid():
            entered_email = form.cleaned_data["username"].strip()
            password = form.cleaned_data["password"]

            user_obj = User.objects.filter(email__iexact=entered_email).first()
            user = None

            if user_obj:
                user = authenticate(
                    request,
                    username=user_obj.username,
                    password=password
                )

            if user is not None:
                login(request, user)

                if not form.cleaned_data.get("remember_me"):
                    request.session.set_expiry(0)

                if getattr(user, "is_producer", False):
                    return redirect("producer_products")
                return redirect("marketplace")
            else:
                messages.error(request, "Invalid email or password.")
    else:
        form = LoginForm()

    return render(request, "login.html", {"form": form})


def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect("login")


# =========================
# MARKETPLACE
# =========================

def marketplace_view(request):
    products = Product.objects.filter(
        availability__in=["in_season", "year_round"],
        stock__gt=0
    ).order_by("-id")

    return render(request, "marketplace.html", {"products": products})


def product_detail_view(request, pk):
    product = get_object_or_404(Product, pk=pk)
    return render(request, "product_detail.html", {"product": product})


# =========================
# CART
# =========================

@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if product.stock <= 0:
        messages.error(request, f"{product.name} is out of stock.")
        return redirect("marketplace")

    cart_item, created = CartItem.objects.get_or_create(
        customer=request.user,
        product=product
    )

    if not created:
        if cart_item.quantity + 1 > product.stock:
            messages.error(request, "Cannot add more than stock.")
            return redirect("marketplace")

        cart_item.quantity += 1
        cart_item.save()

    messages.success(request, "Product added to cart.")
    return redirect("marketplace")


@login_required
def cart_view(request):
    items = CartItem.objects.filter(customer=request.user)
    total = sum(item.subtotal() for item in items)

    return render(request, "cart.html", {
        "items": items,
        "total": total,
    })


@login_required
def update_cart_item(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, customer=request.user)

    if request.method == "POST":
        quantity = int(request.POST.get("quantity"))

        if quantity > cart_item.product.stock:
            messages.error(request, "Not enough stock.")
            return redirect("cart")

        if quantity > 0:
            cart_item.quantity = quantity
            cart_item.save()
        else:
            cart_item.delete()

    return redirect("cart")


@login_required
def remove_cart_item(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, customer=request.user)
    cart_item.delete()
    return redirect("cart")


# =========================
# CHECKOUT
# =========================

@login_required
def checkout_view(request):
    items = CartItem.objects.filter(
        customer=request.user
    ).select_related("product", "product__producer")

    if not items.exists():
        messages.error(request, "Your cart is empty.")
        return redirect("cart")

    producer_map = {}
    for item in items:
        producer_map.setdefault(item.product.producer, []).append(item)

    grouped_items = []
    for producer, producer_items in producer_map.items():
        subtotal = sum(item.subtotal() for item in producer_items)
        commission = (subtotal * Decimal("0.05")).quantize(Decimal("0.01"))
        payout = (subtotal * Decimal("0.95")).quantize(Decimal("0.01"))

        grouped_items.append({
            "producer": producer,
            "items": producer_items,
            "subtotal": subtotal,
            "commission": commission,
            "payout": payout,
        })

    total_amount = sum(group["subtotal"] for group in grouped_items)

    if request.method == "POST":
        items = CartItem.objects.filter(
            customer=request.user
        ).select_related("product", "product__producer")

        producer_map = {}
        for item in items:
            producer_map.setdefault(item.product.producer, []).append(item)

        created_orders = []

        for producer, producer_items in producer_map.items():
            delivery_address = request.POST.get(f"address_{producer.id}")
            delivery_date = request.POST.get(f"date_{producer.id}")

            if not delivery_address or not delivery_date:
                messages.error(request, f"Missing delivery info for producer {producer.business_name or producer.username}.")
                return redirect("checkout")

            subtotal = sum(item.subtotal() for item in producer_items)
            commission = (subtotal * Decimal("0.05")).quantize(Decimal("0.01"))
            payout = (subtotal * Decimal("0.95")).quantize(Decimal("0.01"))

            for item in producer_items:
                if item.quantity > item.product.stock:
                    messages.error(request, f"Not enough stock for {item.product.name}.")
                    return redirect("cart")

            order = Order.objects.create(
                customer=request.user,
                producer=producer,
                delivery_address=delivery_address,
                delivery_date=delivery_date,
                status="pending",
                subtotal=subtotal,
                commission_amount=commission,
                producer_amount=payout,
                total_amount=subtotal,
            )

            created_orders.append(order)

            for item in producer_items:
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    quantity=item.quantity,
                    unit_price=item.product.price,
                    subtotal=item.subtotal(),
                )

                item.product.stock -= item.quantity
                item.product.save()

        items.delete()

        request.session["latest_order_ids"] = [order.id for order in created_orders]
        messages.success(request, f"{len(created_orders)} order(s) created successfully.")

        return redirect("order_success")

    return render(request, "checkout.html", {
        "grouped_items": grouped_items,
        "total_amount": total_amount,
    })


# =========================
# ORDER SUCCESS
# =========================

@login_required
def order_success_view(request):
    order_ids = request.session.get("latest_order_ids", [])

    orders = Order.objects.filter(
        customer=request.user,
        id__in=order_ids
    ).order_by("-id")

    return render(request, "order_success.html", {
        "orders": orders
    })


# =========================
# ORDERS PAGE
# =========================

@login_required
def orders_view(request):
    orders = Order.objects.filter(customer=request.user).order_by("-id")
    return render(request, "orders.html", {"orders": orders})


# =========================
# PRODUCER
# =========================

@login_required
def producer_products_view(request):
    if not request.user.is_producer:
        return HttpResponseForbidden()

    products = Product.objects.filter(producer=request.user)
    return render(request, "producer_products.html", {"products": products})


@login_required
def producer_add_product_view(request):
    if not request.user.is_producer:
        return HttpResponseForbidden()

    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            product.producer = request.user
            product.save()
            messages.success(request, "Product added successfully.")
            return redirect("producer_products")
    else:
        form = ProductForm()

    return render(request, "producer_add_product.html", {"form": form})


@login_required
def producer_edit_product_view(request, pk):
    if not request.user.is_producer:
        return HttpResponseForbidden()

    product = get_object_or_404(Product, pk=pk)

    if product.producer != request.user:
        return HttpResponseForbidden()

    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, "Product updated successfully.")
            return redirect("producer_products")
    else:
        form = ProductForm(instance=product)

    return render(request, "producer_edit_product.html", {"form": form})


@login_required
@require_POST
def producer_delete_product_view(request, pk):
    if not request.user.is_producer:
        return HttpResponseForbidden()

    product = get_object_or_404(Product, pk=pk)

    if product.producer != request.user:
        return HttpResponseForbidden()

    product.delete()
    messages.success(request, "Product deleted successfully.")
    return redirect("producer_products")