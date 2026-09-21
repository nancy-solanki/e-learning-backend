from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User

# Register your models here.


class UserModelAdmin(BaseUserAdmin):
    list_display = ("email", "username", "first_name", "last_name", "avatar", "status")
    list_filter = ("status",)
    fieldsets = (
        ("User Credentials", {"fields": ("email", "password")}),
        (
            "Personal info",
            {"fields": ("first_name", "last_name", "username", "avatar")},
        ),
        ("Permissions", {"fields": ("status", "groups")}),
    )
    add_fieldsets = (
        (
            "Register User",
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "first_name",
                    "last_name",
                    "username",
                    "password1",
                    "password2",
                    "status",
                    "groups",
                ),
            },
        ),
    )
    search_fields = ("email", "username", "first_name", "last_name")
    ordering = ("status",)
    filter_horizontal = ("groups",)


admin.site.register(User, UserModelAdmin)
