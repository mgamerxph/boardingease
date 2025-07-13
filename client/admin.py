from django.contrib import admin
from .models import Profile, BoardingHouse

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'first_name',
        'last_name',
        'contact_number',
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
            'fields': ('user', 'first_name', 'last_name', 'address', 'contact_number')
        }),
        ('Permissions', {
            'fields': ('is_owner', 'is_approved')
        }),
    )

admin.site.register(BoardingHouse)
