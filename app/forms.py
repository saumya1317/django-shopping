from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm,PasswordChangeForm,SetPasswordForm,PasswordResetForm
from django.contrib.auth.models import User
from .models import Customer


class CustomerRegistrationForm(UserCreationForm):
    # Username field with autofocus and Bootstrap styling
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'autofocus': 'True',
            'class': 'form-control',
            'placeholder': 'Enter your username'
        })
    )

    # Email field with Bootstrap styling
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email address'
        })
    )

    # Password1 field with Bootstrap styling and PasswordInput widget
    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your password'
        })
    )

    # Password2 field with Bootstrap styling and PasswordInput widget
    password2 = forms.CharField(
        label='Confirm password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm your password'
        })
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']


# Login Form
class LoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'autofocus': 'True',
            'class': 'form-control',
            'placeholder': 'Enter your username or email'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your password'
        })
    )

    class Meta:
        model = User
        fields = ['username', 'password']



class CustomerProfileform(forms.ModelForm):
    
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your full name',
            }),
            'locality': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your locality',
            }),
            'city': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your city',
            }),
            'mobile': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your mobile number',
            }),
            'state': forms.Select(attrs={
                'class': 'form-select',
            }),
            'zipcode': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your zip code',
            }),
        }
        class Meta:
         model = Customer
        # Include all fields you want in the form
         fields = ['name', 'locality', 'city', 'mobile', 'state', 'zipcode']
class MyPasswordChangeForm(PasswordChangeForm):
    old_password =forms.CharField(label='Old password ',widget=forms.PasswordInput(attrs={'autofocus' :'True','autocomplete':'current-password','class':'form-control'})) 
    new_password1= forms.CharField(label='New Password',widget=forms.PasswordInput(attrs ={'autocomplete':'curent-password','class':'form-control'}))
    new_password2=forms.CharField(label='Confirm-Password',widget=forms.PasswordInput(attrs={'autocomplete':'current-password','class':'form-control'}))
class MyPasswordResetForm(PasswordResetForm):
   email= forms.EmailField(widget=forms.EmailInput(attrs={'class':'form-control'}))
class MySetPasswordForm(SetPasswordForm):
    new_password1=forms.CharField(label='New Password',widget=forms.PasswordInput(attrs={'autocomplete':'current-password', 'class':'form-control'}))
    new_password1=forms.CharField(label='Confirm New Password',widget=forms.PasswordInput(attrs={'autocomplete':'current-password', 'class':'form-control'}))