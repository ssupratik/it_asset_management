# assets/views.py

import csv

from django.forms.models import model_to_dict
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import ListView

from .forms import AssetForm, EmployeeForm
from .models import Asset, AssetHistory, Employee

from django.shortcuts import render, get_object_or_404
from .models import Asset, AssetHistory

def asset_history_list(request):
    history = AssetHistory.objects.select_related("asset", "user").order_by("-timestamp")
    return render(request, "assets/asset_history_list.html", {"history": history})


def asset_history(request, pk):
    asset = get_object_or_404(Asset, pk=pk)
    history = asset.history.select_related("user").order_by("-timestamp")
    return render(request, "assets/asset_history.html", {
        "asset": asset,
        "history": history
    })


def asset_detail(request, pk):
    asset = get_object_or_404(Asset, pk=pk)
    return render(request, "assets/asset_detail.html", {"asset": asset})


def employee_create(request):
    if request.method == "POST":
        form = EmployeeForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("employee_list")
    else:
        form = EmployeeForm()
    return render(request, "employee_create.html", {"form": form})

def employee_list(request):
    employees = Employee.objects.all()
    return render(request, "employee_list.html", {"employees": employees})


def export_assets_csv(request):
    queryset = Asset.objects.select_related("alloted_to").all()

    # Apply the same filters as in AssetListView
    name = request.GET.get("name", "")
    category = request.GET.get("category", "")
    condition = request.GET.get("condition", "")
    assigned = request.GET.get("assigned", "")

    if name:
        queryset = queryset.filter(name__icontains=name)

    if category:
        queryset = queryset.filter(category=category)

    if condition:
        queryset = queryset.filter(condition=condition)

    if assigned:
        if assigned == "yes":
            queryset = queryset.exclude(alloted_to__isnull=True)
        elif assigned == "no":
            queryset = queryset.filter(alloted_to__isnull=True)

    # Create CSV response
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="assets.csv"'

    writer = csv.writer(response)
    writer.writerow(
        ["Name", "Category", "Condition", "Assigned To", "Purchase Date", "Location"]
    )

    for asset in queryset:
        writer.writerow(
            [
                asset.name,
                asset.category,
                asset.condition,
                asset.alloted_to.name if asset.alloted_to else "Unassigned",
                asset.purchase_date,
                asset.location,
            ]
        )

    return response


class AssetListView(ListView):
    model = Asset
    template_name = "assets/asset_list.html"
    context_object_name = "assets"
    paginate_by = 20

    def get_queryset(self):
        queryset = Asset.objects.all().select_related("alloted_to")
        name = self.request.GET.get("name")
        category = self.request.GET.get("category")
        condition = self.request.GET.get("condition")
        assigned = self.request.GET.get("assigned")

        if name:
            queryset = queryset.filter(name__icontains=name)
        if category:
            queryset = queryset.filter(category=category)
        if condition:
            queryset = queryset.filter(condition=condition)
        if assigned == "yes":
            queryset = queryset.exclude(alloted_to=None)
        elif assigned == "no":
            queryset = queryset.filter(alloted_to=None)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categories"] = Asset.objects.values_list(
            "category", flat=True
        ).distinct()
        context["conditions"] = Asset.objects.values_list(
            "condition", flat=True
        ).distinct()
        return context


def dashboard_view(request):
    total_assets = Asset.objects.count()
    assigned_assets = Asset.objects.exclude(alloted_to=None).count()
    under_repair = Asset.objects.filter(condition="repair").count()
    disposed_assets = Asset.objects.filter(condition="disposed").count()
    assets = Asset.objects.all()[:10]  # Show latest 10 assets

    return render(
        request,
        "assets/dashboard.html",
        {
            "total_assets": total_assets,
            "assigned_assets": assigned_assets,
            "under_repair": under_repair,
            "disposed_assets": disposed_assets,
            "assets": assets,
        },
    )


def asset_list(request):
    assets = Asset.objects.all()
    return render(request, "assets/asset_list.html", {"assets": assets})


def asset_create(request):
    if request.method == "POST":
        form = AssetForm(request.POST, request.FILES)
        if form.is_valid():
            asset = form.save()
            # Log "created" history
            AssetHistory.objects.create(
                asset=asset,
                user=request.user,
                action="created",
                remarks="Asset created.",
            )
            # If asset was assigned
            if asset.alloted_to:
                AssetHistory.objects.create(
                    asset=asset,
                    user=request.user,
                    action="assigned",
                    remarks=f"Assigned to {asset.alloted_to}",
                )
            return redirect("asset_list")
    else:
        form = AssetForm()
    return render(
        request, "assets/asset_form.html", {"form": form, "title": "Add Asset"}
    )


def asset_update(request, pk):
    asset = get_object_or_404(Asset, pk=pk)
    previous_alloted_to = asset.alloted_to  # Track before change
    original_data = model_to_dict(asset)    # Snapshot before update

    if request.method == "POST":
        form = AssetForm(request.POST, request.FILES, instance=asset)
        if form.is_valid():
            updated_asset = form.save()
            new_data = model_to_dict(updated_asset)

            remarks = []

            # Detect field changes
            for field, old_value in original_data.items():
                new_value = new_data.get(field)
                if old_value != new_value:
                    remarks.append(f"{field.replace('_', ' ').title()} changed from '{old_value}' to '{new_value}'")

            # Check assignment changes
            new_alloted_to = updated_asset.alloted_to
            if previous_alloted_to != new_alloted_to:
                if new_alloted_to:
                    action = "assigned"
                    remarks.append(f"Assigned to {new_alloted_to}")
                else:
                    action = "returned"
                    remarks.append("Asset returned/unassigned")
                AssetHistory.objects.create(
                    asset=updated_asset,
                    user=request.user,
                    action=action,
                    remarks="; ".join(remarks),
                )

            # Always log updates
            AssetHistory.objects.create(
                asset=asset,
                user=request.user if request.user.is_authenticated else None,
                action="updated",
                remarks="Asset updated successfully."
            )

            return redirect("asset_list")
    else:
        form = AssetForm(instance=asset)

    return render(
        request, "assets/asset_form.html", {"form": form, "title": "Edit Asset"}
    )


def asset_delete(request, pk):
    asset = get_object_or_404(Asset, pk=pk)
    if request.method == "POST":
        asset.delete()
        return redirect("asset_list")
    return render(request, "assets/asset_confirm_delete.html", {"asset": asset})
