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
    email = models.EmailField()

    def __str__(self):
        return self.full_name


class Asset(models.Model):
    """Main asset model"""

    class Meta:
        ordering = ["-created_at"]

    asset_tag = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    alloted_to = models.ForeignKey(
        Employee, on_delete=models.SET_NULL, null=True, blank=True
    )

    # Device details
    make_model = models.CharField(max_length=200)
    cpu_serial_number = models.CharField(max_length=100)

    # Configuration
    processor = models.CharField(max_length=100)
    ram = models.CharField(max_length=50)
    hdd = models.CharField(max_length=50, blank=True, null=True)
    ssd = models.CharField(max_length=50, blank=True, null=True)
    os = models.CharField(max_length=100)

    # Monitor
    monitor_make_model = models.CharField(max_length=200, blank=True, null=True)
    monitor_serial_number = models.CharField(max_length=100, blank=True, null=True)

    # Keyboard & Mouse (optional text field)
    keyboard_mouse = models.CharField(max_length=200, blank=True, null=True)

    # UPS
    ups_make_model = models.CharField(max_length=200, blank=True, null=True)
    ups_serial_number = models.CharField(max_length=100, blank=True, null=True)

    # Printer
    printer_make_model = models.CharField(max_length=200, blank=True, null=True)
    printer_serial_number = models.CharField(max_length=100, blank=True, null=True)

    # Metadata
    year_of_purchase = models.PositiveIntegerField()
    condition = models.CharField(
        max_length=20, choices=CONDITION_CHOICES, default="working"
    )
    remarks = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.asset_tag} - {self.make_model}"


def asset_document_path(instance, filename):
    return f"asset_documents/{instance.asset.asset_tag}/{filename}"


class AssetDocument(models.Model):
    """File uploads like invoice, warranty, etc."""

    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name="documents")
    name = models.CharField(max_length=255)
    document = models.FileField(upload_to=asset_document_path)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.asset.asset_tag} - {self.name}"


class RepairStatus(models.Model):
    """AMC / Repair / Replacement logs"""

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


class AssetHistory(models.Model):
    ACTIONS = [
        ("created", "Created"),
        ("assigned", "Assigned"),
        ("updated", "Updated"),
        ("returned", "Returned"),
        ("repaired", "Sent for Repair"),
        ("disposed", "Disposed"),
        ("deleted", "Deleted"),
    ]

    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name="history")
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=50, choices=ACTIONS)
    timestamp = models.DateTimeField(auto_now_add=True)
    remarks = models.TextField(blank=True)

    def __str__(self):
        return f"{self.asset.asset_tag} - {self.action} - {self.timestamp.strftime('%Y-%m-%d %H:%M')}"
