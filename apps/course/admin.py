from django.contrib import admin

from .models import Course

# Register your models here.


class CourseModelAdmin(admin.ModelAdmin):

    # The fields to be used in displaying the Course model.
    # These override the definitions on the ModelAdmin
    list_display = (
        "title",
        "slug",
        "instructor",
        "is_free",
        "price",
        "total_hours",
        "total_articles",
        "status",
        "deleted_at",
    )
    fieldsets = (
        (
            "Course",
            {
                "fields": (
                    "title",
                    "short_description",
                    "long_description",
                    "instructor",
                    "categories",
                    "thumbnail",
                    "keywords",
                    "reject_reason",
                    "learn_description_points",
                    "requirements",
                    "is_free",
                    "price",
                    "total_hours",
                    "total_articles",
                    "status",
                    "deleted_at",
                )
            },
        ),
    )
    add_fieldsets = (
        (
            "Create Course",
            {
                "classes": ("wide",),
                "fields": (
                    "title",
                    "short_description",
                    "long_description",
                    "instructor",
                    "categories",
                    "thumbnail",
                    "keywords",
                    "reject_reason",
                    "learn_description_points",
                    "requirements",
                    "is_free",
                    "price",
                    "total_hours",
                    "total_articles",
                    "status",
                ),
            },
        ),
    )
    list_filter = ("deleted_at", "is_free")
    search_fields = (
        "title",
        "slug",
        "instructor",
        "categories",
        "price",
        "total_hours",
        "total_articles",
    )
    ordering = ("title", "deleted_at")
    filter_horizontal = ()


# Now register the new UserModelAdmin...
admin.site.register(Course, CourseModelAdmin)
