from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

from config.celery import celery_app


@celery_app.task
def send_email(data: dict) -> None:
    """
    Send a plain-text or HTML email.

    Expected ``data`` keys:
        - subject   (str)
        - body      (str) – plain-text fallback
        - to_email  (str)
        - html_body (str, optional) – if supplied, sent as the HTML alternative
    """
    from_email = settings.DEFAULT_FROM_EMAIL

    msg = EmailMultiAlternatives(
        subject=data["subject"],
        body=data.get("body", ""),
        from_email=from_email,
        to=[data["to_email"]],
    )

    html_body = data.get("html_body")
    if html_body:
        msg.attach_alternative(html_body, "text/html")

    msg.send()


@celery_app.task
def send_templated_email(
    subject: str,
    to_email: str,
    template_name: str,
    context: dict | None = None,
) -> None:
    """
    Render a Django HTML template and send it as an email.

    Templates are resolved from ``templates/emails/<template_name>``.

    Args:
        subject:       Email subject line.
        to_email:      Recipient address.
        template_name: Template file relative to ``templates/emails/``,
                       e.g. ``"welcome.html"``.
        context:       Template context variables.
    """
    template_path = f"{settings.EMAIL_TEMPLATE_DIR}/{template_name}"
    ctx = context or {}

    html_body = render_to_string(template_path, ctx)
    # Strip tags for the plain-text fallback
    from django.utils.html import strip_tags

    plain_body = strip_tags(html_body)

    from_email = settings.DEFAULT_FROM_EMAIL

    msg = EmailMultiAlternatives(
        subject=subject,
        body=plain_body,
        from_email=from_email,
        to=[to_email],
    )
    msg.attach_alternative(html_body, "text/html")
    msg.send()
