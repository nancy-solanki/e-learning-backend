from django.contrib import admin

from .models import Rating


@admin.register(Rating)
class RatingModelAdmin(admin.ModelAdmin):
    """
    Admin configuration for the Rating model.
    """

    list_display = ("user", "course", "rating", "created_at", "deleted_at")
    list_filter = ("deleted_at", "rating", "course")
    search_fields = ("user__email", "course__title", "comment")
    ordering = ("-created_at",)

    fieldsets = (
        (
            "General Information",
            {"fields": ("user", "course", "rating", "comment", "response")},
        ),
        (
            "Timestamps & Soft Delete",
            {"fields": ("created_at", "updated_at", "deleted_at")},
        ),
    )

    readonly_fields = ("created_at", "updated_at", "deleted_at")
