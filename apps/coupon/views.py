from django.core.exceptions import ValidationError
from django.http import Http404
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import filters, status, viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.schema import ErrorsSerializer, MessageSerializer
from apps.course.models import Course

from .filters import CouponFilter
from .models import Coupon
from .pagination import CouponPagination
from .serializers import CouponSerializer
from .service import CouponService


class IsInstructorOrReadOnly(BasePermission):
    """
    Permission to only allow instructors to create coupons for their courses,
    and admins to manage all.
    """

    def has_permission(self, request, view):
        user = request.user
        if user.is_admin:
            return True
        if not user.is_authenticated or not user.is_instructor:
            return False
        if request.method == "POST":
            course_id = request.data.get("course")
            if not course_id:
                return False
            try:
                course = Course.objects.get(id=course_id)
                return user == course.instructor
            except (Course.DoesNotExist, ValidationError):
                return False
        return True


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
        responses={200: MessageSerializer},
    ),
)
class CouponViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing coupons.
    """

    permission_classes = [IsAuthenticated, IsInstructorOrReadOnly]
    serializer_class = CouponSerializer
    queryset = Coupon.objects.none()
    pagination_class = CouponPagination
    filter_backends = (
        DjangoFilterBackend,
        filters.OrderingFilter,
        filters.SearchFilter,
    )
    filterset_class = CouponFilter
    search_fields = ("code", "course__title", "course__short_description")
    ordering_fields = ("code", "created_at", "expired_at", "value", "limit", "used")
    ordering = ("-created_at", "-id")

    def get_queryset(self):
        return CouponService.get_coupons(self.request.user).select_related("course")

    def perform_create(self, serializer):
        if not self.request.user.is_admin:
            course = serializer.validated_data["course"]
            if course.instructor_id != self.request.user.pk:
                raise PermissionDenied(
                    "You can only create coupons for your own courses."
                )
            serializer.save(is_instructor_created=True)
            return
        serializer.save()

    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
        except Http404 as exc:
            # Admins can call DELETE again to restore a soft-deleted coupon;
            # deleted coupons remain hidden from ordinary list/detail queries.
            if not request.user.is_admin:
                raise
            instance = Coupon.objects.filter(pk=kwargs.get(self.lookup_field)).first()
            if instance is None:
                raise exc
            self.check_object_permissions(request, instance)
        message = CouponService.toggle_coupon_status(instance)
        return Response({"message": message}, status=status.HTTP_200_OK)


@extend_schema_view(
    get=extend_schema(
        tags=["Coupon"],
        description="Retrieve and validate a coupon by its code.",
        responses={200: CouponSerializer, 404: ErrorsSerializer},
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
