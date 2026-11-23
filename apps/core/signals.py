from django.apps import apps
from django.db.models.signals import m2m_changed, post_delete, post_save

from apps.core.cache import invalidate_public_api_cache


def _invalidate_public_cache(sender, **kwargs):
    invalidate_public_api_cache()


def connect_public_cache_invalidation():
    model_labels = (
        "category.Category",
        "common.Files",
        "course.Course",
        "course.Tag",
        "lecture.Lecture",
        "section.Section",
        "users.User",
    )
    for model_label in model_labels:
        model = apps.get_model(model_label)
        post_save.connect(
            _invalidate_public_cache,
            sender=model,
            dispatch_uid=f"public-cache-save-{model_label}",
        )
        post_delete.connect(
            _invalidate_public_cache,
            sender=model,
            dispatch_uid=f"public-cache-delete-{model_label}",
        )

    course_model = apps.get_model("course.Course")
    for field_name in ("categories", "tags"):
        through_model = course_model._meta.get_field(field_name).remote_field.through
        m2m_changed.connect(
            _invalidate_public_cache,
            sender=through_model,
            dispatch_uid=f"public-cache-m2m-{field_name}",
        )


connect_public_cache_invalidation()