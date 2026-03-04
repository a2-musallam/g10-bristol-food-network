from django import forms
from .models import User
from .models import Product

# TC-001: Producer Registration Form
class ProducerRegistrationForm(forms.ModelForm):
    # This is the field where Jane Smith can type her full name with spaces
    contact_name = forms.CharField(
        label="Contact Name", 
        widget=forms.TextInput(attrs={'placeholder': 'e.g. Jane Smith'})
    )
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        # We remove 'username' from fields because we will generate it automatically
        fields = ['business_name', 'contact_name', 'email', 'phone', 'address', 'password']
        
        labels = {
            'address': 'Business Address and Postcode',
        }
        
        widgets = {
            'address': forms.Textarea(attrs={
                'rows': 3, 
                'placeholder': 'Enter full business address and postcode here...'
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get("password") != cleaned_data.get("confirm_password"):
            raise forms.ValidationError("Passwords do not match!")
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        contact_name = self.cleaned_data.get('contact_name')
        
        # 1. Split "Jane Smith" into First and Last names for the database
        names = contact_name.split(' ', 1)
        user.first_name = names[0]
        user.last_name = names[1] if len(names) > 1 else ''
        
        # 2. Create a database-friendly username (jane_smith) automatically
        # This solves the "No spaces allowed" error!
        user.username = contact_name.replace(" ", "_").lower()
        
        if commit:
            user.save()
        return user

# TC-002: Customer Registration Form
class CustomerRegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        # Customers usually have separate first/last name boxes, but let's keep it consistent
        fields = ['first_name', 'last_name', 'username', 'email', 'phone', 'address', 'password']
        
        labels = {
            'username': 'Login Username (No spaces)',
            'address': 'Delivery Address and Postcode',
        }
        
        widgets = {
            'address': forms.Textarea(attrs={
                'rows': 3, 
                'placeholder': 'Enter your delivery address and postcode...'
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get("password") != cleaned_data.get("confirm_password"):
            raise forms.ValidationError("Passwords do not match!")
        return cleaned_data

# TC-022: Login Form
class LoginForm(forms.Form):
    username = forms.CharField(max_length=150, label="Username or Contact Name")
    password = forms.CharField(widget=forms.PasswordInput)
    
# Product Form
class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        # IMPORTANT: do NOT include "producer" here (we set it in the view)
        fields = ["name", "description", "price", "stock", "image", "allergens"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
        }