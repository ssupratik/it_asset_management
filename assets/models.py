import uuid

from django.contrib.auth.models import User
from django.db import models

# Choices for asset condition
CONDITION_CHOICES = [
    ("working", "Working"),
    ("damaged", "Damaged"),
    ("repair", "Under Repair"),
    ("obsolete", "Obsolete"),
    ("disposed", "Disposed"),
]

REPAIR_STATUS_CHOICES = [
    ("reported", "Reported"),
    ("in_progress", "In Progress"),
    ("resolved", "Resolved"),
    ("replaced", "Replaced"),
    ("closed", "Closed"),
]


class Employee(models.Model):
    full_name = models.CharField(max_length=100)
    designation = models.CharField(max_length=100)
    email = models.EmailField(null=True, blank=True)

    def __str__(self):
        return self.full_name


class AssetType(models.Model):
    """Type of asset e.g. CPU, Monitor, UPS, Printer, Keyboard/Mouse"""
    name = models.CharField(max_length=100, unique=True)
    category = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        verbose_name_plural = "Asset Types"

    def __str__(self):
        return f"{self.name} ({self.category})" if self.category else self.name


class Asset(models.Model):
    """Each record represents a single physical component"""

    asset_tag = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    type = models.ForeignKey(AssetType, on_delete=models.CASCADE, related_name="assets")
    make_model = models.CharField(max_length=200)
    serial_number = models.CharField(max_length=100, blank=True, null=True)
    year_of_purchase = models.PositiveIntegerField()

    condition = models.CharField(
        max_length=20, choices=CONDITION_CHOICES, default="working"
    )
    remarks = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    # Who has it right now
    alloted_to = models.ForeignKey(
        Employee,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assets",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.type.name} - {self.make_model} ({self.asset_tag})"


class AssetGroup(models.Model):
    """Represents a set of assets assigned together as a 'system'"""

    name = models.CharField(max_length=200)  # e.g. "John's Workstation"
    description = models.TextField(blank=True, null=True)
    owner = models.ForeignKey(
        Employee, on_delete=models.SET_NULL, null=True, blank=True
    )
    assets = models.ManyToManyField(Asset, related_name="groups")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.owner})"


class AssetHistory(models.Model):
    ACTIONS = [
        ("created", "Created"),
        ("assigned", "Assigned"),
        ("transferred", "Transferred"),
        ("returned", "Returned"),
        ("repaired", "Sent for Repair"),
        ("disposed", "Disposed"),
    ]

    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name="history")
    employee = models.ForeignKey(
        Employee, on_delete=models.SET_NULL, null=True, blank=True
    )
    performed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="performed_actions",
    )
    action = models.CharField(max_length=50, choices=ACTIONS)
    timestamp = models.DateTimeField(auto_now_add=True)
    remarks = models.TextField(blank=True)

    class Meta:
        ordering = ["-timestamp"]

    def __str__(self):
        return f"{self.asset.asset_tag} - {self.action} - {self.timestamp.strftime('%Y-%m-%d %H:%M')}"


def asset_document_path(instance, filename):
    return f"asset_documents/{instance.asset.asset_tag}/{filename}"


class AssetDocument(models.Model):
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name="documents")
    name = models.CharField(max_length=255)
    document = models.FileField(upload_to=asset_document_path)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.asset.asset_tag} - {self.name}"


class RepairStatus(models.Model):
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name="repairs")
    issue = models.CharField(max_length=255)
    status = models.CharField(
        max_length=20, choices=REPAIR_STATUS_CHOICES, default="reported"
    )
    date_reported = models.DateField()
    date_resolved = models.DateField(blank=True, null=True)
    remarks = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.asset.asset_tag} - {self.issue}"


class DisposalRecord(models.Model):
    """Disposal / e-waste tracking"""

    asset = models.OneToOneField(
        Asset, on_delete=models.CASCADE, related_name="disposal"
    )
    disposal_date = models.DateField()
    method = models.CharField(max_length=255)
    certificate = models.FileField(
        upload_to="disposal_certificates/", blank=True, null=True
    )
    remarks = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Disposed: {self.asset.asset_tag}"

    def save(self, *args, **kwargs):
        if not self.pk:  # only on creation
            self.asset.condition = "disposed"
            self.asset.save()
        super().save(*args, **kwargs)
