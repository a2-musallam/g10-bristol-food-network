from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST

from .forms import (
    ProducerRegistrationForm,
    CustomerRegistrationForm,
    LoginForm,
    ProductForm,
)

from .models import Product



# REGISTRATION

def register_producer_view(request):
    """ TC-001: Producer Registration """
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
    """ TC-002: Customer Registration """
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


# AUTHENTICATION (TC-022)


def login_view(request):
    """ TC-022: Secure Login """
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            user = authenticate(
                username=form.cleaned_data['username'],
                password=form.cleaned_data['password']
            )
            if user:
                login(request, user)

                # Redirect based on role instead of admin
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


# MARKETPLACE (Customer View)

def marketplace_view(request):
    # Only show products that are available AND in stock (recommended for TC-003)
    products = Product.objects.filter(
        availability__in=["in_season", "year_round"],
        stock__gt=0
    ).order_by("-id")

    return render(request, "marketplace.html", {"products": products})


def product_detail_view(request, pk):
    """ TC-015: Product detail page with allergen display """
    product = get_object_or_404(Product, pk=pk)
    return render(request, "product_detail.html", {"product": product})



# TC-003 PRODUCER PRODUCT LOGIC

@login_required
def producer_products_view(request):
    """ Producer product dashboard """
    if not getattr(request.user, "is_producer", False):
        messages.error(request, "Only producers can access this page.")
        return redirect("login")

    products = Product.objects.filter(producer=request.user).order_by("-id")
    return render(request, "producer_products.html", {"products": products})


@login_required
def producer_add_product_view(request):
    """ Producer adds product """
    if not getattr(request.user, "is_producer", False):
        messages.error(request, "Only producers can add products.")
        return redirect("login")

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
    """ Producer edits own product """
    if not getattr(request.user, "is_producer", False):
        messages.error(request, "Only producers can edit products.")
        return redirect("login")

    product = get_object_or_404(Product, pk=pk, producer=request.user)

    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, "Product updated successfully.")
            return redirect("producer_products")
    else:
        form = ProductForm(instance=product)

    return render(request, "producer_edit_product.html", {"form": form, "product": product})


@login_required
@require_POST
def producer_delete_product_view(request, pk):
    """ Producer deletes own product """
    if not getattr(request.user, "is_producer", False):
        messages.error(request, "Only producers can delete products.")
        return redirect("login")

    product = get_object_or_404(Product, pk=pk, producer=request.user)
    product.delete()
    messages.success(request, "Product deleted successfully.")
    return redirect("producer_products")