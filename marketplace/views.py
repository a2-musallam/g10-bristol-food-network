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
    CheckoutForm,
)

from .models import Product, CartItem, Order, OrderItem


# =========================
# REGISTRATION
# =========================

def register_producer_view(request):
    if request.method == 'POST':
        form = ProducerRegistrationForm(request.POST)

        if form.is_valid():
            user = form.save(commit=False)
            user.is_producer = True
            user.save()

            messages.success(request, f"Welcome {user.business_name}! Account created.")
            return redirect('login')
    else:
        form = ProducerRegistrationForm()

    return render(request, 'register_producer.html', {'form': form})


def register_customer_view(request):
    if request.method == 'POST':
        form = CustomerRegistrationForm(request.POST)

        if form.is_valid():
            user = form.save(commit=False)
            user.is_customer = True
            user.save()

            messages.success(request, "Customer account created successfully!")
            return redirect('login')
    else:
        form = CustomerRegistrationForm()

    return render(request, 'register_customer.html', {'form': form})


# =========================
# AUTHENTICATION
# =========================

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)

        if form.is_valid():
            user = authenticate(
                username=form.cleaned_data['username'],
                password=form.cleaned_data['password']
            )

            if user:
                login(request, user)

                if not form.cleaned_data.get("remember_me"):
                    request.session.set_expiry(0)

                if getattr(user, "is_producer", False):
                    return redirect("producer_products")
                else:
                    return redirect("marketplace")
            else:
                messages.error(request, "Invalid username or password.")
    else:
        form = LoginForm()

    return render(request, 'login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('login')


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
# TC-006 SHOPPING CART
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
            messages.error(request, f"Cannot add more than available stock for {product.name}.")
            return redirect("marketplace")

        cart_item.quantity += 1
        cart_item.save()

    messages.success(request, "Product added to cart")
    return redirect("marketplace")


@login_required
def cart_view(request):
    items = CartItem.objects.filter(customer=request.user)
    total = sum(item.subtotal() for item in items)

    producer = None
    if items.exists():
        producer = items.first().product.producer

    return render(request, "cart.html", {
        "items": items,
        "total": total,
        "producer": producer,
    })


@login_required
def update_cart_item(request, item_id):
    cart_item = get_object_or_404(
        CartItem,
        id=item_id,
        customer=request.user
    )

    if request.method == "POST":
        quantity = request.POST.get("quantity")

        if quantity:
            quantity = int(quantity)

            if quantity > cart_item.product.stock:
                messages.error(
                    request,
                    f"Only {cart_item.product.stock} item(s) available for {cart_item.product.name}."
                )
                return redirect("cart")

            if quantity > 0:
                cart_item.quantity = quantity
                cart_item.save()
                messages.success(request, "Cart updated successfully.")
            else:
                cart_item.delete()
                messages.info(request, "Item removed from cart.")

    return redirect("cart")


@login_required
def remove_cart_item(request, item_id):
    cart_item = get_object_or_404(
        CartItem,
        id=item_id,
        customer=request.user
    )

    cart_item.delete()
    messages.success(request, "Item removed from cart")
    return redirect("cart")


# =========================
# TC-007 CHECKOUT
# =========================

@login_required
def checkout_view(request):
    items = CartItem.objects.filter(customer=request.user)

    if not items.exists():
        messages.error(request, "Your cart is empty.")
        return redirect("cart")

    producers = set(item.product.producer for item in items)

    if len(producers) > 1:
        messages.error(request, "You can only place an order from a single producer.")
        return redirect("cart")

    producer = items.first().product.producer
    subtotal = sum(item.subtotal() for item in items)
    commission_amount = (subtotal * Decimal("0.05")).quantize(Decimal("0.01"))
    producer_amount = (subtotal * Decimal("0.95")).quantize(Decimal("0.01"))
    total_amount = subtotal

    if request.method == "POST":
        form = CheckoutForm(request.POST)

        if form.is_valid():
            for item in items:
                if item.quantity > item.product.stock:
                    messages.error(
                        request,
                        f"Not enough stock for {item.product.name}. Available stock: {item.product.stock}."
                    )
                    return redirect("cart")

            order = Order.objects.create(
                customer=request.user,
                producer=producer,
                delivery_address=form.cleaned_data["delivery_address"],
                delivery_date=form.cleaned_data["delivery_date"],
                status="pending",
                subtotal=subtotal,
                commission_amount=commission_amount,
                producer_amount=producer_amount,
                total_amount=total_amount,
            )

            for item in items:
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    quantity=item.quantity,
                    unit_price=item.product.price,
                    subtotal=item.subtotal(),
                )

                product = item.product
                product.stock -= item.quantity
                product.save()

            items.delete()

            messages.success(request, f"Order #{order.id} created successfully.")
            return redirect("order_success", order_id=order.id)
    else:
        initial_data = {
            "delivery_address": request.user.address or "",
        }
        form = CheckoutForm(initial=initial_data)

    return render(request, "checkout.html", {
        "form": form,
        "items": items,
        "producer": producer,
        "subtotal": subtotal,
        "commission_amount": commission_amount,
        "producer_amount": producer_amount,
        "total_amount": total_amount,
    })


@login_required
def order_success_view(request, order_id):
    order = get_object_or_404(Order, id=order_id, customer=request.user)

    return render(request, "order_success.html", {
        "order": order
    })


# =========================
# PRODUCER PRODUCT LOGIC
# =========================

@login_required
def producer_products_view(request):
    if not request.user.is_producer:
        return HttpResponseForbidden("Access denied. Only producers can access this page.")

    products = Product.objects.filter(producer=request.user).order_by("-id")
    return render(request, "producer_products.html", {"products": products})


@login_required
def producer_add_product_view(request):
    if not request.user.is_producer:
        return HttpResponseForbidden("Access denied. Only producers can add products.")

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
        return HttpResponseForbidden("Access denied. Only producers can edit products.")

    product = get_object_or_404(Product, pk=pk)

    if product.producer != request.user:
        return HttpResponseForbidden("Access denied. You cannot edit another producer's product.")

    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES, instance=product)

        if form.is_valid():
            form.save()
            messages.success(request, "Product updated successfully.")
            return redirect("producer_products")
    else:
        form = ProductForm(instance=product)

    return render(request, "producer_edit_product.html", {
        "form": form,
        "product": product
    })


@login_required
@require_POST
def producer_delete_product_view(request, pk):
    if not request.user.is_producer:
        return HttpResponseForbidden("Access denied. Only producers can delete products.")

    product = get_object_or_404(Product, pk=pk)

    if product.producer != request.user:
        return HttpResponseForbidden("Access denied. You cannot delete another producer's product.")

    product.delete()
    messages.success(request, "Product deleted successfully.")
    return redirect("producer_products")