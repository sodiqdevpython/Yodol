from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, UserConfirmation


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('id', 'username', 'email', 'phone_number', 'auth_type', 'auth_status', 'is_active', 'is_staff')
    list_filter = ('auth_type', 'auth_status', 'is_staff', 'is_superuser', 'is_active')

    search_fields = ('username', 'email', 'phone_number')
    ordering = ('id',)

    readonly_fields = ('last_login', 'date_joined')

    fieldsets = (
        (None, {
            'fields': ('username', 'password')
        }),
        ("Shaxsiy ma'lumotlar", {
            'fields': ('first_name', 'last_name', 'email', 'phone_number', 'gender', 'birth_date', 'profile_picture')
        }),
        ("Ruxsatlar", {
            'fields': ('is_active', 'is_staff', 'is_superuser')
        }),
        ("Django Permissions", {
            'fields': ('groups', 'user_permissions')
        }),
        ("Holat", {
            'fields': ('auth_type', 'auth_status', 'is_premium')
        }),
        ("Vaqtlar", {
            'fields': ('last_login', 'date_joined')
        }),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'phone_number', 'password1', 'password2', 'is_staff', 'is_superuser'),
        }),
    )

@admin.register(UserConfirmation)
class UserConfirmationAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'code', 'verify_type', 'expiration_time', 'is_used')
    list_filter = ('verify_type', 'is_used')
    search_fields = ('user__username', 'user__email', 'code')
    ordering = ('-id',)
