from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm
from django import forms
from django.contrib.auth.models import User


class RegisterForm(UserCreationForm):
    email = forms.EmailField()
    first_name = forms.CharField(max_length=30)
    last_name = forms.CharField(max_length=50)

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email',
                  'password1', 'password2']
        # widget = {
        #     'username': forms.CharField(attrs={'class': 'form-control'}),
        #     'first_name': forms.CharField(attrs={'class': 'form-control'}),
        #     'username': forms.CharField(attrs={'class': 'form-control'}),
        #     'username': forms.CharField(attrs={'class': 'form-control'}),
        #     'username': forms.CharField(attrs={'class': 'form-control'}),
        #     'username': forms.CharField(attrs={'class': 'form-control'}),
        # }
