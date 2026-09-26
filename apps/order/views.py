from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import generics, mixins, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import OrderSerializer
from .service import OrderService


@extend_schema_view(
    get=extend_schema(
        tags=["Order"],
        description="Retrieve a list of orders for the authenticated user.",
    ),
)
class OrderView(mixins.ListModelMixin, generics.GenericAPIView):
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
        description="Retrieve a list of orders for courses taught by the authenticated instructor.",
    ),
)
class OrderInstructorView(mixins.ListModelMixin, generics.GenericAPIView):
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
