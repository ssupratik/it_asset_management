# views/dashboard.py
from django.db.models import Count, Prefetch, Q
from django.shortcuts import render

from assets.models import Asset, AssetHistory, Employee


def dashboard(request):
    q = request.GET.get("q", "").strip()

    total_assets = Asset.objects.count() or 0
    assigned_assets = Asset.objects.filter(alloted_to__isnull=False).count() or 0
    damaged_assets = Asset.objects.filter(condition__iexact="damaged").count() or 0
    under_repair = Asset.objects.filter(condition__icontains="repair").count() or 0
    disposed_assets = Asset.objects.filter(condition__icontains="disposed").count() or 0

    # recent history (keep if needed elsewhere)
    recent_history = AssetHistory.objects.select_related("asset", "employee").order_by(
        "-timestamp"
    )[:5]

    # Build a base asset queryset (used to derive employee-related data)
    base_asset_qs = Asset.objects.select_related("type", "alloted_to").all()
    if q:
        base_asset_qs = base_asset_qs.filter(
            Q(make_model__icontains=q)
            | Q(serial_number__icontains=q)
            | Q(type__name__icontains=q)
        )

    # Get set of employee ids that match via assigned assets
    asset_emp_ids = list(
        base_asset_qs.values_list("alloted_to_id", flat=True).distinct()
    )
    # Employee queryset: include employees whose name matches q OR who have matching assets
    employees_qs = Employee.objects.all()
    if q:
        employees_qs = employees_qs.filter(
            Q(pk__in=[i for i in asset_emp_ids if i])  # filter out None
            | Q(first_name__icontains=q)
            | Q(last_name__icontains=q)
        ).distinct()

    # determine the reverse accessor name for Asset.alloted_to dynamically
    accessor = Asset._meta.get_field("alloted_to").remote_field.get_accessor_name()
    employees_qs = employees_qs.prefetch_related(
        Prefetch(accessor, queryset=Asset.objects.select_related("type"))
    )

    employees_data = []
    for idx, emp in enumerate(employees_qs, start=1):
        # assets assigned to this employee (from prefetch) using dynamic accessor
        assigned_assets_manager = getattr(emp, accessor, None)
        assigned_assets_qs = (
            list(assigned_assets_manager.all()) if assigned_assets_manager else []
        )
        asset_count = len(assigned_assets_qs)

        # per-condition counts for this employee
        damaged_count = 0
        repair_count = 0
        disposed_count = 0
        for a in assigned_assets_qs:
            cond = (a.condition or "").lower()
            if cond == "damaged":
                damaged_count += 1
            elif "repair" in cond:
                repair_count += 1
            elif "disposed" in cond:
                disposed_count += 1

        # sample asset names (up to 3)
        sample_assets = [a.make_model or "-" for a in assigned_assets_qs[:3]]

        # categories assigned (unique)
        categories = []
        seen = set()
        for a in assigned_assets_qs:
            t = getattr(a, "type", None)
            if t and t.id not in seen:
                seen.add(t.id)
                categories.append({"id": t.id, "name": t.name or "-"})

        employees_data.append(
            {
                "sl": idx,
                "id": emp.id,
                "name": f"{emp.first_name or ''} {emp.last_name or ''}".strip() or "-",
                "asset_count": asset_count,
                "sample_assets": sample_assets,
                "categories": categories,
                "damaged_count": damaged_count,
                "repair_count": repair_count,
                "disposed_count": disposed_count,
            }
        )

    context = {
        "total_assets": total_assets,
        "assigned_assets": assigned_assets,
        "damaged_assets": damaged_assets,
        "under_repair": under_repair,
        "disposed_assets": disposed_assets,
        "recent_history": recent_history,
        "employees_data": employees_data,
        "q": q,
    }
    return render(request, "assets/dashboard.html", context)
