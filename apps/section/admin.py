from django.contrib import admin

from .models import Section


@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ("title", "instructor", "course", "status", "order", "deleted_at")
    list_filter = ("deleted_at", "status", "course")
    search_fields = (
        "title",
        "instructor__email",
        "instructor__first_name",
        "course__title",
    )
    ordering = ("course", "order")

    fieldsets = (
        (
            "General Information",
            {"fields": ("title", "slug", "description", "status", "order")},
        ),
        ("Relations", {"fields": ("instructor", "course")}),
        ("Timestamps", {"fields": ("created_at", "updated_at", "deleted_at")}),
    )

    readonly_fields = ("created_at", "updated_at", "deleted_at", "slug")
