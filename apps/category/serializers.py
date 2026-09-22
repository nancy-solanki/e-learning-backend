from rest_framework import serializers

from .models import Category


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        """
        Metaclass for the CategorySerializer
        """
        model = Category
        exclude = ('user', )

    def validate(self, data):
        """
        Validate the category data
        """
        categories = Category.objects.filter(title__icontains=data['title'])
        if self.instance:
            categories = categories.exclude(pk=self.instance.pk)
        if categories.exists():
            raise serializers.ValidationError("Category with title already exists")
        return data

    def to_representation(self, instance):
        from apps.common.serializers import FileSerializer
        data = super().to_representation(instance)
        if hasattr(instance, 'thumbnail') and instance.thumbnail:
            data['thumbnail'] = FileSerializer(instance.thumbnail).data
        else:
            data['thumbnail'] = None
        return data
