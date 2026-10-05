from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import filters, generics, mixins, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .filters import OrderFilter
from .serializers import OrderSerializer
from .service import OrderService


class OrderFilteringMixin:
    filter_backends = (
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    )
    filterset_class = OrderFilter
    search_fields = (
        "id",
        "course__title",
        "user__username",
        "user__first_name",
        "user__last_name",
        "user__email",
        "instructor__username",
        "instructor__first_name",
        "instructor__last_name",
        "instructor__email",
        "coupon__code",
    )
    ordering_fields = ("created_at", "total_paid")
    ordering = ("-created_at",)


ORDER_FILTER_DESCRIPTION = (
    " Filter by status, is_free, course/user/instructor/coupon UUID, "
    "total_paid_min/max, or inclusive creation dates "
    "(created_at_after/before). Search by order ID, course title, username, "
    "name, email, or coupon code. Order by created_at or total_paid "
    "(prefix with '-' for descending)."
)


@extend_schema_view(
    get=extend_schema(
        tags=["Order"],
        description="Retrieve a list of orders for the authenticated user."
        + ORDER_FILTER_DESCRIPTION,
    ),
)
class OrderView(OrderFilteringMixin, mixins.ListModelMixin, generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = OrderSerializer

    def get_queryset(self):
        return OrderService.get_user_orders(self.request.user)

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)


@extend_schema_view(
    get=extend_schema(
        tags=["Order"], description="Retrieve details of a specific order by ID."
    ),
)
class SingleOrderView(mixins.RetrieveModelMixin, generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = OrderSerializer

    def get_queryset(self):
        return OrderService.get_user_orders(self.request.user)

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)


@extend_schema_view(
    get=extend_schema(
        tags=["Order (Instructor)"],
        description="Retrieve a list of orders for courses taught by the authenticated instructor."
        + ORDER_FILTER_DESCRIPTION,
    ),
)
class OrderInstructorView(
    OrderFilteringMixin, mixins.ListModelMixin, generics.GenericAPIView
):
    permission_classes = [IsAuthenticated]
    serializer_class = OrderSerializer

    def get_queryset(self):
        return OrderService.get_instructor_orders(self.request.user)

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)


@extend_schema_view(
    get=extend_schema(
        tags=["Order (Instructor)"],
        description="Retrieve details of a specific order taught by the instructor by ID.",
    ),
)
class SingleOrderInstructorView(mixins.RetrieveModelMixin, generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = OrderSerializer

    def get_queryset(self):
        return OrderService.get_instructor_orders(self.request.user)

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)


class MakePayment(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Payment"],
        description="Initiate a payment and create a Razorpay order.",
        request={"total_paid": float, "course": str},
        responses={201: dict, 400: dict},
    )
    def post(self, request, format=None):
        total_paid = request.data.get("total_paid")
        course_id = request.data.get("course")

        if not total_paid or not course_id:
            return Response(
                {"errors": ["Missing total_paid or course id"]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            payment = OrderService.create_razorpay_order(
                total_paid, course_id, request.user
            )
            return Response(payment, status=status.HTTP_201_CREATED)
        except ValueError as e:
            return Response({"errors": [str(e)]}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(
                {"errors": [str(e)]}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class SuccessPayment(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Payment"],
        description="Verify a successful payment and complete the order and enrollment.",
        request={
            "total_paid": float,
            "course": str,
            "response": dict,
            "is_free": bool,
            "coupon": str,
        },
        responses={200: dict, 400: dict},
    )
    def post(self, request, format=None):
        success, message = OrderService.process_successful_payment(
            request.data, request.user
        )

        if success:
            return Response({"data": message}, status=status.HTTP_200_OK)
        else:
            return Response({"error": message}, status=status.HTTP_400_BAD_REQUEST)
