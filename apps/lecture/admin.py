from django.contrib import admin

from .models import Lecture


@admin.register(Lecture)
class LectureModelAdmin(admin.ModelAdmin):
    """
    Admin configuration for the Lecture model.
    """

    list_display = (
        "title",
        "lecture_type",
        "instructor",
        "course",
        "section",
        "status",
        "order",
        "duration",
        "deleted_at",
    )
    list_filter = ("deleted_at", "status", "lecture_type", "course", "section")
    search_fields = ("title", "instructor__email", "course__title", "section__title")
    ordering = ("course", "section", "order")

    fieldsets = (
        (
            "General Information",
            {
                "fields": (
                    "title",
                    "slug",
                    "description",
                    "lecture_type",
                    "status",
                    "order",
                    "duration",
                    "is_preview",
                )
            },
        ),
        (
            "Content",
            {"fields": ("source", "thumbnail", "document_content", "resources")},
        ),
        ("Relations", {"fields": ("instructor", "course", "section")}),
        ("Feedback", {"fields": ("reject_reason",)}),
        (
            "Timestamps & Soft Delete",
            {"fields": ("created_at", "updated_at", "deleted_at")},
        ),
    )

    readonly_fields = ("created_at", "updated_at", "deleted_at", "slug")
