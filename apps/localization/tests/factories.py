import factory

from apps.localization.models import Localization


class LocalizationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Localization

    language_name = factory.Sequence(lambda n: f"Language {n}")
    country = "India"
