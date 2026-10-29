from django.contrib import admin

from .models import Localization

# Register your models here.


class LocalizationModelAdmin(admin.ModelAdmin):

    def has_module_permission(self, request):
        return request.user.is_active and request.user.is_admin

    def has_view_permission(self, request, obj=None):
        return request.user.is_active and request.user.is_admin

    has_add_permission = has_view_permission
    has_change_permission = has_view_permission
    has_delete_permission = has_view_permission

    # The fields to be used in displaying the Localization model.
    # These override the definitions on the ModelAdmin
    list_display = ("language_name", "country", "deleted_at")
    fieldsets = (
        ("Localization", {"fields": ("language_name", "country", "deleted_at")}),
    )
    add_fieldsets = (
        (
            "Create Localization",
            {
                "classes": ("wide",),
                "fields": ("language_name", "country"),
            },
        ),
    )
    list_filter = ("deleted_at", "country")
    search_fields = ("language_name",)
    ordering = ("language_name", "deleted_at")
    filter_horizontal = ()
    readonly_fields = ("deleted_at", "created_at", "updated_at")


# Now register the new LocalizationModelAdmin...
admin.site.register(Localization, LocalizationModelAdmin)
