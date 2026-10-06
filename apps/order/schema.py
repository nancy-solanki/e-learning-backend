"""Payment wire contracts, kept separate from persistence serializers."""

from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers


class MakePaymentSerializer(serializers.Serializer):
    total_paid = serializers.FloatField(help_text="Amount in major currency units.")
    course = serializers.UUIDField()


@extend_schema_field(
    {
        "oneOf": [
            {
                "type": "object",
                "properties": {
                    "razorpay_order_id": {"type": "string"},
                    "razorpay_payment_id": {"type": "string"},
                    "razorpay_signature": {"type": "string"},
                },
                "required": [
                    "razorpay_order_id",
                    "razorpay_payment_id",
                    "razorpay_signature",
                ],
            },
            {
                "type": "string",
                "description": "Legacy JSON-encoded verification object.",
            },
        ]
    }
)
class PaymentVerificationField(serializers.JSONField):
    """The existing endpoint accepts both structured and JSON-encoded verification."""


class SuccessPaymentSerializer(MakePaymentSerializer):
    response = PaymentVerificationField(
        required=False,
        help_text=(
            "Required for paid courses. A JSON-encoded string is also "
            "accepted for legacy clients."
        ),
    )
    is_free = serializers.BooleanField(required=False, default=False)
    coupon = serializers.UUIDField(required=False, allow_null=True)


class PaymentResultSerializer(serializers.Serializer):
    data = serializers.CharField()


class RazorpayOrderSerializer(serializers.Serializer):
    id = serializers.CharField()
    amount = serializers.IntegerField(
        help_text="Amount in currency subunits (paise for INR)."
    )
    entity = serializers.CharField(required=False)
    currency = serializers.CharField(required=False)
    amount_paid = serializers.IntegerField(required=False)
    amount_due = serializers.IntegerField(required=False)
    status = serializers.CharField(required=False)
    attempts = serializers.IntegerField(required=False)
    receipt = serializers.CharField(required=False, allow_null=True)
    offer_id = serializers.CharField(required=False, allow_null=True)
    notes = serializers.JSONField(required=False)
    created_at = serializers.IntegerField(
        required=False, help_text="Unix timestamp in seconds."
    )
