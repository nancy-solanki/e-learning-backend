import os

from celery import Celery
from celery.schedules import crontab

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")


celery_app = Celery("config")
celery_app.config_from_object("django.conf:settings", namespace="CELERY")
celery_app.conf.imports = (*celery_app.conf.imports, "apps.core.services")

celery_app.conf.timezone = "Asia/Kolkata"
celery_app.conf.enable_utc = False
celery_app.conf.beat_schedule = {
    "notify-expiring-coupons-daily": {
        "task": "apps.coupon.tasks.notify_expiring_coupons",
        "schedule": crontab(hour=9, minute=0),
    }
}

# Load task modules from all registered Django apps.
celery_app.autodiscover_tasks()
