from decimal import Decimal

from django.db.models import Avg, Count, Q, Sum
from django.db.models.functions import TruncDate
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
    DashboardChartsSerializer,
    DashboardStatsSerializer,
    InstructorDashboardSerializer,
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
