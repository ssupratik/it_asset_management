from django.contrib import admin

from .models import Asset, AssetDocument, DisposalRecord, Employee, RepairStatus

admin.site.register(Asset)
admin.site.register(Employee)
admin.site.register(AssetDocument)
admin.site.register(RepairStatus)
admin.site.register(DisposalRecord)
