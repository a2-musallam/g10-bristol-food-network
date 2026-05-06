import csv
from collections import OrderedDict
from datetime import datetime, timedelta
from decimal import Decimal
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.contrib import messages
from django.http import HttpResponse, HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST
from .models import RecurringOrder, RecurringOrderItem, FoodMiles
from .forms import (
    RestaurantRegistrationForm,
    ProducerRegistrationForm,
    CustomerRegistrationForm,
    CheckoutForm,
    ReviewForm,
    CommunityGroupRegistrationForm,
    RecipeForm,
    ProductForm,
    LoginForm,
    FarmStoryForm,
)
from .models import (
    CartItem,
    Notification,
    Order,
    OrderItem,
    Product,
    Review,
    User,
    Recipe,
    FarmStory,
)
import stripe
from django.conf import settings
from django.shortcuts import redirect
from .models import CartItem
from .models import FarmStory

@login_required
@login_required
def notifications_view(request):
    notifications = request.user.notifications.all()

    return render(request, "notifications.html", {
        "notifications": notifications
    })

@login_required
def update_recurring_item(request, item_id):
    item = get_object_or_404(RecurringOrderItem, id=item_id)

    if item.recurring_order.user != request.user:
        return HttpResponseForbidden()

    if request.method == "POST":
        try:
            quantity = int(request.POST.get("quantity", 1))
        except ValueError:
            messages.error(request, "Invalid quantity.")
            return redirect("recurring_orders")

        # Quantity must be positive
        if quantity <= 0:
            messages.error(request, "Quantity must be at least 1.")
            return redirect("recurring_orders")

        # Product availability check
        if item.product.availability == "unavailable":
            messages.error(request, f"{item.product.name} is currently unavailable.")
            return redirect("recurring_orders")

        # Stock check (critical)
        if quantity > item.product.stock:
            messages.error(
                request,
                f"Not enough stock for {item.product.name}. Available: {item.product.stock}"
            )
            return redirect("recurring_orders")

        item.quantity = quantity
        item.save()

        messages.success(request, "Recurring item updated successfully.")

    return redirect("recurring_orders")

@login_required
def modify_next_order(request, order_id):
    recurring = get_object_or_404(RecurringOrder, id=order_id, user=request.user)

    if request.method == "POST":
        new_date = request.POST.get("next_date")

        if new_date:
            recurring.next_order_date = new_date
            recurring.save()

    return redirect("recurring_orders")

@login_required
def cancel_recurring_order(request, order_id):
    order = get_object_or_404(RecurringOrder, id=order_id, user=request.user)
    order.is_active = False
    order.save()
    return redirect("recurring_orders")


@login_required
def pause_recurring_order(request, order_id):
    order = get_object_or_404(RecurringOrder, id=order_id, user=request.user)
    order.is_active = False
    order.save()
    return redirect("recurring_orders")


@login_required
def resume_recurring_order(request, order_id):
    order = get_object_or_404(RecurringOrder, id=order_id, user=request.user)
    order.is_active = True
    order.save()
    return redirect("recurring_orders")

@login_required
def recurring_orders_view(request):
    if not request.user.is_restaurant:
        return HttpResponseForbidden()

    recurring_orders = RecurringOrder.objects.filter(user=request.user)

    #  AUTO GENERATE + NOTIFICATION
    for recurring in recurring_orders:
        if recurring.is_active and recurring.next_order_date:
            
            
            if recurring.next_order_date <= timezone.now().date():
                
                
                new_orders = recurring.generate_next_order()

                #  notification
                messages.success(
                    request,
                    f"Recurring order '{recurring.name}' has been processed automatically."
                )

    return render(request, "recurring_orders.html", {
        "recurring_orders": recurring_orders
    })

def register_restaurant_view(request):
    if request.method == "POST":
        form = RestaurantRegistrationForm(request.POST)

        if form.is_valid():
            form.save()
            messages.success(request, "Restaurant account created successfully.")
            return redirect("login")
    else:
        form = RestaurantRegistrationForm()

    return render(request, "register_restaurant.html", {"form": form})

@login_required
def create_farm_story_view(request):
    if not request.user.is_producer:
        return HttpResponseForbidden()

    if request.method == "POST":
        form = FarmStoryForm(request.POST, request.FILES)
        if form.is_valid():
            story = form.save(commit=False)
            story.producer = request.user
            story.save()
            return redirect("farm_stories")
    else:
        form = FarmStoryForm()

    return render(request, "create_farm_story.html", {
        "form": form
    })
