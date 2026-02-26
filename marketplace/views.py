from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout # Added logout here
from .forms import ProducerRegistrationForm, CustomerRegistrationForm, LoginForm

def register_producer_view(request):
    """ TC-001: Producer Registration Logic. """
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
    """ TC-002: Customer Registration Logic. """
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

def login_view(request):
    """ TC-022: Secure Login Logic. """
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            user = authenticate(
                username=form.cleaned_data['username'], 
                password=form.cleaned_data['password']
            )
            if user:
                login(request, user)
                return redirect('admin:index') 
            else:
                messages.error(request, "Invalid username or password.")
    return render(request, 'login.html', {'form': LoginForm()})

def logout_view(request):
    """ The missing function that was causing your error! """
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('login')

# TC-003 Producer Products

@login_required
def producer_products_view(request):
    """TC-003: Producer product listing (only shows logged-in producer's products)."""
    if not getattr(request.user, "is_producer", False):
        messages.error(request, "Only producers can access this page.")
        return redirect("login")

    products = Product.objects.filter(producer=request.user).order_by("-id")
    return render(request, "producer_products.html", {"products": products})


@login_required
def producer_add_product_view(request):
    """TC-003: Producer adds a product (product is linked to logged-in producer)."""
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