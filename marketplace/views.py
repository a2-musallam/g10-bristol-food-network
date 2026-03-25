from decimal import Decimal

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import CustomerRegistrationForm, LoginForm, ProductForm, ProducerRegistrationForm
from .models import CartItem, Order, OrderItem, Product, User


def register_producer_view(request):
    if request.method == "POST":
        form = ProducerRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_producer = True
            user.save()
            messages.success(
                request,
                f"Welcome {user.business_name}! Account created successfully. You can now log in using your email and password.",
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


def login_view(request):
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            entered_email = form.cleaned_data["username"].strip()
            password = form.cleaned_data["password"]
            user_obj = User.objects.filter(email__iexact=entered_email).first()
            user = None

            if user_obj:
                user = authenticate(request, username=user_obj.username, password=password)

            if user is not None:
                login(request, user)

                if not form.cleaned_data.get("remember_me"):
                    request.session.set_expiry(0)

                if getattr(user, "is_producer", False):
                    return redirect("producer_products")
                return redirect("marketplace")

            messages.error(request, "Invalid email or password.")
    else:
        form = LoginForm()

    return render(request, "login.html", {"form": form})


def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect("login")


def _marketplace_products_queryset():
    products = Product.objects.select_related("producer").filter(stock__gt=0).exclude(availability="unavailable")
    current_month = timezone.now().month

    visible_ids = [
        product.id
        for product in products
        if product.is_currently_in_season(current_month)
    ]

    return Product.objects.select_related("producer").filter(id__in=visible_ids).order_by("-id")


def marketplace_view(request):
    products = _marketplace_products_queryset()

    category = request.GET.get("category", "").strip()
    query = request.GET.get("q", "").strip()

    if category:
        products = products.filter(category=category)

    if query:
        products = products.filter(
            Q(name__icontains=query)
            | Q(description__icontains=query)
            | Q(producer__business_name__icontains=query)
            | Q(producer__username__icontains=query)
        )

    return render(request, "marketplace.html", {
        "products": products,
        "selected_category": category,
        "search_query": query,
        "categories": Product.CATEGORY_CHOICES,
    })


def product_detail_view(request, pk):
    product = get_object_or_404(Product.objects.select_related("producer"), pk=pk)
    return render(request, "product_detail.html", {"product": product})


@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if product.stock <= 0 or not product.is_currently_in_season():
        messages.error(request, f"{product.name} is currently unavailable.")
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
    items = CartItem.objects.filter(customer=request.user).select_related("product", "product__producer")
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
            "minimum_date": (timezone.now() + timezone.timedelta(hours=48)).strftime("%Y-%m-%dT%H:%M"),
        })

    total_amount = sum(group["subtotal"] for group in grouped_items)

    if request.method == "POST":
        created_orders = []

        for producer, producer_items in producer_map.items():
            delivery_address = request.POST.get(f"address_{producer.id}")
            delivery_date_raw = request.POST.get(f"date_{producer.id}")

            if not delivery_address or not delivery_date_raw:
                messages.error(request, f"Missing delivery info for producer {producer.business_name or producer.username}.")
                return redirect("checkout")

            delivery_date = timezone.datetime.fromisoformat(delivery_date_raw)
            if timezone.is_naive(delivery_date):
                delivery_date = timezone.make_aware(delivery_date, timezone.get_current_timezone())

            if delivery_date <= timezone.now() + timezone.timedelta(hours=48):
                messages.error(request, "Delivery date must be at least 48 hours from now.")
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


@login_required
def orders_view(request):
    producer_filter = request.GET.get("producer", "").strip()

    orders = (
        Order.objects.filter(customer=request.user)
        .select_related("producer")
        .prefetch_related("items__product")
        .order_by("-created_at")
    )

    if producer_filter:
        orders = orders.filter(producer__id=producer_filter)

    producers = (
        User.objects.filter(
            id__in=Order.objects.filter(customer=request.user).values_list("producer_id", flat=True)
        )
        .distinct()
        .order_by("business_name", "username")
    )

    return render(request, "orders.html", {
        "orders": orders,
        "producers": producers,
        "selected_producer": producer_filter,
    })


@login_required
def reorder_view(request, order_id):
    order = get_object_or_404(
        Order.objects.prefetch_related("items__product"),
        id=order_id,
        customer=request.user
    )

    added = 0
    skipped = []

    for item in order.items.all():
        product = item.product

        if product.stock <= 0 or not product.is_currently_in_season():
            skipped.append(product.name)
            continue

        cart_item, created = CartItem.objects.get_or_create(
            customer=request.user,
            product=product
        )

        desired_qty = cart_item.quantity + item.quantity if not created else item.quantity

        if desired_qty > product.stock:
            skipped.append(f"{product.name} (not enough stock)")
            continue

        cart_item.quantity = desired_qty
        cart_item.save()
        added += 1

    if added:
        messages.success(request, "Available items from that order were added to your cart.")
    if skipped:
        messages.warning(request, "Some items could not be reordered: " + ", ".join(skipped))

    return redirect("cart")


@login_required
def producer_products_view(request):
    if not request.user.is_producer:
        return HttpResponseForbidden()

    products = Product.objects.filter(producer=request.user)
    return render(request, "producer_products.html", {"products": products})


@login_required
def producer_orders_view(request):
    if not request.user.is_producer:
        return HttpResponseForbidden()

    status = request.GET.get("status", "").strip()

    orders = (
        Order.objects.filter(producer=request.user)
        .select_related("customer")
        .prefetch_related("items__product")
        .order_by("delivery_date", "-created_at")
    )

    if status:
        orders = orders.filter(status=status)

    return render(request, "producer_orders.html", {
        "orders": orders,
        "selected_status": status,
        "status_choices": Order.STATUS_CHOICES,
    })


@login_required
def producer_update_order_status_view(request, order_id):
    if not request.user.is_producer:
        return HttpResponseForbidden()

    order = get_object_or_404(Order, id=order_id, producer=request.user)
    allowed_statuses = order.next_allowed_statuses()

    if request.method == "POST":
        new_status = request.POST.get("status", "").strip()
        status_note = request.POST.get("status_note", "").strip()

        if new_status not in allowed_statuses:
            messages.error(request, "That status change is not allowed.")
            return redirect("producer_orders")

        order.status = new_status
        order.status_note = status_note
        order.save()

        messages.success(request, f"Order #{order.id} updated to {order.get_status_display()}.")
        return redirect("producer_orders")

    return render(request, "producer_update_order_status.html", {
        "order": order,
        "allowed_statuses": allowed_statuses,
    })


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