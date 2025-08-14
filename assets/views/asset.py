from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from ..forms.asset import AssetForm
from ..models import Asset


@login_required
def asset_list(request):
    """List all assets with type and assigned employee."""
    assets = Asset.objects.select_related("type", "alloted_to").all()
    return render(request, "assets/asset_list.html", {"assets": assets})


@login_required
def asset_detail(request, pk):
    """View a single asset's details."""
    asset = get_object_or_404(Asset.objects.select_related("type", "alloted_to"), pk=pk)
    return render(request, "assets/asset_detail.html", {"asset": asset})


@login_required
def asset_create(request):
    """Create a new asset component."""
    if request.method == "POST":
        form = AssetForm(request.POST, request.FILES)
        if form.is_valid():
            asset = form.save()
            messages.success(request, f"Asset '{asset}' created successfully.")
            return redirect("asset_list")
    else:
        form = AssetForm()

    return render(
        request, "assets/asset_form.html", {"form": form, "form_title": "Add Asset"}
    )


@login_required
def asset_update(request, pk):
    """Update an existing asset."""
    asset = get_object_or_404(Asset, pk=pk)

    if request.method == "POST":
        form = AssetForm(request.POST, request.FILES, instance=asset)
        if form.is_valid():
            form.save()
            messages.success(request, f"Asset '{asset}' updated successfully.")
            return redirect("asset_detail", pk=asset.pk)
    else:
        form = AssetForm(instance=asset)

    return render(
        request,
        "assets/asset_form.html",
        {"form": form, "form_title": f"Edit Asset: {asset}"},
    )


@login_required
def asset_delete(request, pk):
    """Delete an asset."""
    asset = get_object_or_404(Asset, pk=pk)

    if request.method == "POST":
        asset.delete()
        messages.success(request, "Asset deleted successfully.")
        return redirect("asset_list")

    return render(request, "assets/asset_confirm_delete.html", {"asset": asset})
