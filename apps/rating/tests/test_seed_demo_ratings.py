from io import StringIO

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from apps.enroll.models import Enroll
from apps.rating.models import Rating
from apps.users.models import User
from apps.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


def test_seed_demo_ratings_creates_58_and_is_idempotent(course):
    learners = UserFactory.create_batch(58)
    Enroll.objects.bulk_create(
        [Enroll(user=learner, course=course) for learner in learners]
    )

    call_command("seed_demo_ratings", stdout=StringIO())

    seeded = Rating.objects.filter(comment__startswith="[Demo rating ")
    assert seeded.count() == 58
    assert seeded.values("user_id", "course_id").distinct().count() == 58

    call_command("seed_demo_ratings", stdout=StringIO())
    assert seeded.count() == 58


def test_seed_demo_ratings_fails_without_enough_eligible_enrollments(course):
    learners = UserFactory.create_batch(57)
    Enroll.objects.bulk_create(
        [Enroll(user=learner, course=course) for learner in learners]
    )

    with pytest.raises(CommandError, match="only 57 additional eligible"):
        call_command("seed_demo_ratings", stdout=StringIO())

    assert not Rating.objects.exists()


def test_seed_demo_ratings_can_create_missing_demo_enrollments(course):
    learners = UserFactory.create_batch(57)
    Enroll.objects.bulk_create(
        [Enroll(user=learner, course=course) for learner in learners]
    )

    call_command(
        "seed_demo_ratings",
        "--create-demo-enrollments",
        stdout=StringIO(),
    )

    assert Rating.objects.filter(comment__startswith="[Demo rating ").count() == 58
    demo_user = User.objects.get(email="demo.rater.001@example.test")
    assert not demo_user.has_usable_password()
    assert Enroll.objects.filter(user=demo_user, course=course).exists()
