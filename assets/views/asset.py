from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpResponseForbidden, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from io import StringIO
from ..forms.asset import AssetForm, AssetDocumentForm
from ..models import Asset, Employee, AssetDocument
from django.forms import inlineformset_factory

AssetDocumentFormSet = inlineformset_factory(
    Asset, AssetDocument, 
    form=AssetDocumentForm, 
    extra=1, 
    can_delete=True
)

@login_required
def upload_document(request, asset_id):
    asset = get_object_or_404(Asset, pk=asset_id)
    if request.method == "POST":
        form = AssetDocumentForm(request.POST, request.FILES)
        if form.is_valid():
            doc = form.save(commit=False)
            doc.asset = asset
            doc.save()
            return redirect("asset_detail", pk=asset_id)
    else:
        form = AssetDocumentForm()
    return render(request, "assets/upload_document.html", {"form": form, "asset": asset})

@login_required
def asset_list(request):
    """List all assets with optional search and filters."""
    q = request.GET.get("q", "").strip()
    type_id = request.GET.get("type")
    assigned_id = request.GET.get("assigned")
    status = request.GET.get("status", "")  # new status filter

    qs = Asset.objects.select_related("type", "alloted_to").all()

    if q:
        qs = qs.filter(
            Q(make_model__icontains=q)
            | Q(serial_number__icontains=q)
            | Q(type__name__icontains=q)
            | Q(alloted_to__first_name__icontains=q)
            | Q(alloted_to__last_name__icontains=q)
        )

    if type_id:
        try:
            qs = qs.filter(type__id=int(type_id))
        except (ValueError, TypeError):
            pass

    if assigned_id:
        # support assigned=true (show all assigned assets) or an employee id
        aid = str(assigned_id).lower()
        if aid in ("1", "true", "yes", "assigned"):
            qs = qs.filter(alloted_to__isnull=False)
        else:
            try:
                qs = qs.filter(alloted_to__id=int(assigned_id))
            except (ValueError, TypeError):
                # invalid assigned value — ignore the filter
                pass

    # apply status/condition filter if present
    if status:
        qs = qs.filter(condition__iexact=status)

    # for building filter dropdowns
    types = (
        Asset.objects.select_related("type").values("type__id", "type__name").distinct()
    )
    employees = Employee.objects.all()

    # statuses from model choices (list of (value,label))
    statuses = Asset._meta.get_field("condition").choices

    context = {
        "assets": qs,
        "q": q,
        "type_id": type_id,
        "assigned_id": assigned_id,
        "status": status,
        "types": types,
        "employees": employees,
        "statuses": statuses,
    }
    return render(request, "assets/asset_list.html", context)


@login_required
def asset_detail(request, pk):
    """View a single asset's details."""
    asset = get_object_or_404(Asset.objects.select_related("type", "alloted_to"), pk=pk)
    return render(request, "assets/asset_detail.html", {"asset": asset})


@login_required
def asset_create(request):
    if request.method == "POST":
        form = AssetForm(request.POST)
        formset = AssetDocumentFormSet(request.POST, request.FILES)
        if form.is_valid() and formset.is_valid():
            asset = form.save()
            formset.instance = asset
            formset.save()
            messages.success(request, "Asset created successfully.")
            return redirect("asset_detail", pk=asset.pk)
    else:
        form = AssetForm()
        formset = AssetDocumentFormSet()
    return render(request, "assets/asset_form.html", {"form": form, "formset": formset, "form_title": "Add Asset"})

@login_required
def asset_update(request, pk):
    asset = get_object_or_404(Asset, pk=pk)
    if request.method == "POST":
        form = AssetForm(request.POST, instance=asset)
        formset = AssetDocumentFormSet(request.POST, request.FILES, instance=asset)
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            messages.success(request, "Asset updated successfully.")
            return redirect("asset_detail", pk=asset.pk)
    else:
        form = AssetForm(instance=asset)
        formset = AssetDocumentFormSet(instance=asset)
    return render(
        request,
        "assets/asset_form.html",
        {"form": form, "formset": formset, "form_title": "Edit Asset"},
    )

@login_required
def asset_delete(request, pk):
    """Delete an asset."""
    asset = get_object_or_404(Asset, pk=pk)

    # Only allow users with delete permission
    if not request.user.has_perm("assets.delete_asset"):
        return HttpResponseForbidden("You do not have permission to delete assets.")

    if request.method == "POST":
        asset.delete()
        messages.success(request, "Asset deleted successfully.")
        return redirect("asset_list")

    return render(request, "assets/asset_confirm_delete.html", {"asset": asset})