def farm_stories_view(request):
    stories = FarmStory.objects.select_related("producer").order_by("-created_at")

    return render(request, "farm_stories.html", {
        "stories": stories
    })
@login_required
def edit_farm_story_view(request, pk):
    story = get_object_or_404(FarmStory, pk=pk)

    if story.producer != request.user:
        return HttpResponseForbidden()

    if request.method == "POST":
        form = FarmStoryForm(request.POST, request.FILES, instance=story)
        if form.is_valid():
            form.save()
            return redirect("farm_stories")
    else:
        form = FarmStoryForm(instance=story)

    return render(request, "create_farm_story.html", {
        "form": form
    })
@login_required
def delete_farm_story_view(request, pk):
    story = get_object_or_404(FarmStory, pk=pk)

    if story.producer != request.user:
        return HttpResponseForbidden()

    story.delete()
    return redirect("farm_stories")

stripe.api_key = settings.STRIPE_SECRET_KEY

@login_required

@login_required
def create_checkout_session(request):
    import stripe
    from decimal import Decimal
    stripe.api_key = settings.STRIPE_SECRET_KEY

    checkout_data = request.session.get("checkout_data")

    if not checkout_data:
        return redirect("cart")

    line_items = []
    subtotal = Decimal("0.00")

    
    for group in checkout_data["groups"]:
        producer_id = group["producer_id"]

        items = CartItem.objects.filter(
            customer=request.user,
            product__producer_id=producer_id
        ).select_related("product")

        for item in items:
            item_total = item.product.price * item.quantity
            subtotal += item_total

            line_items.append({
                "price_data": {
                    "currency": "gbp",
                    "product_data": {
                        "name": item.product.name,
                    },
                    "unit_amount": int(item.product.price * 100),  
                },
                "quantity": item.quantity,
            })

    
    discount_amount = Decimal("0.00")

    if (
        request.user.is_community_group
        and request.user.bulk_discount_rate > 0
        and subtotal >= Decimal("100.00")
    ):
        discount_amount = (
            subtotal * request.user.bulk_discount_rate / Decimal("100")
        ).quantize(Decimal("0.01"))

    session_data = {
        "payment_method_types": ["card"],
        "line_items": line_items,
        "mode": "payment",
        "success_url": "http://127.0.0.1:8000/order-success/",
        "cancel_url": "http://127.0.0.1:8000/checkout/",
    }

    
    if discount_amount > 0:
        coupon = stripe.Coupon.create(
            amount_off=int(discount_amount * 100),
            currency="gbp",
            duration="once",
            name="Community Discount",
        )

        session_data["discounts"] = [
            {"coupon": coupon.id}
        ]

    session = stripe.checkout.Session.create(**session_data)

    return redirect(session.url)


def register_community_group_view(request):
    if request.method == "POST":
        form = CommunityGroupRegistrationForm(request.POST)

        if form.is_valid():
            form.save()
            messages.success(
                request,
                "Community group account created successfully."
            )
            return redirect("login")
    else:
        form = CommunityGroupRegistrationForm()

    return render(
        request,
        "register_community_group.html",
        {"form": form}
    )

def check_low_stock(product):
    if product.stock <= product.low_stock_threshold:
        notification, created = Notification.objects.get_or_create(
            user=product.producer,
            product=product,
            is_read=False,
            defaults={
                "message": f"Low Stock Alert: {product.name} - Only {product.stock} remaining"
            }
        )

        if not created:
            notification.message = f"Low Stock Alert: {product.name} - Only {product.stock} remaining"
            notification.is_read = False
            notification.save()
    else:
        Notification.objects.filter(
            user=product.producer,
            product=product
        ).delete()



def can_review_product(user, product):
    if not user.is_authenticated or not getattr(user, "is_customer", False):
        return False

    return OrderItem.objects.filter(
        order__customer=user,
        order__status="delivered",
        product=product
    ).exists()


def has_existing_review(user, product):
    if not user.is_authenticated:
        return False

    return Review.objects.filter(customer=user, product=product).exists()


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
            messages.success(
                request,
                "Customer account created successfully! You can now log in."
            )
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

            messages.error(request, "Invalid email or password.")
    else:
        form = LoginForm()

    return render(request, "login.html", {"form": form})


def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect("login")


