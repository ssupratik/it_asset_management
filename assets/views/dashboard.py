# views/dashboard.py
from django.shortcuts import render
from assets.models import Asset, AssetHistory, Employee

def dashboard(request):
    total_assets = Asset.objects.count()
    total_employees = Employee.objects.count()
    recent_history = AssetHistory.objects.select_related('asset', 'employee').order_by('-transfer_date')[:5]

    context = {
        'total_assets': total_assets,
        'total_employees': total_employees,
        'recent_history': recent_history,
    }
    return render(request, 'dashboard.html', context)
