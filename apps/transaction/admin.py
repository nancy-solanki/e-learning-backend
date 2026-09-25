from django.contrib import admin

from .models import Transaction


class TransactionModelAdmin(admin.ModelAdmin):
    # The fields to be used in displaying the Transaction model.
    list_display = (
        "id",
        "user",
        "wallet",
        "amount",
        "transaction_type",
        "status",
        "created_at",
    )
    fieldsets = (
        (
            "Transaction Info",
            {
                "fields": (
                    "user",
                    "wallet",
                    "amount",
                    "transaction_type",
                    "status",
                    "description",
                    "tx_id",
                )
            },
        ),
    )
    add_fieldsets = (
        (
            "Create Transaction",
            {
                "classes": ("wide",),
                "fields": (
                    "user",
                    "wallet",
                    "amount",
                    "transaction_type",
                    "status",
                    "description",
                    "tx_id",
                ),
            },
        ),
    )
    list_filter = ("transaction_type", "status", "created_at")
    search_fields = ("user__email", "tx_id", "description")
    ordering = ("-created_at",)
    filter_horizontal = ()


admin.site.register(Transaction, TransactionModelAdmin)
