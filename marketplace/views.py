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

from .models import Product, CartItem


# =========================
# REGISTRATION
# =========================

def register_producer_view(request):

    if request.method == 'POST':
        form = ProducerRegistrationForm(request.POST)

        if form.is_valid():
            user = form.save(commit=False)
            user.is_producer = True
            user.set_password(form.cleaned_data['password'])
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
            user.set_password(form.cleaned_data['password'])
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

    cart_item, created = CartItem.objects.get_or_create(
        customer=request.user,
        product=product
    )

    if not created:
        cart_item.quantity += 1
        cart_item.save()

    messages.success(request, "Product added to cart")

    return redirect("marketplace")


@login_required
def cart_view(request):

    items = CartItem.objects.filter(customer=request.user)

    total = sum(item.subtotal() for item in items)

    return render(request, "cart.html", {
        "items": items,
        "total": total
    })


# ⭐ NEW: UPDATE CART ITEM
@login_required
def update_cart_item(request, item_id):

    cart_item = get_object_or_404(
        CartItem,
        id=item_id,
        customer=request.user
    )

    if request.method == "POST":

        quantity = int(request.POST.get("quantity"))

        if quantity > 0:
            cart_item.quantity = quantity
            cart_item.save()

    return redirect("cart")


# ⭐ NEW: REMOVE CART ITEM
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