from django.apps import AppConfig


class CourseConfig(AppConfig):
    name = "apps.course"

    def ready(self):
        from . import signals  # noqa: F401
