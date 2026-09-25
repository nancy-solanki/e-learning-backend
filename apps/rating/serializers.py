from rest_framework import serializers

from apps.enroll.models import Enroll
from apps.users.serializers import UserSerializer

from .models import Rating


class RatingSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    course_title = serializers.CharField(source="course.title", read_only=True)

    class Meta:
        model = Rating
        fields = "__all__"

    def validate(self, attrs):
        user = self.context["request"].user

        # If it's a create (self.instance is None)
        if not self.instance:
            course = attrs.get("course")
            if not course:
                raise serializers.ValidationError({"course": "Course is required."})

            # Check if enrolled
            if not Enroll.objects.filter(
                user=user, course=course, deleted_at__isnull=True
            ).exists():
                raise serializers.ValidationError(
                    "Only students enrolled in this course can rate or comment."
                )

            # Check if already rated
            if Rating.objects.filter(
                user=user, course=course, deleted_at__isnull=True
            ).exists():
                raise serializers.ValidationError("You have already rated this course.")

            # Students cannot specify response during creation
            if "response" in attrs:
                attrs.pop("response")

        # If it's an update (self.instance is not None)
        else:
            rating_instance = self.instance

            # Check if student is trying to update
            if user == rating_instance.user:
                # Students can update only the rating and comment.
                if "response" in attrs:
                    raise serializers.ValidationError(
                        "Students cannot respond to ratings."
                    )
                # Discard course/user updates if sent
                attrs.pop("course", None)
                attrs.pop("user", None)

            # Check if instructor is trying to update
            elif user == rating_instance.course.instructor:
                # Instructors can update only the response.
                if "rating" in attrs or "comment" in attrs:
                    raise serializers.ValidationError(
                        "Instructors can only update the response of a rating."
                    )
                # Discard course/user updates if sent
                attrs.pop("course", None)
                attrs.pop("user", None)

            # Admin list/override
            elif user.is_superuser or user.groups.filter(name="admin").exists():
                pass
            else:
                raise serializers.ValidationError(
                    "You are not authorized to update this rating."
                )

        return attrs
