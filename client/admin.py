from django.contrib import admin
from .models import Profile, BoardingHouse
from django.core.mail import send_mail

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'first_name',
        'last_name',
        'contact_number',
        'email',
        'address',
        'is_owner',
        'is_approved',
    )
    list_filter = ('is_owner', 'is_approved')
    search_fields = (
        'user__username',
        'user__email',
        'first_name',
        'last_name',
        'contact_number',
    )
    list_editable = ('is_approved',)
    fieldsets = (
        (None, {
            'fields': (
                'user',
                'first_name',
                'last_name',
                'address',
                'contact_number',
                'email',
                'business_permit',  # 🆕 Image field for permit
            )
        }),
        ('Permissions', {
            'fields': ('is_owner', 'is_approved')
        }),
    )

    def save_model(self, request, obj, form, change):
        if change:
            old_obj = Profile.objects.get(pk=obj.pk)
            if not old_obj.is_approved and obj.is_approved:
                subject = "Your BoardingEase Account Has Been Approved"
                message = f"""
Hi {obj.first_name} {obj.last_name},

Your account on BoardingEase has been approved by the administrator.
You can now log in and start managing your boarding house.

Login here: https://mgamerxph.pythonanywhere.com/login

Thank you,
BoardingEase Team
"""
                send_mail(subject, message, None, [obj.user.email])
        super().save_model(request, obj, form, change)

admin.site.register(BoardingHouse)
