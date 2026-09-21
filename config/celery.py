import os

from celery import Celery

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")


celery_app = Celery("config")
celery_app.config_from_object("django.conf:settings", namespace="CELERY")

celery_app.conf.timezone = "Asia/Kolkata"
celery_app.conf.enable_utc = False

# Load task modules from all registered Django apps.
celery_app.autodiscover_tasks()
