from django import forms
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import (
    Product,
    Review,
    User,
    Recipe,
    FarmStory,
)
from .models import FarmStory

class FarmStoryForm(forms.ModelForm):
    class Meta:
        model = FarmStory
        fields = ["title", "content", "image"]


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


class CustomerRegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ["first_name", "last_name", "email", "phone", "address", "password"]

        labels = {
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

class CommunityGroupRegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = [
            "business_name",
            "email",
            "phone",
            "password",
            "confirm_password",
        ]

        labels = {
            "business_name": "Community Group Name",
            "email": "Institutional Email Address",
            "phone": "Contact Number",
        }

        widgets = {
            "business_name": forms.TextInput(attrs={
                "placeholder": "e.g. St. Mary's School"
            }),
            "email": forms.EmailInput(attrs={
                "placeholder": "e.g. catering@stmarys-school.org.uk"
            }),
            "phone": forms.TextInput(attrs={
                "placeholder": "e.g. 0117 123 4567"
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

        user.username = self.cleaned_data["email"]
        user.set_password(self.cleaned_data["password"])

        user.is_customer = True
        user.is_community_group = True
        user.invoice_payment_enabled = True
        user.bulk_discount_rate = 10

        if commit:
            user.save()

        return user


class LoginForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        label="Email Address"
    )

    password = forms.CharField(widget=forms.PasswordInput)

    remember_me = forms.BooleanField(
        required=False,
        label="Remember Me"
    )


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
            "seasonal_start_month",
            "seasonal_end_month",
            "stock",
            "low_stock_threshold",
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
            ("paypal", "PayPal (Test)"),
            ("klarna", "Klarna (Test)"),
        ]
    )

    card_name = forms.CharField(
        label="Cardholder Name",
        max_length=100,
        required=False
    )

    card_number = forms.CharField(
        label="Card Number",
        max_length=16,
        required=False
    )

    expiry_date = forms.CharField(
        label="Expiry Date",
        max_length=5,
        required=False
    )

    cvv = forms.CharField(
        label="CVV",
        max_length=3,
        required=False
    )

    def clean_delivery_date(self):
        delivery_date = self.cleaned_data.get("delivery_date")

        if delivery_date <= timezone.now() + timezone.timedelta(hours=48):
            raise forms.ValidationError("Delivery date must be at least 48 hours from now.")

        return delivery_date

    def clean(self):
        cleaned_data = super().clean()
        payment_method = cleaned_data.get("payment_method")

        if payment_method == "card":
            card_number = cleaned_data.get("card_number", "").replace(" ", "")
            expiry_date = cleaned_data.get("expiry_date", "")
            cvv = cleaned_data.get("cvv", "")

            if card_number != "4242424242424242":
                self.add_error("card_number", "Use test card number: 4242424242424242")
            if expiry_date != "12/34":
                self.add_error("expiry_date", "Use test expiry date: 12/34")
            if cvv != "123":
                self.add_error("cvv", "Use test CVV: 123")

        return cleaned_data


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ["rating", "title", "comment"]
        widgets = {
            "rating": forms.NumberInput(attrs={"min": 1, "max": 5}),
            "title": forms.TextInput(attrs={"placeholder": "Review title"}),
            "comment": forms.Textarea(attrs={"rows": 4, "placeholder": "Write your review here..."})
        }

    def clean_rating(self):
        rating = self.cleaned_data.get("rating")
        if rating < 1 or rating > 5:
            raise forms.ValidationError("Rating must be between 1 and 5.")
        return rating
class RecipeForm(forms.ModelForm):
    class Meta:
        model = Recipe
        fields = [
            "title",
            "description",
            "ingredients",
            "instructions",
            "season",
            "products",
            "image",
        ]

        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
            "ingredients": forms.Textarea(attrs={"rows": 5}),
            "instructions": forms.Textarea(attrs={"rows": 6}),
            "products": forms.CheckboxSelectMultiple(),
        }


