import json

from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils.text import slugify
from rest_framework import serializers

from apps.category.models import Category
from apps.common.serializers import FileSerializer
from apps.common.service import FileService
from apps.core.moderation import InstructorStatusReadOnlyMixin
from apps.localization.models import Localization

from .models import Course, Tag

User = get_user_model()


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ["id", "name", "slug"]


class CategoryMinimalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "title", "slug"]


class InstructorSerializer(serializers.ModelSerializer):
    avatar = serializers.URLField(read_only=True)

    class Meta:
        model = User
        fields = ["id", "first_name", "last_name", "username", "avatar"]


class CourseMinimalSerializer(serializers.ModelSerializer):
    instructor = InstructorSerializer(read_only=True)
    thumbnail = FileSerializer(read_only=True)

    class Meta:
        model = Course
        fields = [
            "id",
            "title",
            "slug",
            "thumbnail",
            "instructor",
            "is_free",
            "price",
            "status",
            "total_hours",
            "localization",
        ]


class FilteredCourseSerializer(serializers.ModelSerializer):
    instructor = InstructorSerializer(read_only=True)
    categories = CategoryMinimalSerializer(many=True, read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    thumbnail = FileSerializer(read_only=True)
    student_count = serializers.SerializerMethodField()

    def get_student_count(self, obj) -> int:
        return obj.enroll.count()

    class Meta:
        model = Course
        fields = [
            "id",
            "title",
            "slug",
            "short_description",
            "long_description",
            "is_free",
            "price",
            "status",
            "is_best_seller",
            "learn_description_points",
            "requirements",
            "total_hours",
            "total_articles",
            "thumbnail",
            "tags",
            "instructor",
            "categories",
            "localization",
            "student_count",
            "created_at",
            "updated_at",
        ]


class CourseTagsField(serializers.ListField):
    """Accept repeated multipart names or a JSON array (including [] to clear)."""

    def to_internal_value(self, value):
        if isinstance(value, list) and len(value) == 1:
            candidate = value[0]
            if isinstance(candidate, str) and candidate.lstrip().startswith("["):
                try:
                    value = json.loads(candidate)
                except ValueError:
                    raise serializers.ValidationError(
                        "Provide a valid JSON array of tag names."
                    )
        return super().to_internal_value(value)


class CourseSerializer(InstructorStatusReadOnlyMixin, serializers.ModelSerializer):
    instructor = serializers.PrimaryKeyRelatedField(read_only=True)
    student_count = serializers.SerializerMethodField()
    thumbnail = serializers.ImageField(write_only=True)
    localization = serializers.PrimaryKeyRelatedField(
        queryset=Localization.objects.filter(deleted_at__isnull=True),
        required=False,
        allow_null=True,
    )
    tags = CourseTagsField(
        child=serializers.CharField(max_length=100), required=False, write_only=True
    )

    class Meta:
        model = Course
        fields = "__all__"

    def validate_tags(self, names):
        for name in names:
            if not slugify(name):
                raise serializers.ValidationError(
                    "Tag names must produce a non-empty slug."
                )
        return names

    def _prepare_related(self, validated_data):
        thumbnail = validated_data.get("thumbnail")
        if thumbnail is not None:
            try:
                validated_data["thumbnail"] = FileService.upload_file_to_cloud(
                    thumbnail, "course"
                )
            except ValueError as exc:
                raise serializers.ValidationError({"thumbnail": [str(exc)]}) from exc
        if "tags" in validated_data:
            tags = []
            for name in validated_data["tags"]:
                tag = Tag.objects.filter(name__iexact=name).first()
                if tag is None:
                    tag, _ = Tag.objects.get_or_create(
                        slug=slugify(name), defaults={"name": name}
                    )
                tags.append(tag)
            validated_data["tags"] = tags
        return validated_data

    @transaction.atomic
    def create(self, validated_data):
        return super().create(self._prepare_related(validated_data))

    @transaction.atomic
    def update(self, instance, validated_data):
        return super().update(instance, self._prepare_related(validated_data))

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["thumbnail"] = FileSerializer(instance.thumbnail).data
        data["tags"] = TagSerializer(instance.tags.all(), many=True).data
        return data

    def get_student_count(self, obj) -> int:
        return obj.enroll.count()


class CourseResponseSerializer(CourseSerializer):
    thumbnail = FileSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
