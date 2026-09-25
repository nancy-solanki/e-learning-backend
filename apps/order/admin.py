from django.contrib import admin

from .models import Order

# Register your models here.


class OrderModelAdmin(admin.ModelAdmin):

    # The fields to be used in displaying the Order model.
    # These override the definitions on the ModelAdmin
    list_display = (
        "course",
        "user",
        "instructor",
        "coupon",
        "total_paid",
        "is_free",
        "admin_commission",
        "status",
    )
    fieldsets = (
        (
            "Order",
            {
                "fields": (
                    "course",
                    "user",
                    "instructor",
                    "coupon",
                    "total_paid",
                    "is_free",
                    "admin_commission",
                    "status",
                    "reject_reason",
                    "enroll",
                )
            },
        ),
    )
    add_fieldsets = (
        (
            "Create Order",
            {
                "classes": ("wide",),
                "fields": (
                    "course",
                    "user",
                    "instructor",
                    "coupon",
                    "total_paid",
                    "is_free",
                    "admin_commission",
                    "status",
                    "reject_reason",
                    "enroll",
                ),
            },
        ),
    )
    list_filter = ("is_free", "status")
    search_fields = ("course", "user", "instructor", "coupon")
    ordering = ("course",)
    filter_horizontal = ()


admin.site.register(Order, OrderModelAdmin)
