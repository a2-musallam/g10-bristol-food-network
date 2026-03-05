from django import forms
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import User, Product


# TC-001: Producer Registration Form
class ProducerRegistrationForm(forms.ModelForm):
    contact_name = forms.CharField(
        label="Contact Name",
        widget=forms.TextInput(attrs={"placeholder": "e.g. Jane Smith"})
    )
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ["business_name", "contact_name", "email", "phone", "address", "password"]

        labels = {
            "address": "Business Address and Postcode",
        }

        widgets = {
            "address": forms.Textarea(attrs={
                "rows": 3,
                "placeholder": "Enter full business address and postcode here..."
            }),
        }

    # 🔐 PASSWORD SECURITY (TC-022)
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
        contact_name = self.cleaned_data.get("contact_name")

        # Split "Jane Smith" into first and last name
        names = contact_name.split(" ", 1)
        user.first_name = names[0]
        user.last_name = names[1] if len(names) > 1 else ""

        # Create username automatically
        user.username = contact_name.replace(" ", "_").lower()

        # 🔐 Password hashing
        user.set_password(self.cleaned_data["password"])

        if commit:
            user.save()

        return user


# TC-002: Customer Registration Form
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

    # 🔐 PASSWORD SECURITY (TC-022)
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

        # 🔐 Password hashing
        user.set_password(self.cleaned_data["password"])

        if commit:
            user.save()

        return user


# TC-022: Login Form (REMEMBER ME ADDED)
class LoginForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        label="Username or Contact Name"
    )

    password = forms.CharField(
        widget=forms.PasswordInput
    )

    # ✅ Remember Me for session persistence
    remember_me = forms.BooleanField(
        required=False,
        label="Remember Me"
    )


# TC-003: Product Form
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