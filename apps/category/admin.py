from django.contrib import admin

from .models import Category

# Register your models here.


class CategoryModelAdmin(admin.ModelAdmin):
    list_display = ("title", "slug", "thumbnail")
    fieldsets = (("Category", {"fields": ("title", "description", "thumbnail")}),)
    add_fieldsets = (
        (
            "Create Category",
            {
                "classes": ("wide",),
                "fields": ("title", "description", "thumbnail"),
            },
        ),
    )
    search_fields = ("title",)
    ordering = ("title",)
    filter_horizontal = ()


admin.site.register(Category, CategoryModelAdmin)
