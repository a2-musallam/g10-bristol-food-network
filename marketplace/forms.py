from django import forms
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.utils import timezone

from .models import User, Product


# =========================
# TC-001: Producer Registration Form
# =========================
class ProducerRegistrationForm(forms.ModelForm):
    contact_name = forms.CharField(
        label="Full Name",
        widget=forms.TextInput(attrs={"placeholder": "e.g. Jane Smith"})
    )
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ["business_name", "email", "phone", "address"]

        labels = {
            "address": "Business Address and Postcode",
        }

        widgets = {
            "address": forms.Textarea(attrs={
                "rows": 3,
                "placeholder": "Enter full business address and postcode here..."
            }),
        }

    def clean_password(self):
        password = self.cleaned_data.get("password")
        try:
            validate_password(password)
        except ValidationError as e:
            raise forms.ValidationError(e.messages)
        return password

    def clean(self):
        cleaned_data = super().clean()

        if cleaned_data.get("password") != cleaned_data.get("confirm_password"):
            raise forms.ValidationError("Passwords do not match!")

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        contact_name = self.cleaned_data.get("contact_name", "").strip()

        names = contact_name.split(" ", 1)
        user.first_name = names[0] if len(names) > 0 else ""
        user.last_name = names[1] if len(names) > 1 else ""

        # Generate username from full name for internal auth
        base_username = contact_name.replace(" ", "_").lower()
        username = base_username
        counter = 1

        while User.objects.filter(username=username).exists():
            username = f"{base_username}_{counter}"
            counter += 1

        user.username = username
        user.set_password(self.cleaned_data["password"])

        if commit:
            user.save()

        return user


# =========================
# TC-002: Customer Registration Form
# =========================
class CustomerRegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ["first_name", "last_name", "username", "email", "phone", "address", "password"]

        labels = {
            "username": "Login Username (No spaces)",
            "address": "Delivery Address and Postcode",
        }

        widgets = {
            "address": forms.Textarea(attrs={
                "rows": 3,
                "placeholder": "Enter your delivery address and postcode..."
            }),
        }

    def clean_password(self):
        password = self.cleaned_data.get("password")
        try:
            validate_password(password)
        except ValidationError as e:
            raise forms.ValidationError(e.messages)
        return password

    def clean(self):
        cleaned_data = super().clean()

        if cleaned_data.get("password") != cleaned_data.get("confirm_password"):
            raise forms.ValidationError("Passwords do not match!")

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])

        if commit:
            user.save()

        return user


# =========================
# TC-022: Login Form
# =========================
class LoginForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        label="Email Address"
    )

    password = forms.CharField(
        widget=forms.PasswordInput
    )

    remember_me = forms.BooleanField(
        required=False,
        label="Remember Me"
    )


# =========================
# TC-003: Product Form
# =========================
class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            "name",
            "category",
            "description",
            "price",
            "unit",
            "availability",
            "stock",
            "harvest_date",
            "image",
            "allergens",
        ]

        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
            "allergens": forms.TextInput(attrs={
                "placeholder": "e.g. Contains: Milk, Eggs, Wheat (Gluten)"
            }),
        }


# =========================
# TC-007: Checkout Form
# =========================
class CheckoutForm(forms.Form):
    delivery_address = forms.CharField(
        label="Delivery Address",
        widget=forms.Textarea(attrs={
            "rows": 3,
            "placeholder": "Enter delivery address..."
        })
    )

    delivery_date = forms.DateTimeField(
        label="Delivery Date and Time",
        widget=forms.DateTimeInput(attrs={
            "type": "datetime-local"
        }),
        input_formats=["%Y-%m-%dT%H:%M"]
    )

    payment_method = forms.ChoiceField(
        label="Payment Method",
        choices=[
            ("", "-- Select Payment Method --"),
            ("card", "Credit / Debit Card"),
        ]
    )

    card_name = forms.CharField(
        label="Cardholder Name",
        max_length=100
    )

    card_number = forms.CharField(
        label="Card Number",
        max_length=16
    )

    expiry_date = forms.CharField(
        label="Expiry Date",
        max_length=5
    )

    cvv = forms.CharField(
        label="CVV",
        max_length=3
    )

    def clean_delivery_date(self):
        delivery_date = self.cleaned_data.get("delivery_date")

        if delivery_date <= timezone.now() + timezone.timedelta(hours=48):
            raise forms.ValidationError("Delivery date must be at least 48 hours from now.")

        return delivery_date

    def clean_card_number(self):
        card_number = self.cleaned_data.get("card_number", "").replace(" ", "")
        if card_number != "4242424242424242":
            raise forms.ValidationError("Use test card number: 4242424242424242")
        return card_number

    def clean_expiry_date(self):
        expiry_date = self.cleaned_data.get("expiry_date", "")
        if expiry_date != "12/34":
            raise forms.ValidationError("Use test expiry date: 12/34")
        return expiry_date

    def clean_cvv(self):
        cvv = self.cleaned_data.get("cvv", "")
        if cvv != "123":
            raise forms.ValidationError("Use test CVV: 123")
        return cvv