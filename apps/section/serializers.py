from rest_framework import serializers
# TODO: Uncomment when lecture app is created
# from lecture.serializers import LectureSerializer
# from lecture.models import Lecture
from .models import Section


class SectionSerializer(serializers.ModelSerializer):
    instructor = serializers.ReadOnlyField(source='instructor.username')
    # TODO: Uncomment when lecture app is created
    # lecture = LectureSerializer(read_only=True, many=True)
    course_title = serializers.SerializerMethodField("get_course_title")

    def get_course_title(self, instance):
        return instance.course.title

    class Meta:
        model = Section
        fields = '__all__'


class FilteredSectionSerializer(serializers.ModelSerializer):
    instructor = serializers.ReadOnlyField(source='instructor.username')
    # TODO: Uncomment when lecture app is created
    # lecture = serializers.SerializerMethodField('published_lecture')

    # def published_lecture(self, instance):
    #     query = Lecture.objects.filter(status="published", section=instance).order_by("order")
    #     serializer = LectureSerializer(query, many=True)
    #     return serializer.data

    class Meta:
        model = Section
        fields = '__all__'