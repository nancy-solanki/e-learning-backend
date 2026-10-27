"""Provision personal wallets when users acquire an earning role."""

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db import transaction
from django.db.models.signals import m2m_changed, post_save
from django.dispatch import receiver

from .models import Wallet

User = get_user_model()
WALLET_ROLES = ("admin", "instructor")


def ensure_user_wallet(user_id, using):
    # Serialize provisioning for the same user, including concurrent role additions.
    with transaction.atomic(using=using):
        User.objects.using(using).select_for_update().get(pk=user_id)
        wallets = Wallet.objects.using(using).filter(
            user_id=user_id, is_site_wallet=False
        )
        # Preserve existing balances and intentionally disabled wallets.
        if not wallets.exists():
            wallets.create(user_id=user_id, is_site_wallet=False)


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def provision_superuser_wallet(sender, instance, raw, using, **kwargs):
    if not raw and instance.is_superuser:
        ensure_user_wallet(instance.pk, using)


@receiver(m2m_changed, sender=User.groups.through)
def provision_role_wallet(sender, instance, action, reverse, pk_set, using, **kwargs):
    if action != "post_add" or not pk_set:
        return
    if reverse:
        if instance.name in WALLET_ROLES:
            for user_id in sorted(pk_set):
                ensure_user_wallet(user_id, using)
    elif (
        Group.objects.using(using).filter(pk__in=pk_set, name__in=WALLET_ROLES).exists()
    ):
        ensure_user_wallet(instance.pk, using)
