from django.core.exceptions import ValidationError
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import filters, status, viewsets
from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.course.models import Course

from .filters import CouponFilter
from .serializers import CouponSerializer
from .service import CouponService


class IsInstructorOrReadOnly(BasePermission):
    """
    Permission to only allow instructors to create coupons for their courses,
    and admins to manage all.
    """

    def has_permission(self, request, view):
        if request.user.is_admin:
            return True
        if request.method == "POST":
            course_id = request.data.get("course")
            if not course_id:
                return False
            try:
                course = Course.objects.get(id=course_id)
                return request.user == course.instructor
            except (Course.DoesNotExist, ValidationError):
                return False
        return request.user.is_instructor


@extend_schema_view(
    list=extend_schema(
        tags=["Coupon"],
        description="List all coupons. Admin sees all, instructors see their own.",
    ),
    retrieve=extend_schema(
        tags=["Coupon"], description="Retrieve a specific coupon by UUID."
    ),
    create=extend_schema(tags=["Coupon"], description="Create a new coupon."),
    update=extend_schema(tags=["Coupon"], description="Update a coupon."),
    partial_update=extend_schema(
        tags=["Coupon"], description="Partial update of a coupon (instructor or owner)."
    ),
    destroy=extend_schema(
        tags=["Coupon"],
        description="Toggle deletion status (soft delete/restore) for a coupon.",
    ),
)
class CouponViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing coupons.
    """

    permission_classes = [IsAuthenticated, IsInstructorOrReadOnly]
    serializer_class = CouponSerializer
    filter_backends = (
        DjangoFilterBackend,
        filters.OrderingFilter,
        filters.SearchFilter,
    )
    filterset_class = CouponFilter
    search_fields = ("code", "course__title", "course__short_description")
    ordering_fields = ("created_at", "expired_at", "value", "limit", "used")
    ordering = ("-created_at",)

    def get_queryset(self):
        return CouponService.get_coupons(self.request.user)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        message = CouponService.toggle_coupon_status(instance)
        return Response({"message": message}, status=status.HTTP_200_OK)


@extend_schema_view(
    get=extend_schema(
        tags=["Coupon"], description="Retrieve and validate a coupon by its code."
    ),
)
class GetCoupon(APIView):
    """
    API View to retrieve and validate a coupon by its code.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, code, format=None):
        coupon, error = CouponService.validate_coupon(code)
        if error:
            return Response({"errors": [error]}, status=status.HTTP_404_NOT_FOUND)

        serializer = CouponSerializer(coupon)
        return Response(serializer.data, status=status.HTTP_200_OK)
