from types import SimpleNamespace

from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.core.cache import cache
from django.test import override_settings
from rest_framework.test import APIRequestFactory
from rest_framework.throttling import ScopedRateThrottle


def test_scoped_throttle_rejects_requests_over_rate():
    cache.clear()
    rest_framework_settings = {
        **settings.REST_FRAMEWORK,
        "DEFAULT_THROTTLE_RATES": {"test_scope": "1/minute"},
    }

    with override_settings(REST_FRAMEWORK=rest_framework_settings):
        throttle = ScopedRateThrottle()
        view = SimpleNamespace(throttle_scope="test_scope")
        request = APIRequestFactory().post("/", REMOTE_ADDR="192.0.2.1")
        request.user = AnonymousUser()

        assert throttle.allow_request(request, view)
        assert not throttle.allow_request(request, view)

    cache.clear()