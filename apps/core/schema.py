"""Shared OpenAPI conventions. No runtime records are used as documentation."""

from drf_spectacular.openapi import AutoSchema
from rest_framework import serializers


class MessageSerializer(serializers.Serializer):
    message = serializers.CharField(read_only=True)


class DetailSerializer(serializers.Serializer):
    detail = serializers.CharField(read_only=True)


class ErrorSerializer(serializers.Serializer):
    error = serializers.CharField(read_only=True)


class ErrorsSerializer(serializers.Serializer):
    errors = serializers.ListField(child=serializers.CharField(), read_only=True)


class ApplicationSchema(AutoSchema):
    """Consistent metadata and standard DRF errors across all operations."""

    def get_summary(self):
        return self.get_operation_id().replace("_", " ").capitalize()

    def get_description(self):
        description = super().get_description()
        if description:
            return description
        return self.get_summary() + "."

    def get_tags(self):
        resource = self.path.strip("/").split("/")[2]
        return [
            {"auth": "Authentication", "users": "Users"}.get(
                resource, resource.replace("-", " ").title()
            )
        ]

    def get_operation(self, *args, **kwargs):
        operation = super().get_operation(*args, **kwargs)
        if operation is None:
            return None
        responses = operation["responses"]
        detail = self.resolve_serializer(DetailSerializer(), "response").ref
        if operation.get("security"):
            for code, description in (
                ("401", "Authentication required or invalid credentials."),
                ("403", "Permission denied."),
            ):
                responses.setdefault(
                    code,
                    {
                        "description": description,
                        "content": {"application/json": {"schema": detail}},
                    },
                )
        if "{" in self.path:
            responses.setdefault(
                "404",
                {
                    "description": "Resource not found or outside the caller's scope.",
                    "content": {"application/json": {"schema": detail}},
                },
            )
        if self.method in ("POST", "PUT", "PATCH") or any(
            p["in"] == "query" for p in operation.get("parameters", [])
        ):
            responses.setdefault(
                "400",
                {
                    "description": (
                        "Validation error. Keys identify fields or non_field_errors; "
                        "values contain error details."
                    ),
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "additionalProperties": {
                                    "oneOf": [
                                        {"type": "string"},
                                        {"type": "array", "items": {"type": "string"}},
                                        {"type": "object", "additionalProperties": {}},
                                    ]
                                },
                            }
                        }
                    },
                },
            )
        return operation


def order_status_choices():
    from apps.order.models import Order

    return Order.STATUS.choices


def transaction_status_choices():
    from apps.transaction.models import Transaction

    return Transaction.STATUS.choices


def course_status_choices():
    from apps.course.models import Course

    return Course.Status.choices


def content_status_choices():
    from apps.section.models import Section

    return Section.Status.choices
