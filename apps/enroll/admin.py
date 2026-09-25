from django.contrib import admin

from .models import Enroll


@admin.register(Enroll)
class EnrollModelAdmin(admin.ModelAdmin):
    """
    Admin configuration for the Enroll model.
    """

    list_display = ("user", "course", "created_at", "updated_at", "deleted_at")
    list_filter = ("deleted_at", "course", "user")
    search_fields = ("user__email", "user__username", "course__title")
    ordering = ("-created_at",)

    fieldsets = (
        ("General Information", {"fields": ("user", "course")}),
        (
            "Timestamps & Soft Delete",
            {"fields": ("created_at", "updated_at", "deleted_at")},
        ),
    )

    readonly_fields = ("created_at", "updated_at", "deleted_at")