def _marketplace_products_queryset():
    products = (
        Product.objects.select_related("producer")
        .exclude(availability="unavailable")
    )

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

    # 🔔 NOTIFICATION COUNT
    unread_notifications_count = 0
    if request.user.is_authenticated:
        unread_notifications_count = request.user.notifications.filter(
            is_read=False
        ).count()

    return render(request, "marketplace.html", {
        "products": products,
        "selected_category": category,
        "search_query": query,
        "categories": Product.CATEGORY_CHOICES,
        "unread_notifications_count": unread_notifications_count,  #  IMPORTANT
    })


def product_detail_view(request, pk):
    product = get_object_or_404(Product.objects.select_related("producer"), pk=pk)
    reviews = product.reviews.select_related("customer").all()

    user_can_review = can_review_product(request.user, product)
    already_reviewed = has_existing_review(request.user, product)
    
    # Calculate food miles if user has postcode
    food_miles = None
    within_radius = False
    
    if request.user.is_authenticated and request.user.postcode:
        food_miles = product.get_food_miles(request.user.postcode)
        if food_miles:
            km_limit = Decimal("32.19")  # 20 miles
            within_radius = food_miles <= km_limit

    return render(request, "product_detail.html", {
        "product": product,
        "reviews": reviews,
        "user_can_review": user_can_review,
        "already_reviewed": already_reviewed,
        "food_miles_km": food_miles,
        "within_radius": within_radius,
        "food_miles_miles": float(food_miles) / 1.60934 if food_miles else None,
    })


@login_required
def product_food_miles_api(request, product_id):
    """API endpoint to get food miles for a product."""
    product = get_object_or_404(Product, id=product_id)
    customer_postcode = request.GET.get("postcode", "").strip()
    
    if not customer_postcode:
        return JsonResponse({"error": "Postcode required"}, status=400)
    
    food_miles = product.get_food_miles(customer_postcode)
    
    if food_miles is None:
        return JsonResponse({
            "error": "Could not calculate food miles - producer coordinates missing"
        }, status=400)
    
    km_limit = Decimal("32.19")  # 20 miles
    within_radius = food_miles <= km_limit
    miles = float(food_miles) / 1.60934  # km to miles
    
    return JsonResponse({
        "product_id": product_id,
        "product_name": product.name,
        "distance_km": float(food_miles),
        "distance_miles": round(miles, 1),
        "within_20_mile_radius": within_radius,
        "producer_name": product.producer.business_name or product.producer.username,
    })


