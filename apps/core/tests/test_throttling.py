from types import SimpleNamespace

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
    request_factory = APIRequestFactory()
    request = request_factory.post("/", REMOTE_ADDR="192.0.2.1")
    request.user = SimpleNamespace(is_authenticated=True, pk=1)
    another_user_request = request_factory.post("/", REMOTE_ADDR="192.0.2.1")
    another_user_request.user = SimpleNamespace(is_authenticated=True, pk=2)

    assert throttle.allow_request(request, view)
    assert not throttle.allow_request(request, view)
    assert throttle.allow_request(another_user_request, view)

    cache.clear()