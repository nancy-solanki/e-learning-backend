from rest_framework import serializers

from apps.course.models import Course
from apps.course.serializers import CourseMinimalSerializer
from apps.users.serializers import PublicUserSerializer

from .models import Enroll


class EnrollSerializer(serializers.ModelSerializer):
    course = CourseMinimalSerializer(read_only=True)
    user = PublicUserSerializer(read_only=True)
    average_rating = serializers.FloatField(read_only=True)
    progress = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Enroll
        fields = [
            "id",
            "user",
            "course",
            "average_rating",
            "progress",
            "created_at",
            "updated_at",
            "deleted_at",
        ]

    def get_progress(self, obj) -> int:
        """
        Calculate progress as a percentage based on completed lectures.
        Currently returns 0 as lecture completion tracking is not yet implemented.
        """
        # TODO: Implement lecture completion tracking to calculate actual progress
        # For now, return 0 as a placeholder
        return 0


class EnrollmentStudentSerializer(PublicUserSerializer):
    class Meta(PublicUserSerializer.Meta):
        fields = (*PublicUserSerializer.Meta.fields, "email")
        read_only_fields = fields


class EnrollmentCourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = ("id", "title", "slug")
        read_only_fields = fields


class AdminEnrollmentSerializer(serializers.ModelSerializer):
    user = EnrollmentStudentSerializer(read_only=True)
    course = EnrollmentCourseSerializer(read_only=True)
    total_lessons = serializers.IntegerField(read_only=True)
    # Completion events and access duration are not stored in this application.
    completed_lessons = serializers.IntegerField(
        read_only=True, default=None, allow_null=True
    )
    progress = serializers.IntegerField(read_only=True, default=None, allow_null=True)
    status = serializers.CharField(read_only=True, default="unknown")
    access = serializers.CharField(read_only=True, default=None, allow_null=True)
    progress_tracking_available = serializers.BooleanField(
        read_only=True, default=False
    )

    class Meta:
        model = Enroll
        fields = (
            "id",
            "user",
            "course",
            "created_at",
            "total_lessons",
            "completed_lessons",
            "progress",
            "status",
            "access",
            "progress_tracking_available",
        )
        read_only_fields = fields


class EnrollmentSummarySerializer(serializers.Serializer):
    total_enrollments = serializers.IntegerField()
    in_progress = serializers.IntegerField(allow_null=True)
    completed = serializers.IntegerField(allow_null=True)
    not_started = serializers.IntegerField(allow_null=True)
    unknown = serializers.IntegerField()
    progress_tracking_available = serializers.BooleanField()
