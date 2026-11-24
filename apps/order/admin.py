from django.contrib import admin

from apps.core.email_notifications import queue_notification_email

from .models import Order

# Register your models here.


class OrderModelAdmin(admin.ModelAdmin):

    def save_model(self, request, obj, form, change):
        previous_status = None
        if change:
            previous_status = (
                Order.objects.filter(pk=obj.pk).values_list("status", flat=True).first()
            )
        super().save_model(request, obj, form, change)
        if obj.status == Order.STATUS.REJECTED and previous_status != obj.status:
            reason = f" Reason: {obj.reject_reason}" if obj.reject_reason else ""
            queue_notification_email(
                obj.user,
                subject=f"Order rejected: {obj.course.title}",
                title="Your order was rejected",
                message=(
                    f'Your order for "{obj.course.title}" was rejected.{reason} '
                    "Contact support if you need help."
                ),
                preference_required=False,
            )

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
