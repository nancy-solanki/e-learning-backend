from rest_framework import serializers
from django.contrib.auth import get_user_model

from apps.category.models import Category
from apps.common.models import Files
from apps.common.serializers import FileSerializer
from .models import Course, Tag

User = get_user_model()


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name', 'slug']


class CategoryMinimalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'title', 'slug']


class InstructorSerializer(serializers.ModelSerializer):
    avatar = FileSerializer(read_only=True)
    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'username', 'avatar']

class CourseMinimalSerializer(serializers.ModelSerializer):
    instructor = InstructorSerializer(read_only=True)
    thumbnail = FileSerializer(read_only=True)

    class Meta:
        model = Course
        fields = [
            'id', 'title', 'slug', 'thumbnail', 'instructor', 
            'is_free', 'price', 'status', 'total_hours'
        ]



class FilteredCourseSerializer(serializers.ModelSerializer):
    instructor = InstructorSerializer(read_only=True)
    categories = CategoryMinimalSerializer(many=True, read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    thumbnail = FileSerializer(read_only=True)
    student_count = serializers.SerializerMethodField()

    def get_student_count(self, obj):
        return obj.enroll.count()

    class Meta:
        model = Course
        fields = [
            'id', 'title', 'slug', 'short_description', 'long_description',
            'is_free', 'price', 'status', 'is_best_seller', 'learn_description_points',
            'requirements', 'total_hours', 'total_articles', 'thumbnail', 'tags',
            'instructor', 'categories', 'student_count',
            'created_at', 'updated_at'
        ]


class CourseSerializer(serializers.ModelSerializer):
    student_count = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = '__all__'

    def get_student_count(self, obj):
        return obj.enroll.count()
