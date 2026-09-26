import factory

from apps.transaction.models import Transaction
from apps.users.tests.factories import UserFactory


class TransactionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Transaction

    user = factory.SubFactory(UserFactory)
    amount = 100
    transaction_type = "credit"
    tx_id = factory.Sequence(lambda n: f"tx-{n}")
