from django.utils.text import slugify
from rest_framework import serializers

from .models import Category


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        """
        Metaclass for the CategorySerializer
        """

        model = Category
        exclude = ("user",)
        read_only_fields = ("created_at", "updated_at", "deleted_at", "thumbnail")

    def validate(self, data):
        """
        Validate the category data
        """
        categories = Category.objects.all()
        if self.instance:
            categories = categories.exclude(pk=self.instance.pk)
        if "title" in data:
            data["title"] = data["title"].strip().lower()
            if categories.filter(title__iexact=data["title"]).exists():
                raise serializers.ValidationError(
                    {"title": "Category with title already exists."}
                )
        slug = data.get("slug") or (
            self.instance.slug if self.instance else slugify(data.get("title", ""))
        )
        if not slug or len(slug) > Category._meta.get_field("slug").max_length:
            raise serializers.ValidationError(
                {"slug": "Provide a non-empty slug of at most 50 characters."}
            )
        if categories.filter(slug=slug).exists():
            raise serializers.ValidationError({"slug": "Category slug already exists."})
        data["slug"] = slug
        return data

    def to_representation(self, instance):
        from apps.common.serializers import FileSerializer

        data = super().to_representation(instance)
        if hasattr(instance, "thumbnail") and instance.thumbnail:
            data["thumbnail"] = FileSerializer(instance.thumbnail).data
        else:
            data["thumbnail"] = None
        return data
