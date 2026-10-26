from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from apps.course.models import Course
from apps.enroll.models import Enroll
from apps.rating.models import Rating
from apps.users.models import User

TARGET_RATING_COUNT = 58
DEMO_COMMENT_PREFIX = "[Demo rating "
COMMENTS = (
    "Clear explanations and a well-structured course.",
    "The lessons were useful and easy to follow.",
    "Good examples helped me understand the topic.",
    "A helpful course with practical material.",
    "Enjoyed the content and learned a lot.",
    "The course covered the fundamentals thoroughly.",
)
RESPONSES = (
    "Thanks for sharing your feedback!",
    "Glad you found the course helpful.",
    "Thank you for taking the time to review the course.",
)
RATINGS = tuple(Decimal(value) for value in ("3.0", "3.5", "4.0", "4.5", "5.0"))


class Command(BaseCommand):
    help = "Create 58 demo ratings from active learner enrollments."

    def add_arguments(self, parser):
        parser.add_argument(
            "--create-demo-enrollments",
            action="store_true",
            help="Create unusable-password demo learners and enrollments if needed.",
        )

    def handle(self, *args, **options):
        with transaction.atomic():
            demo_ratings = list(
                Rating.objects.filter(
                    deleted_at__isnull=True,
                    comment__startswith=DEMO_COMMENT_PREFIX,
                ).order_by("created_at", "pk")
            )
            if len(demo_ratings) >= TARGET_RATING_COUNT:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Already have {len(demo_ratings)} active demo ratings; "
                        "no ratings added."
                    )
                )
                return

            remaining = TARGET_RATING_COUNT - len(demo_ratings)
            rated_pairs = set(
                Rating.objects.filter(deleted_at__isnull=True).values_list(
                    "user_id", "course_id"
                )
            )
            available_enrollments = []
            seen_pairs = set()
            enrollments = (
                Enroll.objects.filter(
                    deleted_at__isnull=True,
                    user__is_active=True,
                    user__status="AC",
                )
                .exclude(user__is_superuser=True)
                .exclude(user__groups__name__in=("admin", "instructor"))
                .select_related("user", "course")
                .order_by("created_at", "pk")
                .distinct()
            )
            for enrollment in enrollments:
                pair = (enrollment.user_id, enrollment.course_id)
                if pair in rated_pairs or pair in seen_pairs:
                    continue
                seen_pairs.add(pair)
                available_enrollments.append(enrollment)

            if len(available_enrollments) < remaining:
                if not options["create_demo_enrollments"]:
                    raise CommandError(
                        f"Cannot create {TARGET_RATING_COUNT} active demo ratings: "
                        f"{len(demo_ratings)} already exist and only "
                        f"{len(available_enrollments)} additional eligible, unrated "
                        "learner/course enrollments are available. Add enrollments "
                        "or rerun with --create-demo-enrollments."
                    )
                available_enrollments = self._create_demo_enrollments(
                    available_enrollments, rated_pairs, remaining
                )

            now = timezone.now()
            for index, enrollment in enumerate(
                available_enrollments, start=len(demo_ratings) + 1
            ):
                comment = COMMENTS[(index - 1) % len(COMMENTS)]
                Rating.objects.create(
                    user=enrollment.user,
                    course=enrollment.course,
                    rating=RATINGS[(index - 1) % len(RATINGS)],
                    comment=f"{DEMO_COMMENT_PREFIX}{index:03d}] {comment}",
                    response=(
                        RESPONSES[(index - 1) % len(RESPONSES)]
                        if index % 2 == 0
                        else None
                    ),
                    created_at=now - timedelta(days=(index * 3) % 90),
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"Created {remaining} demo ratings; "
                f"{TARGET_RATING_COUNT} active demo ratings are now available."
            )
        )

    def _create_demo_enrollments(self, available_enrollments, rated_pairs, target):
        courses = list(
            Course.objects.filter(
                deleted_at__isnull=True,
                instructor__is_active=True,
            ).order_by("pk")
        )
        if not courses:
            raise CommandError(
                "Cannot create demo enrollments because no active courses with "
                "active instructors are available."
            )

        enrolled_pairs = set(
            Enroll.objects.filter(deleted_at__isnull=True).values_list(
                "user_id", "course_id"
            )
        )
        demo_user_index = 1
        while len(available_enrollments) < target:
            email = f"demo.rater.{demo_user_index:03d}@example.test"
            username = f"demo_rater_{demo_user_index:03d}"
            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    "username": username,
                    "first_name": "Demo",
                    "last_name": f"Learner {demo_user_index:03d}",
                    "status": User.Status.ACTIVE,
                    "gender": User.Gender.FEMALE,
                    "is_active": True,
                },
            )
            if created:
                user.set_unusable_password()
                user.save(update_fields=["password"])
            elif (
                not user.is_active
                or user.status != User.Status.ACTIVE
                or user.is_admin
                or user.is_instructor
            ):
                raise CommandError(
                    f"Cannot use {email} as a demo learner because the existing "
                    "account is not an active student."
                )

            for course in courses:
                pair = (user.pk, course.pk)
                if pair in enrolled_pairs or pair in rated_pairs:
                    continue
                enrollment = Enroll.objects.create(user=user, course=course)
                enrolled_pairs.add(pair)
                available_enrollments.append(enrollment)
                if len(available_enrollments) == target:
                    break
            demo_user_index += 1

        return available_enrollments
