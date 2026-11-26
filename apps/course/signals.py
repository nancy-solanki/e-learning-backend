from django.conf import settings
from django.db.models.signals import m2m_changed, post_delete, post_save, pre_delete
from django.dispatch import receiver

from .models import Course
from .search import schedule_course_index

if getattr(settings, "OPENSEARCH_ENABLED", False):

    @receiver(post_save, sender=Course)
    @receiver(post_delete, sender=Course)
    def course_changed(sender, instance, **kwargs):
        schedule_course_index(instance.pk)

    @receiver(m2m_changed, sender=Course.categories.through)
    @receiver(m2m_changed, sender=Course.tags.through)
    def course_relations_changed(sender, instance, action, **kwargs):
        if action in {"post_add", "post_remove", "post_clear"}:
            if isinstance(instance, Course):
                schedule_course_index(instance.pk)
            else:
                relation = (
                    "categories" if sender is Course.categories.through else "tags"
                )
                for course_id in Course.objects.filter(
                    **{relation: instance}
                ).values_list("pk", flat=True):
                    schedule_course_index(course_id)

    @receiver(post_save, sender="category.Category")
    @receiver(pre_delete, sender="category.Category")
    @receiver(post_save, sender="course.Tag")
    @receiver(pre_delete, sender="course.Tag")
    @receiver(post_save, sender="users.User")
    @receiver(pre_delete, sender="users.User")
    def related_search_data_changed(sender, instance, **kwargs):
        model = sender
        if model.__name__ == "Category":
            ids = Course.objects.filter(categories=instance).values_list(
                "pk", flat=True
            )
        elif model.__name__ == "Tag":
            ids = Course.objects.filter(tags=instance).values_list("pk", flat=True)
        else:
            ids = Course.objects.filter(instructor=instance).values_list(
                "pk", flat=True
            )
        for course_id in ids:
            schedule_course_index(course_id)
