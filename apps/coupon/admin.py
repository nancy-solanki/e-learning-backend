from django.contrib import admin

from .models import Coupon


@admin.register(Coupon)
class CouponModelAdmin(admin.ModelAdmin):
    """
    Admin configuration for the Coupon model.
    """

    list_display = (
        "code",
        "coupon_type",
        "value",
        "course",
        "used",
        "limit",
        "expired_at",
        "deleted_at",
    )
    list_filter = ("deleted_at", "coupon_type", "is_global", "is_instructor_created")
    search_fields = ("code", "course__title")
    ordering = ("-created_at",)

    fieldsets = (
        (
            "General Information",
            {
                "fields": (
                    "code",
                    "coupon_type",
                    "value",
                    "course",
                    "is_global",
                    "is_instructor_created",
                )
            },
        ),
        ("Usage & Limit", {"fields": ("limit", "used", "is_unlimited", "expired_at")}),
        (
            "Timestamps & Soft Delete",
            {"fields": ("created_at", "updated_at", "deleted_at")},
        ),
    )

    readonly_fields = ("created_at", "updated_at", "deleted_at", "used")
