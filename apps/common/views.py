from django.db.models import Count, Sum
from django.db.models.functions import TruncDate
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.permission import IsSuperuser
from apps.course.models import Course
from apps.enroll.models import Enroll
from apps.order.models import Order
from apps.users.models import User
from apps.wallet.models import Wallet


@extend_schema(
    tags=["Admin Dashboard"],
    description=(
        "Returns aggregate statistics for the admin dashboard: "
        "total users, instructors, courses, enrollments, and revenue figures."
    ),
    responses={200: dict},
)
class AdminDashboardStatsView(APIView):
    permission_classes = (IsSuperuser,)

    def get(self, request):
        # Users & instructors
        total_users = User.objects.filter(deleted_at__isnull=True).count()
        total_instructors = User.objects.filter(
            deleted_at__isnull=True, groups__name="instructor"
        ).count()

        # Courses (all, not soft-deleted)
        total_courses = Course.objects.filter(deleted_at__isnull=True).count()

        # Enrollments
        total_enrollments = Enroll.objects.filter(deleted_at__isnull=True).count()

        # Revenue — sum of total_paid on successful orders
        revenue_qs = Order.objects.filter(
            deleted_at__isnull=True, status=Order.STATUS.SUCCESS
        ).aggregate(total=Sum("total_paid"))
        total_revenue = round(revenue_qs["total"] or 0.0, 2)

        # Site wallet for current_earnings / total_earnings
        site_wallet = Wallet.objects.filter(
            is_site_wallet=True, deleted_at__isnull=True
        ).first()

        current_earnings = float(site_wallet.current_earnings) if site_wallet else 0.0
        total_earnings = (
            float(site_wallet.total_earnings) if site_wallet else total_revenue
        )

        return Response(
            {
                "total_users": total_users,
                "total_instructors": total_instructors,
                "total_courses": total_courses,
                "total_enrollments": total_enrollments,
                "total_revenue": total_revenue,
                "current_earnings": current_earnings,
                "total_earnings": total_earnings,
            }
        )


@extend_schema(
    tags=["Admin Dashboard"],
    description=(
        "Returns time-series chart data for the admin dashboard: "
        "daily order/enrollment counts and daily new user registrations "
        "for the last 30 days. Dates are in YYYY-MM-DD format."
    ),
    responses={200: dict},
)
class AdminDashboardChartsView(APIView):
    permission_classes = (IsSuperuser,)

    def get(self, request):
        # Default: last 30 days
        since = timezone.now() - timezone.timedelta(days=30)

        # Daily orders (successful)
        orders_qs = (
            Order.objects.filter(
                deleted_at__isnull=True,
                status=Order.STATUS.SUCCESS,
                created_at__gte=since,
            )
            .annotate(date=TruncDate("created_at"))
            .values("date")
            .annotate(count=Count("id"))
            .order_by("date")
        )

        orders_data = [
            {"date": entry["date"].strftime("%Y-%m-%d"), "count": entry["count"]}
            for entry in orders_qs
        ]

        # Daily new users
        users_qs = (
            User.objects.filter(
                deleted_at__isnull=True,
                created_at__gte=since,
            )
            .annotate(date=TruncDate("created_at"))
            .values("date")
            .annotate(count=Count("id"))
            .order_by("date")
        )

        users_data = [
            {"date": entry["date"].strftime("%Y-%m-%d"), "count": entry["count"]}
            for entry in users_qs
        ]

        return Response(
            {
                "orders": orders_data,
                "users": users_data,
            }
        )
