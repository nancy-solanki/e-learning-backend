from hashlib import sha256

from django.conf import settings
from django.core.cache import cache
from rest_framework.response import Response

PUBLIC_CACHE_VERSION_KEY = "public-api:cache-version"


def invalidate_public_api_cache():
    if cache.add(PUBLIC_CACHE_VERSION_KEY, 1, timeout=None):
        return
    try:
        cache.incr(PUBLIC_CACHE_VERSION_KEY)
    except ValueError:
        cache.set(PUBLIC_CACHE_VERSION_KEY, 1, timeout=None)


class PublicResponseCacheMixin:
    def _public_cache_key(self, request, action):
        uri = request._request.build_absolute_uri()
        digest = sha256(uri.encode()).hexdigest()
        view_name = f"{self.__class__.__module__}.{self.__class__.__name__}"
        version = cache.get(PUBLIC_CACHE_VERSION_KEY, 0)
        return f"public-api:{version}:{view_name}:{action}:{digest}"

    def _cached_response(self, request, action):
        key = self._public_cache_key(request, action)
        data = cache.get(key)
        if data is None:
            return key, None
        return key, Response(data)

    @staticmethod
    def _store_response(key, response):
        if response.status_code == 200:
            cache.set(key, response.data, settings.PUBLIC_API_CACHE_SECONDS)
        return response

    def list(self, request, *args, **kwargs):
        key, response = self._cached_response(request, "list")
        if response is not None:
            return response
        response = super().list(request, *args, **kwargs)
        return self._store_response(key, response)

    def retrieve(self, request, *args, **kwargs):
        key, response = self._cached_response(request, "retrieve")
        if response is not None:
            return response
        response = super().retrieve(request, *args, **kwargs)
        return self._store_response(key, response)