from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import BaseModel


class Rating(BaseModel):
    course = models.ForeignKey(
        "course.Course", on_delete=models.RESTRICT, related_name="rating"
    )
    rating = models.DecimalField(decimal_places=1, max_digits=5)
    comment = models.CharField(max_length=5000)
    response = models.CharField(max_length=5000, null=True, blank=True)
    user = models.ForeignKey("users.User", on_delete=models.RESTRICT)

    def __str__(self):
        return f"{self.user} - {self.course.title} ({self.rating})"

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
        db_table = "rating"
        verbose_name = _("rating")
        verbose_name_plural = _("ratings")
        ordering = ["-created_at"]
