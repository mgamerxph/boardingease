from django import forms
from .models import BoardingHouse, Profile, Booking
from django.contrib.auth.models import User

class BoardingHouseForm(forms.ModelForm):
    class Meta:
        model = BoardingHouse
        fields = ['name', 'address', 'description', 'price', 'image']


class OwnerRegistrationForm(forms.ModelForm):
    first_name = forms.CharField(max_length=30)
    last_name = forms.CharField(max_length=30)
    contact_number = forms.CharField(max_length=15)
    address = forms.CharField(widget=forms.Textarea(attrs={'rows': 2}))
    email = forms.EmailField()
    business_permit = forms.ImageField(required=False)  # ✅ New image field
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
        user.email = self.cleaned_data["email"]  # ✅ Save email to user

        if commit:
            user.save()
            profile = user.profile
            profile.is_owner = True
            profile.contact_number = self.cleaned_data["contact_number"]
            profile.address = self.cleaned_data["address"]
            profile.email = self.cleaned_data["email"]  # ✅ Save to profile too
            profile.business_permit = self.cleaned_data.get("business_permit")  # ✅ Save image
            profile.save()

        return user

class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ['name', 'address', 'contact_number']