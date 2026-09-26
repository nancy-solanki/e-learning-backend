import factory

from apps.common.models import Files


class FileFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Files

    url = "https://example.com/image.png"
    name = "image.png"
    type = "image/png"
    size = 4
