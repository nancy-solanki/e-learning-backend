import pytest
from django.db import transaction

from apps.core.email_notifications import queue_notification_email
from apps.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db(transaction=True)


def test_notification_waits_for_commit(mocker):
    enqueue = mocker.patch("apps.core.email_notifications.send_templated_email.delay")
    user = UserFactory(email_notifications=True)

    with transaction.atomic():
        assert queue_notification_email(
            user,
            subject="Course update",
            title="Course update",
            message="A course changed.",
        )
        enqueue.assert_not_called()

    enqueue.assert_called_once_with(
        "Course update",
        user.email,
        "notification.html",
        {"title": "Course update", "message": "A course changed."},
    )


def test_opted_out_user_does_not_receive_preference_based_email(mocker):
    enqueue = mocker.patch("apps.core.email_notifications.send_templated_email.delay")
    user = UserFactory(email_notifications=False)

    assert not queue_notification_email(
        user,
        subject="Course update",
        title="Course update",
        message="A course changed.",
    )
    enqueue.assert_not_called()


def test_essential_email_ignores_preference_and_queue_failure_is_nonfatal(mocker):
    enqueue = mocker.patch(
        "apps.core.email_notifications.send_templated_email.delay",
        side_effect=RuntimeError("broker unavailable"),
    )
    user = UserFactory(email_notifications=False)

    assert queue_notification_email(
        user,
        subject="Account suspended",
        title="Account suspended",
        message="Your account was suspended.",
        preference_required=False,
    )
    enqueue.assert_called_once()


def test_missing_email_is_not_queued(mocker):
    enqueue = mocker.patch("apps.core.email_notifications.send_templated_email.delay")
    user = UserFactory(email="")

    assert not queue_notification_email(
        user,
        subject="Course update",
        title="Course update",
        message="A course changed.",
    )
    enqueue.assert_not_called()
