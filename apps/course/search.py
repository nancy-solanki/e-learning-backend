"""OpenSearch indexing and query helpers for the public course catalog."""

import logging

from django.conf import settings

logger = logging.getLogger(__name__)


def get_client():
    from opensearchpy import OpenSearch

    options = {
        "hosts": [settings.OPENSEARCH_URL],
        "use_ssl": settings.OPENSEARCH_USE_SSL,
        "verify_certs": settings.OPENSEARCH_VERIFY_CERTS,
    }
    if settings.OPENSEARCH_USERNAME:
        options["http_auth"] = (
            settings.OPENSEARCH_USERNAME,
            settings.OPENSEARCH_PASSWORD,
        )
    return OpenSearch(**options)


def course_document(course):
    return {
        "title": course.title,
        "short_description": course.short_description,
        "long_description": course.long_description,
        "requirements": course.requirements,
        "learn_description_points": course.learn_description_points,
        "categories": list(
            course.categories.filter(deleted_at__isnull=True).values_list(
                "title", flat=True
            )
        ),
        "tags": list(
            course.tags.filter(deleted_at__isnull=True).values_list("name", flat=True)
        ),
        "instructor": " ".join(
            value
            for value in (course.instructor.first_name, course.instructor.last_name)
            if value
        ),
        "status": course.status,
        "deleted": course.deleted_at is not None,
    }


def index_course(course_id):
    from .models import Course

    client = get_client()
    try:
        course = (
            Course.objects.select_related("instructor")
            .prefetch_related("categories", "tags")
            .get(pk=course_id)
        )
    except Course.DoesNotExist:
        client.delete(index=settings.OPENSEARCH_INDEX, id=str(course_id), ignore=[404])
        return
    client.index(
        index=settings.OPENSEARCH_INDEX,
        id=str(course.pk),
        body=course_document(course),
        refresh=False,
    )


def search_course_ids(query):
    response = get_client().search(
        index=settings.OPENSEARCH_INDEX,
        body={
            "size": 10000,
            "_source": False,
            "query": {
                "multi_match": {
                    "query": query,
                    "fields": [
                        "title^5",
                        "short_description^2",
                        "long_description",
                        "categories^2",
                        "tags^2",
                        "instructor",
                        "requirements",
                        "learn_description_points",
                    ],
                    "type": "best_fields",
                    "operator": "and",
                    "fuzziness": "AUTO",
                }
            },
        },
    )
    return [hit["_id"] for hit in response["hits"]["hits"]]


def schedule_course_index(course_id):
    from django.db import transaction

    transaction.on_commit(lambda: _safe_index(course_id))


def _safe_index(course_id):
    try:
        index_course(course_id)
    except Exception:
        logger.exception("Could not update OpenSearch course document %s", course_id)
