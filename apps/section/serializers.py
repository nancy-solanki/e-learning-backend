from rest_framework import serializers

from apps.core.moderation import InstructorStatusReadOnlyMixin
from apps.course.models import Course

# TODO: Uncomment when lecture app is created
# from lecture.serializers import LectureSerializer
# from lecture.models import Lecture
from .models import Section


class SectionSerializer(InstructorStatusReadOnlyMixin, serializers.ModelSerializer):
    instructor = serializers.ReadOnlyField(source="instructor.username")
    course = serializers.PrimaryKeyRelatedField(queryset=Course.objects.all())
    # TODO: Uncomment when lecture app is created
    # lecture = LectureSerializer(read_only=True, many=True)
    course_title = serializers.SerializerMethodField("get_course_title")

    def get_course_title(self, instance) -> str:
        return instance.course.title

    def validate(self, attrs):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        course = attrs.get("course", getattr(self.instance, "course", None))
        if (
            user
            and user.is_authenticated
            and not user.is_admin
            and course
            and course.instructor_id != user.pk
        ):
            raise serializers.ValidationError(
                {"course": "Select a course owned by the authenticated instructor."}
            )

        status = attrs.get("status", getattr(self.instance, "status", None))
        if (
            user
            and user.is_authenticated
            and user.is_admin
            and status == Section.Status.PUBLISHED
            and self.instance
            and not self.instance.lecture.filter(deleted_at__isnull=True).exists()
        ):
            raise serializers.ValidationError(
                {"status": "A section must have at least one non-deleted lecture."}
            )
        return attrs

    class Meta:
        model = Section
        fields = "__all__"


class FilteredSectionSerializer(serializers.ModelSerializer):
    instructor = serializers.ReadOnlyField(source="instructor.username")
    # TODO: Uncomment when lecture app is created
    # lecture = serializers.SerializerMethodField('published_lecture')

    # def published_lecture(self, instance):
    #     query = Lecture.objects.filter(status="published", section=instance).order_by("order")
    #     serializer = LectureSerializer(query, many=True)
    #     return serializer.data

    class Meta:
        model = Section
        fields = "__all__"
