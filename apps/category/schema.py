from rest_framework import serializers

from .serializers import CategorySerializer


class CategoryUploadSerializer(CategorySerializer):
    thumbnail = serializers.ImageField(
        help_text="Upload a thumbnail image as multipart/form-data."
    )