@login_required
def export_current_data(request):
    if not request.user.is_staff:
        return HttpResponseForbidden("Only admin can export data.")

    # Define the peripheral types as used in import
    PERIPHERAL_TYPES = ["Monitor", "Keyboard and Mouse", "UPS", "Printer", "Speaker"]

    header = (
        "Sl.No.,Alloted To,Device,Make model,Serial No.,PROCESSOR,RAM,HDD,SSD,OS,Year of Purchase,"
        "Monitor,Monitor Serial number,Monitor Year of Purchase,"
        "Keyboard and Mouse,UPS,UPS Serial number,UPS Year of Purchase,"
        "Printer,Printer Serial number,Printer Year of Purchase,"
        "Speaker,Condition,REMARKS\n"
    )
    output = StringIO()
    output.write(header)

    # Main assets are those whose type is not in peripheral types.
    main_assets = (
        Asset.objects.select_related("type", "alloted_to")
        .exclude(type__name__in=PERIPHERAL_TYPES)
        .all()
    )

    counter = 1
    for asset in main_assets:
        # Alloted To: If exists, combine first and last name.
        alloted = ""
        if asset.alloted_to:
            alloted = f"{asset.alloted_to.first_name} {asset.alloted_to.last_name}"

        # Main asset fields:
        # For export we use:
        #   Device: asset.type.name
        #   Make model: (here, we output the asset type – as per your import mapping, this field
        #               is used for lookup and must match the import sample)
        #   Serial No.: asset.serial_number
        #   PROCESSOR: asset.make_model (contains processor info)
        #   RAM, HDD, SSD, OS, Year of Purchase as stored.
        main_device = asset.type.name if asset.type else ""
        main_make_model = asset.type.name if asset.type else ""
        serial_no = asset.serial_number or ""
        processor = asset.make_model or ""
        ram = asset.ram or ""
        hdd = asset.hdd or ""
        ssd = asset.ssd or ""
        os_val = asset.os or ""
        yop = str(asset.year_of_purchase) if asset.year_of_purchase else ""

        # For Condition and REMARKS, output composite values in the format: "<AssetType>: Value"
        condition_comp = f"{asset.type.name}: {asset.condition}" if asset.type and asset.condition else (asset.condition or "")
        remarks_comp = f"{asset.type.name}: {asset.remarks}" if asset.type and asset.remarks else (asset.remarks or "")

        # For peripherals, we try to find an asset (for the same employee) of that type.
        peripheral_values = {}
        if asset.alloted_to:
            for p in PERIPHERAL_TYPES:
                periph = (
                    Asset.objects.filter(alloted_to=asset.alloted_to, type__name=p)
                    .order_by("id")
                    .first()
                )
                if periph:
                    peripheral_values[p] = {
                        "make_model": periph.make_model or "",
                        "serial_number": periph.serial_number or "",
                        "year": str(periph.year_of_purchase) if periph.year_of_purchase else "",
                    }
                else:
                    peripheral_values[p] = {"make_model": "", "serial_number": "", "year": ""}
        else:
            for p in PERIPHERAL_TYPES:
                peripheral_values[p] = {"make_model": "", "serial_number": "", "year": ""}

        row = [
            str(counter),
            alloted,
            main_device,
            main_make_model,
            serial_no,
            processor,
            ram,
            hdd,
            ssd,
            os_val,
            yop,
            # Monitor
            peripheral_values["Monitor"]["make_model"],
            peripheral_values["Monitor"]["serial_number"],
            peripheral_values["Monitor"]["year"],
            # Keyboard and Mouse
            peripheral_values["Keyboard and Mouse"]["make_model"],
            # UPS
            peripheral_values["UPS"]["make_model"],
            peripheral_values["UPS"]["serial_number"],
            peripheral_values["UPS"]["year"],
            # Printer
            peripheral_values["Printer"]["make_model"],
            peripheral_values["Printer"]["serial_number"],
            peripheral_values["Printer"]["year"],
            # Speaker
            peripheral_values["Speaker"]["make_model"],
            # Condition and REMARKS for main asset
            condition_comp,
            remarks_comp,
        ]
        output.write(",".join(row) + "\n")
        counter += 1

    response = HttpResponse(output.getvalue(), content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="exported_assets.csv"'
    return response