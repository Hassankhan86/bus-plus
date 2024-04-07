# myapp/forms.py

from django import forms
from .models import *
from .models import Trip, Route, Stops
from .tasks import contactus_email


class CustomUserSignupForm(forms.ModelForm):
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Confirm Password', widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['username', 'email', "password1", "password2"]

    def clean_username(self):
        username = self.cleaned_data.get("username")
        if not username:
            raise forms.ValidationError("This field is required.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if not email:
            raise forms.ValidationError("This field is required.")

        return email

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")

        if not password1:
            raise forms.ValidationError("This field is required.")

        if not password2:
            raise forms.ValidationError("This field is required.")

        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords do not match.")
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
        return user


class CustomUserLoginForm(forms.ModelForm):
    username = forms.EmailField(label='Email')  # Use EmailField for email validation
    password = forms.CharField(label='Password', widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['username', 'password']

    def clean_password(self):
        password = self.cleaned_data.get("password")
        if not password:
            raise forms.ValidationError("This field is required.")
        return password


class ResetForm(forms.Form):
    username = forms.EmailField(label='Email',widget=forms.EmailInput(attrs={"class":"form-control"}))

    def clean_email(self):
        email = self.cleaned_data.get("username")
        if not email:
            raise forms.ValidationError("Email is required")

        return email
    

class ResetPasswordForm(forms.ModelForm):
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Confirm Password', widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ["password1", "password2"]


    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")

        if not password1:
            raise forms.ValidationError("This field is required.")

        if not password2:
            raise forms.ValidationError("This field is required.")

        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords do not match.")
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
        return user



class StopsForm(forms.ModelForm):
    class Meta:
        model = Stops
        exclude = ["created_at"]
        fields = '__all__'


class RouteForm(forms.ModelForm):
    class Meta:
        model = Route
        fields = '__all__'
        exclude = ["created_at"]
        widgets = {
            'bus_stops': forms.CheckboxSelectMultiple,  # To display stops as checkboxes
        }


class TripForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['is_driver_required'].disabled = False
        self.fields['is_id_verified'].disabled = True

    def clean(self):
        show_buses = settings.IS_BUSES_SHOW_TO_USER
        data = self.cleaned_data
        if show_buses:
            number_children = data.get("number_children", 0)
            number_adults = data.get("number_adults", 0)
            total_passengers = number_children + number_adults
            bus = self.instance.bus
            if not bus.is_available or bus.bus_status != BUS_STATUS[0][0]:
                raise forms.ValidationError(
                    f"This Bus  is not available please Select another  one")
            if total_passengers and bus and total_passengers > bus.number_seats:
                raise forms.ValidationError(
                    f"The number of passengers exceeds the bus limit. The bus can accommodate only {bus.number_seats} passengers.")

            weight = data.get("weight")
            luggage_capacity = bus.luggage_capacity if bus else None

            if weight and luggage_capacity and weight > luggage_capacity:
                raise forms.ValidationError(
                    f"The weight of the luggage exceeds the bus's luggage capacity. The bus can carry luggage up to {luggage_capacity} kg.")
        return data

    class Meta:
        labels = {
            "is_id_verified": "Is id Verified",
            "identity_card": "Upload Identity"
        }
        model = Trip
        exclude = ["bus", "user", "trip_status", "bus_returned_date", "created_at", "modified_at", "per_scale_charges",
                   "number_passengers", "trip_type","scale"]
        widgets = {
            "number_children": forms.NumberInput(attrs={"onchange": "update_passengers()"}),
            "number_adults": forms.NumberInput(attrs={"onchange": "update_passengers()"}),
            "weight_of_luggage": forms.NumberInput(attrs={"onchange": "update_passengers()"}),

            "trip_category": forms.Select(
                attrs={"class": "select-contain-select", "placeholder": "Choose license type"})
        }


class UserLicenseForm(forms.ModelForm):
    class Meta:
        model = UserLicense
        exclude = ["id", "user", "trip", "status", "created_at"]
        widgets = {
            "license": forms.FileInput(attrs={"required": False}),
            "license_type": forms.Select(
                attrs={"class": "select-contain-select", "placeholder": "Choose license type", "required": False})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['license'].required = False

    def clean(self):

        data = self.cleaned_data
        self_drive_available = self.trip.bus.self_drive_available
        if self.trip.trip_type == TRIP_TYPE[2][0] and not self_drive_available:
            raise forms.ValidationError(
                f"Sorry this bus is not available for self drive")
        if "license" not in data and not self.instance.license:
            raise forms.ValidationError("License file is required")
        if "license" not in data:
            data["license"] = self.instance.license
        license_obj = License.objects.filter(license_name=data.get("license_type"),
                                             seat_limit__gte=self.trip.bus.number_seats).first()
        if not license_obj:
            raise forms.ValidationError(
                f"Please select a valid license. You do not have permission to drive a {self.trip.bus.number_seats}-seater Bus.")
        return data

    def __init__(self, *args, user=None, trip=None, **kwargs):
        super(UserLicenseForm, self).__init__(*args, **kwargs)
        self.user = user
        self.trip = trip
        instance = kwargs.get('instance')
        if instance and instance.license:
            self.fields['license'].initial = instance.license

    def save(self, commit=True):
        instance = super(UserLicenseForm, self).save(commit=False)
        instance.user = self.user
        instance.trip = self.trip
        if commit:
            instance.save()
        return instance


class UseInsuranceForm(forms.ModelForm):
    class Meta:
        model = TripInsurance
        exclude = ["id", "trip", "date_time", "created_at", "modified_at"]
        widgets = {
            "insurance": forms.SelectMultiple(attrs={"class": "select-contain-select insurances", "required": False}, )
        }
        labels = {
            "insurance": "Select Insurances"
        }

    def clean(self):
        insurance_data = self.cleaned_data['insurance']
        if not insurance_data:
            raise forms.ValidationError("Please select at least one insurance.")
        return insurance_data


class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactUs
        fields = "__all__"
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Your name"}),
            "email": forms.TextInput(attrs={"class": "form-control", "placeholder": "Email address"}),
            "subject": forms.TextInput(attrs={"class": "form-control", "placeholder": "Subject"}),
            "message": forms.TextInput(attrs={"class": "message-control form-control", "placeholder": "Write message"}),
        }

