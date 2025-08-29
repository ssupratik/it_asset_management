from django.contrib.auth.models import User
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from common.current_user import get_current_user  # << added

from .models import Asset, AssetHistory


@receiver(pre_save, sender=Asset)
def log_asset_changes(sender, instance, **kwargs):
    """
    Before saving, compare with the old instance to detect changes
    and record them in AssetHistory.
    """
    if not instance.pk:  # New asset
        return  # post_save will handle "created"

    try:
        old_instance = Asset.objects.get(pk=instance.pk)
    except Asset.DoesNotExist:
        return

    changes = []

    if old_instance.alloted_to != instance.alloted_to:
        changes.append(
            (
                "transferred" if old_instance.alloted_to else "assigned",
                instance.alloted_to,
            )
        )

    if old_instance.condition != instance.condition:
        if instance.condition == "disposed":
            changes.append(("disposed", instance.alloted_to))
        elif instance.condition == "repair":
            changes.append(("repaired", instance.alloted_to))

    # If asset was deactivated (is_active=False)
    if old_instance.is_active != instance.is_active and not instance.is_active:
        changes.append(("returned", instance.alloted_to))

    # Write history for each detected change
    user = get_current_user()
    for action, employee in changes:
        AssetHistory.objects.create(
            asset=instance,
            employee=employee,
            performed_by=user,
            action=action,
            remarks=f"System auto-logged change: {action}",
        )


@receiver(post_save, sender=Asset)
def log_asset_creation(sender, instance, created, **kwargs):
    """Log when a new asset is created"""
    if created:
        user = get_current_user()
        AssetHistory.objects.create(
            asset=instance,
            employee=instance.alloted_to,
            performed_by=user,
            action="created",
            remarks="Asset record created",
        )
