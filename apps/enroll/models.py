from django.db import models

from apps.core.models import BaseModel

# Create your models here.


class Enroll(BaseModel):
    user = models.ForeignKey("users.User", on_delete=models.RESTRICT)
    course = models.ForeignKey(
        "course.Course", on_delete=models.RESTRICT, related_name="enroll"
    )

    def __str__(self):
        return f"{self.user} - {self.course.title}"

    def soft_delete(self):
        from django.utils import timezone

        self.deleted_at = timezone.now()
        self.save(update_fields=["deleted_at"])
        return self

    def restore(self):
        self.deleted_at = None
        self.save(update_fields=["deleted_at"])
        return self

    class Meta:
        db_table = "enroll"
        verbose_name = "enroll"
        verbose_name_plural = "enrolls"
        ordering = ["-created_at"]
