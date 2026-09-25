from rest_framework import serializers

from apps.course.serializers import CourseMinimalSerializer
from apps.users.serializers import UserSerializer

from .models import Enroll


class EnrollSerializer(serializers.ModelSerializer):
    course = CourseMinimalSerializer(read_only=True)
    user = UserSerializer(read_only=True)
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

    def get_progress(self, obj):
        """
        Calculate progress as a percentage based on completed lectures.
        Currently returns 0 as lecture completion tracking is not yet implemented.
        """
        # TODO: Implement lecture completion tracking to calculate actual progress
        # For now, return 0 as a placeholder
        return 0
