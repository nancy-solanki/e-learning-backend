from datetime import date, datetime, time, timedelta
from datetime import timezone as datetime_timezone
from decimal import ROUND_HALF_UP, Decimal

from django.db.models import Avg, Count, Q, Sum
from django.db.models.functions import TruncDate, TruncMonth, TruncYear
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.permission import IsInstructorOrAdmin, IsSuperuser
from apps.course.models import Course
from apps.enroll.models import Enroll
from apps.order.models import Order
from apps.rating.models import Rating
from apps.users.models import User
from apps.wallet.models import Wallet, WalletEntry

from .schema import (
    AdminDashboardSerializer,
    DashboardChartsSerializer,
    DashboardStatsSerializer,
    InstructorDashboardSerializer,
)


@extend_schema(
    tags=["Admin Dashboard"],
    summary="Retrieve admin dashboard data",
    description=(
        "Returns platform-wide dashboard metrics, time-series trends, course "
        "status counts, and recent orders. Requires administrator access."
    ),
    responses={200: AdminDashboardSerializer},
)
class AdminDashboardView(APIView):
    """Platform-wide dashboard data for authenticated administrators."""

    permission_classes = (IsSuperuser,)

    def get(self, request):
        period = request.query_params.get("period", "daily")
        if period not in {"daily", "monthly", "yearly"}:
            return Response({"period": ["Use daily, monthly, or yearly."]}, status=400)

        # A single UTC instant controls both the headline windows and chart buckets.
        as_of = timezone.now().astimezone(datetime_timezone.utc)
        since_30d = as_of - timedelta(days=30)
        users = User.objects.filter(deleted_at__isnull=True)
        courses = Course.objects.filter(deleted_at__isnull=True)
        enrollments = Enroll.objects.filter(deleted_at__isnull=True)
        orders = Order.objects.filter(deleted_at__isnull=True)
        successful_paid_orders = orders.filter(
            status=Order.STATUS.SUCCESS, is_free=False
        )

        def buckets_for_period():
            current = as_of.date()
            if period == "daily":
                first = current - timedelta(days=29)
                return [first + timedelta(days=i) for i in range(30)], TruncDate
            if period == "monthly":
                current_month = current.replace(day=1)
                values = []
                for offset in range(11, -1, -1):
                    index = current_month.year * 12 + current_month.month - 1 - offset
                    year, month = divmod(index, 12)
                    values.append(date(year, month + 1, 1))
                return values, TruncMonth
            return [date(current.year - i, 1, 1) for i in range(4, -1, -1)], TruncYear

        bucket_dates, truncator = buckets_for_period()
        start_date = bucket_dates[0]
        if period == "daily":
            start = datetime.combine(start_date, time.min, tzinfo=datetime_timezone.utc)
            end = as_of
            date_format = "%Y-%m-%d"
        elif period == "monthly":
            start = datetime.combine(start_date, time.min, tzinfo=datetime_timezone.utc)
            next_month = bucket_dates[-1]
            end = datetime(
                next_month.year + (next_month.month == 12),
                1 if next_month.month == 12 else next_month.month + 1,
                1,
                tzinfo=datetime_timezone.utc,
            )
            date_format = "%Y-%m"
        else:
            start = datetime.combine(start_date, time.min, tzinfo=datetime_timezone.utc)
            end = datetime(
                bucket_dates[-1].year + 1, 1, 1, tzinfo=datetime_timezone.utc
            )
            date_format = "%Y"

        def key_for_bucket(value):
            if isinstance(value, datetime):
                value = value.date()
            if period == "daily":
                return value
            if period == "monthly":
                return date(value.year, value.month, 1)
            return date(value.year, 1, 1)

        def truncated(field_name):
            if period == "daily":
                return TruncDate(field_name, tzinfo=datetime_timezone.utc)
            return truncator(field_name, tzinfo=datetime_timezone.utc)

        trend_orders = successful_paid_orders.filter(created_at__gte=start)
        trend_enrollments = enrollments.filter(created_at__gte=start)
        if period == "daily":
            trend_orders = trend_orders.filter(created_at__lte=as_of)
            trend_enrollments = trend_enrollments.filter(created_at__lte=as_of)
        else:
            trend_orders = trend_orders.filter(created_at__lt=end)
            trend_enrollments = trend_enrollments.filter(created_at__lt=end)

        enrollment_counts = {
            key_for_bucket(row["bucket"]): row["count"]
            for row in trend_enrollments.annotate(bucket=truncated("created_at"))
            .values("bucket")
            .annotate(count=Count("id"))
        }
        if period == "daily":
            revenue_totals = {}
            for order in trend_orders.values("created_at", "total_paid"):
                bucket = timezone.localtime(
                    order["created_at"], datetime_timezone.utc
                ).date()
                revenue_totals[bucket] = revenue_totals.get(
                    bucket, Decimal("0.00")
                ) + Decimal(str(order["total_paid"]))
        else:
            revenue_totals = {
                key_for_bucket(row["bucket"]): row["total"]
                for row in trend_orders.annotate(
                    bucket=truncator("created_at", tzinfo=datetime_timezone.utc)
                )
                .values("bucket")
                .annotate(total=Sum("total_paid"))
            }

        def money(value):
            return str(
                Decimal(str(value or 0)).quantize(
                    Decimal("0.01"), rounding=ROUND_HALF_UP
                )
            )

        revenue_total = successful_paid_orders.aggregate(total=Sum("total_paid"))[
            "total"
        ]
        status_counts = {
            row["status"]: row["count"]
            for row in courses.values("status").annotate(count=Count("id"))
        }
        currency = (
            Wallet.objects.filter(is_site_wallet=True, deleted_at__isnull=True)
            .values_list("currency", flat=True)
            .first()
            or "INR"
        )
        recent_orders = []
        for order in orders.select_related("user", "course").order_by(
            "-created_at", "-id"
        )[:5]:
            recent_orders.append(
                {
                    "id": str(order.id),
                    "user_name": f"{order.user.first_name} {order.user.last_name}".strip(),
                    "course_title": order.course.title if order.course_id else None,
                    "status": order.status,
                    "is_free": order.is_free,
                    "total_paid": money(order.total_paid),
                    "created_at": order.created_at,
                }
            )

        return Response(
            {
                "metrics": {
                    # Includes all account types, including staff/admin accounts.
                    "total_users": users.count(),
                    "active_learners": users.filter(
                        is_active=True,
                        status=User.Status.ACTIVE,
                        groups__name="student",
                    )
                    .distinct()
                    .count(),
                    "instructors": users.filter(
                        is_active=True,
                        status=User.Status.ACTIVE,
                        groups__name="instructor",
                    )
                    .distinct()
                    .count(),
                    "total_courses": courses.count(),
                    "published_courses": courses.filter(
                        status=Course.Status.PUBLISHED
                    ).count(),
                    "total_enrollments": enrollments.count(),
                    "enrollments_30d": enrollments.filter(
                        created_at__gte=since_30d, created_at__lte=as_of
                    ).count(),
                    "gross_revenue": money(revenue_total),
                    "orders_30d": orders.filter(
                        created_at__gte=since_30d, created_at__lte=as_of
                    ).count(),
                },
                "currency": currency,
                "as_of": as_of.isoformat().replace("+00:00", "Z"),
                "enrollment_trend": [
                    {
                        "date": bucket.strftime(date_format),
                        "count": enrollment_counts.get(key_for_bucket(bucket), 0),
                    }
                    for bucket in bucket_dates
                ],
                "revenue_trend": [
                    {
                        "date": bucket.strftime(date_format),
                        "amount": money(revenue_totals.get(key_for_bucket(bucket))),
                    }
                    for bucket in bucket_dates
                ],
                "course_status_counts": [
                    {"status": status, "count": status_counts.get(status, 0)}
                    for status in Course.Status.values
                ]
                + [
                    {"status": status, "count": count}
                    for status, count in status_counts.items()
                    if status not in Course.Status.values
                ],
                "recent_orders": recent_orders,
            }
        )


