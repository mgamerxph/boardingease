from django import forms
from django.contrib.auth.models import User
from .models import BoardingHouse, Profile, Booking


# -----------------------------
# BoardingHouse Form
# -----------------------------
class BoardingHouseForm(forms.ModelForm):
    class Meta:
        model = BoardingHouse
        fields = [
            'name', 'address', 'price',
            'is_bedspacer', 'capacity',
            'image', 'additional_photo',
            'inclusions', 'other_inclusions',
            'amenities', 'other_amenities',
            'house_rules', 'other_house_rules',
            'curfew_start', 'curfew_end',
            'advance_months', 'deposit_months',
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'price': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_bedspacer': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'capacity': forms.NumberInput(attrs={'class': 'form-control'}),
            'other_inclusions': forms.TextInput(attrs={'class': 'form-control'}),
            'other_amenities': forms.TextInput(attrs={'class': 'form-control'}),
            'other_house_rules': forms.TextInput(attrs={'class': 'form-control'}),
            'inclusions': forms.CheckboxSelectMultiple,
            'amenities': forms.CheckboxSelectMultiple,
            'house_rules': forms.CheckboxSelectMultiple,
            'curfew_start': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'curfew_end': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'advance_months': forms.NumberInput(attrs={'class': 'form-control'}),
            'deposit_months': forms.NumberInput(attrs={'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        is_bedspacer = cleaned_data.get("is_bedspacer")
        capacity = cleaned_data.get("capacity")

        # If not bedspacer, force capacity = 1
        if not is_bedspacer:
            cleaned_data["capacity"] = 1

        return cleaned_data


# -----------------------------
# Owner Registration Form
# -----------------------------
class OwnerRegistrationForm(forms.ModelForm):
    first_name = forms.CharField(max_length=30)
    last_name = forms.CharField(max_length=30)
    contact_number = forms.CharField(max_length=15)
    address = forms.CharField(widget=forms.Textarea(attrs={'rows': 2}))
    email = forms.EmailField()
    business_permit = forms.ImageField(required=False)
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm = cleaned_data.get("confirm_password")
        if password and confirm and password != confirm:
            raise forms.ValidationError("Passwords do not match")
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        user.email = self.cleaned_data["email"]

        if commit:
            user.save()
            profile = user.profile
            profile.is_owner = True
            profile.contact_number = self.cleaned_data["contact_number"]
            profile.address = self.cleaned_data["address"]
            profile.email = self.cleaned_data["email"]
            profile.business_permit = self.cleaned_data.get("business_permit")
            profile.save()

        return user


# -----------------------------
# Booking Form
# -----------------------------
class BookingForm(forms.ModelForm):
    visit_date = forms.DateField(
        widget=forms.DateInput(
            attrs={'class': 'form-control', 'type': 'date'}
        ),
        required=True,
        label="Date of Visit"
    )

    class Meta:
        model = Booking
        fields = ['name', 'address', 'contact_number', 'email', 'visit_date']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'contact_number': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }