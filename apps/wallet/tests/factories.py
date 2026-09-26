import factory

from apps.users.tests.factories import UserFactory
from apps.wallet.models import Wallet


class WalletFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Wallet

    user = factory.SubFactory(UserFactory)
