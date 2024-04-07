from django import forms
from booking.models import *
from django.forms import inlineformset_factory


class BusForm(forms.ModelForm):
    images = forms.FileField(
        widget=forms.ClearableFileInput(
            attrs={"accept": "image/*", "data-min-file-count": "1", "name": "images", "required": False,
                   'multiple': True, 'placeholder': 'Select multiple images'}), required=False,
    )

    class Meta:
        model = Bus
        exclude = ['created_at', 'modified_at']
        widgets = {
            "bus_number": forms.TextInput(attrs={"class": "form-control", "placeholder": "Enter Bus Number"}),
            "company_name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Enter Company Name"}),
            "number_seats": forms.NumberInput(attrs={"class": "form-control", "placeholder": "Enter Number of Seats"}),
            "is_available": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "self_drive_available": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Enter Name"}),
            "bus_model": forms.TextInput(attrs={"class": "form-control", "placeholder": "Enter Bus Model"}),
            "bus_emergency_number": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Enter Bus Emergency Number"}),
            "luggage_capacity": forms.NumberInput(
                attrs={"class": "form-control", "placeholder": "Enter Luggage Capacity"}),
            "tag": forms.Select(attrs={"class": "form-control select2", "placeholder": "Select a Tag"}),

        }

    def save(self, commit=True):
        bus = super(BusForm, self).save(commit=commit)
        images_data = self.files.getlist('images')

        if images_data:
            for image in images_data:
                BusImages.objects.create(bus=bus, image=image)
        return bus


class BusChargeForm(forms.ModelForm):
    class Meta:
        model = BusCharges
        fields = ["id", 'bus', 'scale', 'per_scale_charges']
        widgets = {
            "scale": forms.Select(attrs={"class": "form-control", "placeholder": "Select a Scale"}),
            "per_scale_charges": forms.NumberInput(
                attrs={"class": "form-control", "placeholder": "Enter Per Scale Charges"}),

            "id": forms.HiddenInput(attrs=
                                    {"required": False})
        }


BusChargeInlineForm = inlineformset_factory(
    Bus,
    BusCharges,
    form=BusChargeForm,
    extra=len(BUS_CHARGES_SCALE),
)


class FaqCategoryForm(forms.ModelForm):
    class Meta:
        model = FaqsCategory
        exclude = ['created_at', 'modified_at']
        widgets = {
            "type": forms.TextInput(attrs={"class": "form-control", "placeholder": "Enter Faq Type"}),
        }


class FaqForm(forms.ModelForm):
    class Meta:
        model = Faqs
        exclude = ['created_at', 'modified_at']

        widgets = {
            "type": forms.Select(attrs={"class": "form-control"}),
            "question": forms.TextInput(attrs={"class": "form-control", "placeholder": "Enter Question"}),
            "answer": forms.TextInput(attrs={"class": "form-control", "placeholder": "Enter Answer"}),

        }


class CouponForm(forms.ModelForm):
    class Meta:
        model = Coupons
        exclude = ['created_at', 'modified_at']
        widgets = {
            "code": forms.TextInput(attrs={"class": "form-control", "placeholder": "Enter Coupon Code"}),
            "start_date": forms.DateInput(
                attrs={"class": "form-control", "placeholder": "Enter Start Date", "type": "date"}),
            "end_date": forms.DateInput(
                attrs={"class": "form-control", "placeholder": "Enter End Date", "type": "date"}),
            "minimum_amount": forms.NumberInput(attrs={"class": "form-control", "placeholder": "Enter Minimum Amount"}),
            "amount": forms.NumberInput(attrs={"class": "form-control", "placeholder": "Enter Amount"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set default values for is_active and one_time_use_per_user fields
        self.fields["is_active"].initial = True
        self.fields["one_time_use_per_user"].initial = True


class CitiesForm(forms.ModelForm):
    class Meta:
        model = Cities
        exclude = ['created_at', 'modified_at']
        widgets = {
            "city": forms.TextInput(attrs={"class": "form-control", "placeholder": "Enter City"}),
            "latitude": forms.NumberInput(attrs={"class": "form-control", "placeholder": "Enter Latitude"}),
            "longitude": forms.NumberInput(attrs={"class": "form-control", "placeholder": "Enter Longitude"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class FeaturedTripsForm(forms.ModelForm):
    child_number = forms.IntegerField(initial=0)
    adult_number = forms.IntegerField(initial=0)
    weight_of_luggage = forms.IntegerField(initial=0)

    class Meta:
        model = FeaturedTrips
        exclude = ['created_at', 'modified_at']
        widgets = {
            "child_number": forms.NumberInput(attrs={"onchange": "update_passengers()", "value": 0}),
            "adult_number": forms.NumberInput(attrs={"onchange": "update_passengers()", "value": 0}),
            "weight_of_luggage": forms.NumberInput(attrs={"onchange": "update_passengers()", "value": 0}),
            'bus': forms.Select(attrs={'class': 'form-control'}),
            'trip_location': forms.Select(attrs={'class': 'form-control'}),
            'price': forms.NumberInput(attrs={'class': 'form-control'}),
            'discount_price': forms.NumberInput(attrs={'class': 'form-control'}),
            'rating': forms.NumberInput(attrs={'class': 'form-control'}),
        }


class TripCategoryForm(forms.ModelForm):
    class Meta:
        model = TripCategory
        exclude = ['created_at', 'modified_at']

        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),

        }


class StopChargesForm(forms.ModelForm):
    class Meta:
        model = StopCharges
        exclude = ['created_at', 'modified_at']
        widgets = {
            'stop_title': forms.TextInput(attrs={'class': 'form-control'}),
            'charge_per_minute': forms.NumberInput(attrs={'class': 'form-control'}),
        }


class LicenseForm(forms.ModelForm):
    class Meta:
        model = License
        exclude = ['created_at', 'modified_at']
        widgets = {
            'license_name': forms.TextInput(attrs={'class': 'form-control'}),
            'seat_limit': forms.NumberInput(attrs={'class': 'form-control'}),
        }


class InsuranceForm(forms.ModelForm):
    class Meta:
        model = Insurance
        exclude = ['created_at', 'modified_at']

        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'id': 'editor', 'required': False}),

            'coverage_amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'premium': forms.NumberInput(attrs={'class': 'form-control'}),
        }
