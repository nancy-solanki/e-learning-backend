import factory

from apps.bank.models import Bank
from apps.users.tests.factories import UserFactory


class BankFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Bank

    user = factory.SubFactory(UserFactory)
    name = "Example Bank"
    ifsc_code = "BANK0001234"
    account_number = factory.Sequence(lambda n: str(1000000000 + n))