@extend_schema(
    tags=["Admin Dashboard"],
    description=(
        "Returns aggregate statistics for the admin dashboard: "
        "total users, instructors, courses, enrollments, and revenue figures."
    ),
    responses={200: DashboardStatsSerializer},
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
    responses={200: DashboardChartsSerializer},
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


@extend_schema(
    tags=["Instructor Dashboard"],
    description="Returns dashboard metrics and activity for the authenticated instructor.",
    responses={200: InstructorDashboardSerializer},
)
class InstructorDashboardView(APIView):
    permission_classes = (IsAuthenticated, IsInstructorOrAdmin)

    def get(self, request):
        instructor = request.user
        since = timezone.now() - timezone.timedelta(days=30)
        courses = Course.objects.filter(instructor=instructor, deleted_at__isnull=True)
        enrollments = Enroll.objects.filter(
            course__instructor=instructor,
            course__deleted_at__isnull=True,
            deleted_at__isnull=True,
        )
        ratings = Rating.objects.filter(
            course__instructor=instructor,
            course__deleted_at__isnull=True,
            deleted_at__isnull=True,
        )

        metrics = {
            "published_courses": courses.filter(status=Course.Status.PUBLISHED).count(),
            "total_students": enrollments.values("user_id").distinct().count(),
            "average_rating": ratings.aggregate(value=Avg("rating"))["value"],
            "new_students_30d": enrollments.filter(created_at__gte=since)
            .values("user_id")
            .distinct()
            .count(),
        }
        enrollment_trend = (
            enrollments.filter(created_at__gte=since)
            .annotate(date=TruncDate("created_at"))
            .values("date")
            .annotate(count=Count("id"))
            .order_by("date")
        )

        today = timezone.localdate()
        first_date = today - timezone.timedelta(days=29)
        earning_totals = {
            row["date"]: row["total"]
            for row in WalletEntry.objects.filter(
                wallet__user=instructor,
                wallet__deleted_at__isnull=True,
                wallet__is_site_wallet=False,
                type=WalletEntry.Kind.EARNING,
                status=WalletEntry.Status.COMPLETED,
                completed_at__date__gte=first_date,
                completed_at__date__lte=today,
            )
            .annotate(date=TruncDate("completed_at"))
            .values("date")
            .annotate(total=Sum("amount"))
        }
        course_earnings = [
            {
                "date": (first_date + timezone.timedelta(days=offset)).isoformat(),
                "amount": str(
                    earning_totals.get(
                        first_date + timezone.timedelta(days=offset), Decimal("0.00")
                    )
                ),
            }
            for offset in range(30)
        ]

        top_courses = []
        for course in (
            courses.annotate(
                student_count=Count(
                    "enroll",
                    filter=Q(enroll__deleted_at__isnull=True),
                    distinct=True,
                ),
                average_rating=Avg(
                    "rating__rating", filter=Q(rating__deleted_at__isnull=True)
                ),
            )
            .select_related("thumbnail")
            .order_by("-student_count", "title", "id")[:5]
        ):
            top_courses.append(
                {
                    "id": str(course.id),
                    "title": course.title,
                    "slug": course.slug,
                    "thumbnail_url": (
                        course.thumbnail.url if course.thumbnail_id else None
                    ),
                    "status": course.status,
                    "student_count": course.student_count,
                    "average_rating": course.average_rating,
                    "updated_at": course.updated_at,
                }
            )

        recent_ratings = [
            {
                "id": str(rating.id),
                "course_title": rating.course.title,
                "student_name": f"{rating.user.first_name} {rating.user.last_name}".strip(),
                "rating": rating.rating,
                "comment": rating.comment or None,
                "created_at": rating.created_at,
            }
            for rating in ratings.select_related("course", "user").order_by(
                "-created_at", "-id"
            )[:5]
        ]
        return Response(
            {
                "instructor": {"first_name": instructor.first_name},
                "metrics": metrics,
                "enrollment_trend": [
                    {"date": row["date"].strftime("%Y-%m-%d"), "count": row["count"]}
                    for row in enrollment_trend
                ],
                "course_earnings": course_earnings,
                "top_courses": top_courses,
                "recent_ratings": recent_ratings,
            }
        )
