import pytest
from django.core import mail

from apps.core.services import send_email, send_templated_email


@pytest.mark.parametrize("html", [None, "<p>Hello</p>"])
def test_send_email(mailoutbox, settings, html):
    settings.DEFAULT_FROM_EMAIL = "sender@example.com"
    data = {"subject": "Welcome", "body": "Hello", "to_email": "user@example.com"}
    if html:
        data["html_body"] = html
    send_email.run(data)
    assert len(mailoutbox) == 1
    message = mailoutbox[0]
    assert message.subject == "Welcome"
    assert message.from_email == "sender@example.com"
    assert message.to == ["user@example.com"]
    assert message.body == "Hello"
    assert message.alternatives == ([(html, "text/html")] if html else [])


def test_send_email_without_body(mailoutbox):
    send_email.run({"subject": "Welcome", "to_email": "user@example.com"})
    assert mailoutbox[0].body == ""


@pytest.mark.parametrize("missing", ["subject", "to_email"])
def test_missing_required_email_data(missing, mailoutbox):
    data = {"subject": "Welcome", "to_email": "user@example.com"}
    del data[missing]
    with pytest.raises(KeyError):
        send_email.run(data)
    assert not mailoutbox


@pytest.mark.parametrize("context", [None, {"username": "Nancy"}])
def test_templated_email(context, settings, mailoutbox):
    settings.EMAIL_TEMPLATE_DIR = "emails"
    settings.TEMPLATES = [
        {
            "BACKEND": "django.template.backends.django.DjangoTemplates",
            "OPTIONS": {
                "loaders": [
                    (
                        "django.template.loaders.locmem.Loader",
                        {
                            "emails/welcome.html": "<p>Hello {{ username|default:'friend' }}</p>"
                        },
                    )
                ]
            },
        }
    ]
    send_templated_email.run("Welcome", "user@example.com", "welcome.html", context)
    assert len(mailoutbox) == 1
    expected = "Hello Nancy" if context else "Hello friend"
    message = mailoutbox[0]
    assert message.subject == "Welcome"
    assert message.to == ["user@example.com"]
    assert message.body == expected
    assert message.alternatives == [(f"<p>{expected}</p>", "text/html")]


def test_delivery_failure_propagates(mocker):
    mocker.patch.object(
        mail.EmailMultiAlternatives,
        "send",
        side_effect=RuntimeError("SMTP unavailable"),
    )
    with pytest.raises(RuntimeError, match="SMTP unavailable"):
        send_email.run({"subject": "Welcome", "to_email": "user@example.com"})
