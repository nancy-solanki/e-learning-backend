from rest_framework import serializers

from .models import Lecture


class LectureSerializer(serializers.ModelSerializer):
    instructor = serializers.ReadOnlyField(source="instructor.username")

    class Meta:
        model = Lecture
        fields = "__all__"
