import factory

from apps.category.models import Category
from apps.common.tests.factories import FileFactory
from apps.users.tests.factories import UserFactory


class CategoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Category

    title = factory.Sequence(lambda n: f"category {n}")
    description = "Learning resources"
    user = factory.SubFactory(UserFactory)
    thumbnail = factory.SubFactory(FileFactory)
