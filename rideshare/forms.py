from django import forms
from .models import UserProfile, Vehicle, OwnerRide, VehicleTypeInfo
from django.contrib.auth.forms import UserChangeForm
from django.contrib.admin.widgets import AdminSplitDateTime, AdminDateWidget
from datetime import datetime
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from .mywidgets import DateSelectorWidget, BootstrapDateTimePickerInput


# validation functions
def validate_positive(value):
    if (value <= 0):
        raise ValidationError("Should be postive!")


# extended user model
class UserProfileForm(forms.ModelForm):
    birthday = forms.DateField(
        widget=forms.DateInput(
            attrs={
                'placeholder': "YYYY-mm-dd",
            }
        )
    )

    class Meta:
        model = UserProfile
        fields = ['phoneNumber', 'birthday', 'gender']

    # def clean_birthday(self, *args, **kwargs):
    #     birthday = self.cleaned_data.get('birthday')
    #     print(type(birthday))
    #     if '-' in birthday:
    #         return birthday
    #     else:
    #         raise forms.ValidationError(
    #             "Please enter a valid date in yyyy-mm-dd format."
    #         )


# built in user model
class EditProfileForm(UserChangeForm):

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name',
                  'email', 'password']


# vehicle register form
class DriverProfileForm(forms.ModelForm):

    class Meta:
        model = Vehicle
        fields = ['vehicleType', 'plateNum', 'specialInfo']


class RideRequestForm(forms.ModelForm):
    destaddr = forms.CharField(
        label="Destination Address",
        widget=forms.Textarea(
            attrs={'cols': '10', 'rows': '5',
                   'placeholder': 'Enter your address here.'}),
        min_length=0,
        max_length=400
    )
    arrivalTime = forms.DateTimeField(
        label="Desired Arrival Time",
        input_formats=['%d/%m/%Y %H:%M'],
        widget=BootstrapDateTimePickerInput(
            attrs={
                'placeholder': "dd/mm/yyyy hh:mm",
            }
        )
    )

    class Meta:
        model = OwnerRide
        fields = ['destaddr', 'arrivalTime', 'numPassengers',
                  'vehicleType', 'shareable', 'specialRequest']

    def clean(self, *args, **kwargs):
        cleaned_data = self.cleaned_data
        vehicleType = cleaned_data.get('vehicleType')
        numPassengers = cleaned_data.get("numPassengers")
        vtinfo = VehicleTypeInfo()
        if numPassengers <= 0:
            raise forms.ValidationError(
                "The passenger num should be positive."
            )
        if (vtinfo.max_capacity[vehicleType] <= numPassengers):
            raise forms.ValidationError(
                "The passenger num is greater than the capacity of %s."
                % (vtinfo.type_choices[vehicleType][1])
            )
        return cleaned_data
