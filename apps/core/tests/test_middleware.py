from datetime import timedelta
from uuid import uuid4

import jwt
import pytest
from django.http import HttpResponse
from django.test import RequestFactory
from django.utils import timezone

from apps.core.middleware import UserStatusMiddleware
from apps.users.models import User
from apps.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


@pytest.fixture
def downstream(mocker):
    return mocker.Mock(return_value=HttpResponse("ok"))


def request_token(settings, payload, key=None):
    token = jwt.encode(payload, key or settings.SECRET_KEY, algorithm="HS256")
    return RequestFactory().get("/", HTTP_AUTHORIZATION=f"Bearer {token}")


@pytest.mark.parametrize("header", ["", "Basic abc", "Bearer", "Bearer "])
def test_without_bearer_passes_through(header, downstream):
    request = RequestFactory().get("/", HTTP_AUTHORIZATION=header)
    assert UserStatusMiddleware(downstream)(request).status_code == 200
    downstream.assert_called_once_with(request)


def test_valid_token_sets_user(settings, downstream):
    user = UserFactory()
    request = request_token(
        settings, {"id": str(user.id), "iat": int(timezone.now().timestamp())}
    )
    assert UserStatusMiddleware(downstream)(request).status_code == 200
    assert request.user == user
    downstream.assert_called_once_with(request)


@pytest.mark.parametrize("status", [User.Status.PENDING, User.Status.SUSPEND])
def test_inactive_user_rejected(settings, downstream, status):
    user = UserFactory(status=status)
    request = request_token(settings, {"id": str(user.id)})
    response = UserStatusMiddleware(downstream)(request)
    assert response.status_code == 403
    assert response.is_rendered
    assert response.data["errors"]["non_field_error"]
    downstream.assert_not_called()


@pytest.mark.parametrize(
    "scenario",
    [
        "expired",
        "wrong_signature",
        "missing_user",
        "unknown_user",
        "malformed_id",
        "garbage",
    ],
)
def test_invalid_tokens(settings, downstream, scenario):
    user = UserFactory()
    payload = {"id": str(user.id)}
    key = None
    if scenario == "expired":
        payload["exp"] = int((timezone.now() - timedelta(seconds=30)).timestamp())
    elif scenario == "wrong_signature":
        key = "another-secret-key-that-is-long-enough"
    elif scenario == "missing_user":
        payload = {}
    elif scenario == "unknown_user":
        payload["id"] = str(uuid4())
    elif scenario == "malformed_id":
        payload["id"] = "invalid-uuid"
    request = request_token(settings, payload, key)
    if scenario == "garbage":
        request.META["HTTP_AUTHORIZATION"] = "Bearer garbage"
    response = UserStatusMiddleware(downstream)(request)
    assert response.status_code == 401
    assert response.data["errors"]["code"] == "token_not_valid"
    assert response["Content-Type"] == "application/json"
    downstream.assert_not_called()


@pytest.mark.parametrize("offset, expected", [(-60, 401), (0, 200), (60, 200)])
def test_password_change_invalidates_older_tokens(
    settings, downstream, offset, expected
):
    changed = (timezone.now() - timedelta(minutes=5)).replace(microsecond=0)
    user = UserFactory(password_changed_at=changed)
    request = request_token(
        settings, {"id": str(user.id), "iat": int(changed.timestamp()) + offset}
    )
    assert UserStatusMiddleware(downstream)(request).status_code == expected
    assert downstream.call_count == (1 if expected == 200 else 0)


def test_missing_issued_at_after_password_change(settings, downstream):
    user = UserFactory(password_changed_at=timezone.now())
    response = UserStatusMiddleware(downstream)(
        request_token(settings, {"id": str(user.id)})
    )
    assert response.status_code == 401
    downstream.assert_not_called()