@login_required
def add_review_view(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if not request.user.is_customer:
        messages.error(request, "Only customers can submit reviews.")
        return redirect("product_detail", pk=product.id)

    if not can_review_product(request.user, product):
        messages.error(request, "You can only review products from delivered orders.")
        return redirect("product_detail", pk=product.id)

    if has_existing_review(request.user, product):
        messages.error(request, "You have already reviewed this product.")
        return redirect("product_detail", pk=product.id)

    if request.method == "POST":
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.product = product
            review.customer = request.user
            review.save()
            messages.success(request, "Review submitted successfully.")
            return redirect("product_detail", pk=product.id)
    else:
        form = ReviewForm()

    return render(request, "add_review.html", {
        "form": form,
        "product": product,
    })


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
    items = CartItem.objects.filter(customer=request.user).select_related(
        "product",
        "product__producer"
    )
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
def order_success_view(request):
    from .utils import create_food_miles_record, calculate_total_food_miles
    
    checkout_data = request.session.get("checkout_data")

    if not checkout_data:
        return render(request, "order_success.html", {
            "orders": []
        })

    created_orders = []

    for group in checkout_data.get("groups", []):
        producer = User.objects.get(id=group["producer_id"])

        items = CartItem.objects.filter(
            customer=request.user,
            product__producer=producer
        ).select_related("product")

        if not items.exists():
            continue

        subtotal = sum(item.subtotal() for item in items)
        discount = Decimal("0.00")

        if (
            request.user.is_community_group
            and request.user.bulk_discount_rate > 0
            and subtotal >= Decimal("100.00")
        ):
            discount = (
                subtotal * request.user.bulk_discount_rate / Decimal("100")
            ).quantize(Decimal("0.01"))

        total = (subtotal - discount).quantize(Decimal("0.01"))

        delivery_date = timezone.make_aware(
            timezone.datetime.fromisoformat(group["date"])
        )

        order = Order.objects.create(
            customer=request.user,
            producer=producer,
            delivery_address=group["address"],
            delivery_date=delivery_date,
            status="pending",
            subtotal=subtotal,
            discount_amount=discount,
            total_amount=total,
        )

        for item in items:
            OrderItem.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity,
                unit_price=item.product.price,
                subtotal=item.subtotal(),
            )

            item.product.stock -= item.quantity
            item.product.save()
            
            # Create food miles record for each product in order
            create_food_miles_record(item.product, request.user, request.user.postcode, order)
        
        # Calculate and store total food miles for order
        total_miles = calculate_total_food_miles(items, request.user.postcode)
        order.total_food_miles = total_miles
        order.save()

        created_orders.append(order)

    # TC-018 recurring order logic
    if request.user.is_restaurant and checkout_data.get("make_recurring"):
        recurring_order = RecurringOrder.objects.create(
            user=request.user,
            name="Weekly Restaurant Order",
            frequency="weekly",
            order_day=checkout_data.get("order_day", "Monday"),
            delivery_day=checkout_data.get("delivery_day", "Wednesday"),
            next_order_date=timezone.now().date() + timedelta(days=7),
        )

        all_items = CartItem.objects.filter(
            customer=request.user
        ).select_related("product")

        for cart_item in all_items:
            RecurringOrderItem.objects.create(
                recurring_order=recurring_order,
                product=cart_item.product,
                quantity=cart_item.quantity,
            )

        for order in created_orders:
            order.recurring_order = recurring_order
            order.save()

        # Optional demo logic: advance next scheduled date
        recurring_order.generate_next_order()

    CartItem.objects.filter(customer=request.user).delete()
    request.session.pop("checkout_data", None)

    return render(request, "order_success.html", {
        "orders": created_orders
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
    unread_notifications_count = Notification.objects.filter(
        user=request.user,
        is_read=False
    ).count()

    return render(request, "producer_products.html", {
        "products": products,
        "unread_notifications_count": unread_notifications_count,
    })


@login_required
def producer_notifications_view(request):
    if not request.user.is_producer:
        return HttpResponseForbidden()

    notifications = (
        Notification.objects
        .filter(user=request.user)
        .select_related("product")
        .order_by("-created_at")
    )

    return render(request, "producer_notifications.html", {
        "notifications": notifications
    })


@login_required
@require_POST
def mark_notification_read_view(request, notification_id):
    if not request.user.is_producer:
        return HttpResponseForbidden()

    notification = get_object_or_404(
        Notification,
        id=notification_id,
        user=request.user
    )
    notification.is_read = True
    notification.save()

    return redirect("producer_notifications")


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

    if request.method == "POST":
        new_status = request.POST.get("status", "").strip()
        status_note = request.POST.get("status_note", "").strip()

        order.status = new_status
        order.status_note = status_note
        order.save()

        messages.success(request, f"Order #{order.id} updated to {order.get_status_display()}.")
        return redirect("producer_orders")

    return render(request, "producer_update_order_status.html", {
        "order": order,
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
            check_low_stock(product)
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
            product = form.save()
            check_low_stock(product)
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
        subtotal = sum(item.product.price * item.quantity for item in producer_items)
        discount = Decimal("0.00")

        if (
            request.user.is_community_group
            and request.user.bulk_discount_rate > 0
            and subtotal >= Decimal("100.00")
        ):
            discount = subtotal * request.user.bulk_discount_rate / Decimal("100")

        total = subtotal - discount

        grouped_items.append({
            "producer": producer,
            "items": producer_items,
            "subtotal": subtotal,
            "discount": discount,
            "total": total,
            "minimum_date": (
                timezone.now() + timezone.timedelta(hours=48)
            ).strftime("%Y-%m-%dT%H:%M"),
        })

    total_amount = sum(group["total"] for group in grouped_items)

    if request.method == "POST":
        checkout_data = {
            "groups": [],
            "total": float(total_amount),

            # TC-018 recurring order data
            "make_recurring": bool(request.POST.get("make_recurring")),
            "order_day": request.POST.get("order_day", "Monday"),
            "delivery_day": request.POST.get("delivery_day", "Wednesday"),
        }

        for producer, producer_items in producer_map.items():
            address = request.POST.get(f"address_{producer.id}")
            date_value = request.POST.get(f"date_{producer.id}")

            if not address or not date_value:
                messages.error(request, "Fill all delivery fields.")
                return redirect("checkout")

            checkout_data["groups"].append({
                "producer_id": producer.id,
                "address": address,
                "date": date_value,
                "discount_rate": float(request.user.bulk_discount_rate),
                "items": [
                    {
                        "name": item.product.name,
                        "price": float(item.product.price),
                        "quantity": item.quantity,
                    }
                    for item in producer_items
                ],
            })

        request.session["checkout_data"] = checkout_data
        return redirect("create_checkout_session")

    return render(request, "checkout.html", {
        "grouped_items": grouped_items,
        "total_amount": total_amount,
    })


@login_required
def producer_order_detail_view(request, order_id):
    if not request.user.is_producer:
        return HttpResponseForbidden()

    order = get_object_or_404(
        Order.objects.select_related("customer").prefetch_related("items__product"),
        id=order_id,
        producer=request.user
    )

    return render(request, "producer_order_detail.html", {
        "order": order
    })


@login_required
def producer_finances_view(request):
    if not request.user.is_producer:
        return HttpResponseForbidden()

    delivered_orders = Order.objects.filter(
        producer=request.user,
        status="delivered"
    ).order_by("-updated_at")

    weekly_data = OrderedDict()
    ytd_total = Decimal("0.00")
    current_year = timezone.now().year

    for order in delivered_orders:
        if order.updated_at.year == current_year:
            ytd_total += order.producer_amount

        week_start = order.updated_at.date() - timedelta(days=order.updated_at.date().weekday())
        week_str = week_start.strftime("%Y-%m-%d")

        if week_str not in weekly_data:
            days_since_start = (timezone.now().date() - week_start).days
            status = "Processed" if days_since_start > 7 else "Pending Bank Transfer"

            weekly_data[week_str] = {
                "week_start": week_start,
                "status": status,
                "total_orders_value": Decimal("0.00"),
                "commission": Decimal("0.00"),
                "payout": Decimal("0.00"),
                "orders": []
            }

        weekly_data[week_str]["total_orders_value"] += order.total_amount
        weekly_data[week_str]["commission"] += order.commission_amount
        weekly_data[week_str]["payout"] += order.producer_amount
        weekly_data[week_str]["orders"].append(order)

    if request.GET.get("download_csv"):
        week = request.GET.get("week")

        try:
            week_date = datetime.strptime(week, "%Y-%m-%d")
            filename_date = f"{week_date.day}-{week_date.month}-{week_date.year}"
        except (ValueError, TypeError):
            filename_date = week

        response = HttpResponse(content_type="text/csv; charset=utf-8")
        response["Content-Disposition"] = f'attachment; filename="settlement_report_{filename_date}.csv"'
        response.write("\ufeff")

        writer = csv.writer(response)
        writer.writerow([
            "Order Number",
            "Customer Name",
            "Items Sold",
            "Date",
            "Total Amount",
            "Commission",
            "Payout"
        ])

        if week in weekly_data:
            for o in weekly_data[week]["orders"]:
                items_sold = ", ".join(
                    [f"{item.product.name} (x{item.quantity})" for item in o.items.all()]
                )
                writer.writerow([
                    o.id,
                    o.customer.get_full_name() or o.customer.username,
                    items_sold,
                    f"{o.updated_at.day}/{o.updated_at.month}/{o.updated_at.year}",
                    f"£{o.total_amount}",
                    f"£{o.commission_amount}",
                    f"£{o.producer_amount}"
                ])
        return response

    return render(request, "producer_finances.html", {
        "weekly_data": weekly_data.values(),
        "ytd_total": ytd_total,
        "current_year": current_year
    })


@login_required
def create_recipe_view(request):
    if not request.user.is_producer:
        return redirect("marketplace")

    if request.method == "POST":
        form = RecipeForm(request.POST, request.FILES)

        if form.is_valid():
            recipe = form.save(commit=False)
            recipe.producer = request.user
            recipe.save()
            form.save_m2m()
            return redirect("producer_products")
    else:
        form = RecipeForm()

    return render(request, "recipe_form.html", {
        "form": form
    })


def recipe_detail_view(request, recipe_id):
    recipe = get_object_or_404(Recipe, id=recipe_id)
    return render(request, "recipe_detail.html", {"recipe": recipe})


@login_required
def producer_dashboard_view(request):
    if not request.user.is_producer:
        return redirect("marketplace")

    return render(request, "producer_dashboard.html")
