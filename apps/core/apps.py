from importlib import import_module

from django.apps import AppConfig


class CoreConfig(AppConfig):
    name = "apps.core"

    def ready(self):
        import_module("apps.core.signals")
