from apps.core.email_notifications import queue_notification_email
from apps.enroll.models import Enroll
from apps.users.models import User


def notify_coupon_audience(coupon, *, event: str):
    if event == "expiring":
        subject = f"Coupon {coupon.code} expires soon"
        title = "A coupon you may like expires soon"
        message = (
            f'Coupon "{coupon.code}" for "{coupon.course.title}" expires on '
            f"{coupon.expired_at.isoformat()}."
        )
    elif event == "created":
        subject = f"New offer for {coupon.course.title}"
        title = "A new course offer is available"
        message = (
            f'Use coupon "{coupon.code}" for "{coupon.course.title}" before '
            f"{coupon.expired_at.isoformat()}."
        )
    elif event == "removed":
        subject = f"Offer ended for {coupon.course.title}"
        title = "A course offer is no longer available"
        message = f'The offer "{coupon.code}" for "{coupon.course.title}" has ended.'
    elif event == "restored":
        subject = f"Offer available again for {coupon.course.title}"
        title = "A course offer is available again"
        message = (
            f'Coupon "{coupon.code}" for "{coupon.course.title}" is available '
            f"until {coupon.expired_at.isoformat()}."
        )
    else:
        subject = f"Offer updated for {coupon.course.title}"
        title = "A course offer was updated"
        message = (
            f'The terms for coupon "{coupon.code}" on "{coupon.course.title}" '
            "have changed. Review the offer before using it."
        )

    audience = User.objects.filter(
        is_active=True,
        status=User.Status.ACTIVE,
        promotional_emails=True,
    )
    # Coupons are attached to a course, so target that course's enrolled
    # learners instead of broadcasting offers to every opted-in account.
    if not coupon.is_global:
        enrolled_user_ids = Enroll.objects.filter(
            course=coupon.course,
            deleted_at__isnull=True,
        ).values_list("user_id", flat=True)
        audience = audience.filter(pk__in=enrolled_user_ids)
    for user in audience.iterator(chunk_size=500):
        queue_notification_email(
            user,
            subject=subject,
            title=title,
            message=message,
            preference_field="promotional_emails",
        )
