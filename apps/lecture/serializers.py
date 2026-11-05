from rest_framework import serializers

from apps.core.moderation import InstructorStatusReadOnlyMixin
from apps.course.models import Course
from apps.section.models import Section

from .models import Lecture


class LectureSerializer(InstructorStatusReadOnlyMixin, serializers.ModelSerializer):
    instructor = serializers.ReadOnlyField(source="instructor.username")
    course = serializers.PrimaryKeyRelatedField(queryset=Course.objects.all())
    section = serializers.PrimaryKeyRelatedField(queryset=Section.objects.all())

    class Meta:
        model = Lecture
        fields = (
            "id",
            "title",
            "slug",
            "description",
            "status",
            "lecture_type",
            "source",
            "is_preview",
            "document_content",
            "reject_reason",
            "resources",
            "order",
            "thumbnail",
            "instructor",
            "course",
            "section",
            "duration",
            "created_at",
            "updated_at",
            "deleted_at",
        )
        read_only_fields = (
            "id",
            "slug",
            "reject_reason",
            "duration",
            "created_at",
            "updated_at",
            "deleted_at",
        )

    def validate(self, attrs):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated or user.is_admin:
            return attrs

        course = attrs.get("course", getattr(self.instance, "course", None))
        section = attrs.get("section", getattr(self.instance, "section", None))
        errors = {}
        if course and course.instructor_id != user.pk:
            errors["course"] = "Select a course owned by the authenticated instructor."
        if section:
            if section.instructor_id != user.pk:
                errors["section"] = (
                    "Select a section owned by the authenticated instructor."
                )
            if course and section.course_id != course.pk:
                errors["section"] = "The section must belong to the selected course."
        if errors:
            raise serializers.ValidationError(errors)
        return attrs
