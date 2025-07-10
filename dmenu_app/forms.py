from django import forms
from .models import Category, MenuItem, Profile
from django.utils.safestring import mark_safe
from django.db.models import Max
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.models import User

class CustomerDetailsForm(forms.Form):
    name = forms.CharField(max_length=100, label='Your Name')
    phone_number = forms.CharField(max_length=15, label='Your Phone Number')

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name','sort_id'] 

        widgets = {
            'sort_id': forms.NumberInput(attrs={
                'min': '1',
                'class': 'form-control'
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Category Name'
            })
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)  # Get the user from kwargs
        super().__init__(*args, **kwargs)
        
        # If editing an existing instance, ensure it belongs to the user
        if self.instance.pk and self.user:
            if self.instance.user != self.user:
                raise forms.ValidationError("You don't own this category")

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if self.user and Category.objects.filter(user=self.user, name=name).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("You already have a category with this name")
        return name

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.user:
            instance.user = self.user  # Set the owner
        if commit:
            instance.save()
        return instance
    
    
class MenuItemForm(forms.ModelForm):
    class Meta:
        model = MenuItem
        fields = ['name', 'price', 'category','image']  

        widgets = {
            'price': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)  # Get the user from kwargs
        super().__init__(*args, **kwargs)
        if self.user:
            # Filter categories to only those belonging to the current user
            self.fields['category'].queryset = Category.objects.filter(user=self.user)

# from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
# from .models import Restaurant, RestaurantUser, Category, MenuItem, Order

# class RestaurantSignupForm(UserCreationForm):
#     restaurant_name = forms.CharField(
#         max_length=100,
#         widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Restaurant Name'})
#     )
#     address = forms.CharField(
#         widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Full Address'})
#     )
#     phone = forms.CharField(
#         max_length=15,
#         widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Contact Number'})
#     )
#     email = forms.EmailField(
#         widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email Address'})
#     )
#     logo = forms.ImageField(
#         required=False,
#         widget=forms.FileInput(attrs={'class': 'form-control'}),
#         help_text="Upload your restaurant logo"
#     )

#     class Meta:
#         model = RestaurantUser
#         fields = ('username', 'email', 'password1', 'password2',
#                  'restaurant_name', 'address', 'phone', 'logo')
#         widgets = {
#             'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}),
#             'password1': forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'}),
#             'password2': forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm Password'}),
#         }

# class RestaurantLoginForm(AuthenticationForm):
#     username = forms.CharField(
#         widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'})
#     )
#     password = forms.CharField(
#         widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'})
#     )

# class RestaurantProfileForm(forms.ModelForm):
#     class Meta:
#         model = Restaurant
#         fields = ['name', 'logo', 'address', 'phone']
#         widgets = {
#             'name': forms.TextInput(attrs={'class': 'form-control'}),
#             'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
#             'phone': forms.TextInput(attrs={'class': 'form-control'}),
#             #'gst_number': forms.TextInput(attrs={'class': 'form-control'}),
#             'logo': forms.FileInput(attrs={'class': 'form-control'}),
#         }



# class UsernameRecoveryForm(forms.Form):
#     email = forms.EmailField(
#         label="Email",
#         max_length=254,
#         widget=forms.EmailInput(attrs={'autocomplete': 'email'})
#     )

class UserUpdateForm(forms.ModelForm):
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ['username', 'email']

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = [
            'restaurant_name', 
            'address', 
            'phone', 
            'logo', 
            'gst_number',
            'theme_color',
            'cart_enabled',
            'menu_display_mode',
            
            
        ]
        widgets = {
            'theme_color': forms.TextInput(attrs={'type': 'color'}),
            'menu_display_mode': forms.Select(choices=Profile.MENU_DISPLAY_CHOICES),
        }
