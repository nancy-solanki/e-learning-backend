from types import SimpleNamespace

from django.contrib.auth.models import AnonymousUser
from django.core.cache import cache
from rest_framework.test import APIRequestFactory
from rest_framework.throttling import ScopedRateThrottle


def test_scoped_throttle_rejects_requests_over_rate(mocker):
    cache.clear()
    mocker.patch.object(
        ScopedRateThrottle,
        "THROTTLE_RATES",
        {"test_scope": "1/minute"},
    )

    throttle = ScopedRateThrottle()
    view = SimpleNamespace(throttle_scope="test_scope")
    request = APIRequestFactory().post("/", REMOTE_ADDR="192.0.2.1")
    request.user = AnonymousUser()

    assert throttle.allow_request(request, view)
    assert not throttle.allow_request(request, view)

    cache.clear()