from django.urls import path

from .views.asset import asset_create, asset_list
from .views.dashboard import dashboard
from .views.employee import employee_create, employee_list
from .views.history import history_create, history_list

urlpatterns = [
    path("", dashboard, name="dashboard"),
    # Employee
    path("employees/", employee_list, name="employee_list"),
    path("employees/create/", employee_create, name="employee_create"),
    # Asset
    path("assets/", asset_list, name="asset_list"),
    path("assets/create/", asset_create, name="asset_create"),
    # History
    path("history/", history_list, name="history_list"),
    path("history/create/", history_create, name="history_create"),
]
