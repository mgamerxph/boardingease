from django.contrib import admin
from .models import Profile, BoardingHouse
from django.core.mail import send_mail
from django.utils.html import format_html

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'first_name',
        'last_name',
        'contact_number',
        'email',
        'address',
        'business_permit',
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
    readonly_fields = ('business_permit_preview',)

    fieldsets = (
        (None, {
            'fields': (
                'user',
                'first_name',
                'last_name',
                'email',
                'contact_number',
                'address',
                'business_permit',
                'business_permit_preview',  # 👁️ image preview
            )
        }),
        ('Permissions', {
            'fields': ('is_owner', 'is_approved')
        }),
    )

    def business_permit_preview(self, obj):
        if obj.business_permit:
            return format_html('<img src="{}" style="max-height: 200px;" />', obj.business_permit.url)
        return "No permit uploaded"
    business_permit_preview.short_description = 'Business Permit Preview'

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