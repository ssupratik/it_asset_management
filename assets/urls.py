from django.contrib.auth import views as auth_views
from django.urls import path

from .views.asset import (
    asset_create,
    asset_delete,
    asset_detail,
    asset_list,
    asset_update,
    export_current_data,
    upload_document
)
from .views.dashboard import dashboard
from .views.employee import (
    employee_create,
    employee_delete,
    employee_edit,
    employee_list,
)
from .views.history import history_detail, history_list
from .views.upload import bulk_upload, download_sample_csv
urlpatterns = [
    path("", dashboard, name="dashboard"),
    # Employee
    path("employees/", employee_list, name="employee_list"),
    path("employees/create/", employee_create, name="employee_create"),
    path("employees/<int:pk>/edit/", employee_edit, name="employee_edit"),
    path("employees/<int:pk>/delete/", employee_delete, name="employee_delete"),
    # Asset
    path("assets/", asset_list, name="asset_list"),
    path("assets/create/", asset_create, name="asset_create"),
    path("assets/<int:pk>/", asset_detail, name="asset_detail"),
    path("assets/<int:pk>/edit/", asset_update, name="asset_update"),
    path("assets/<int:pk>/delete/", asset_delete, name="asset_delete"),
    # History
    path("history/", history_list, name="history_list"),
    path("history/<int:pk>/", history_detail, name="history_detail"),
    path("bulk-upload/", bulk_upload, name="bulk_upload"),
    path("download-sample-csv/", download_sample_csv, name="download_sample_csv"),
    path("export-data/", export_current_data, name="export_current_data"),
    path("assets/<int:asset_id>/upload-document/", upload_document, name="upload_document"),
    # Auth
    path(
        "login/",
        auth_views.LoginView.as_view(template_name="assets/login.html"),
        name="login",
    ),
    path("logout/", auth_views.LogoutView.as_view(next_page="login"), name="logout"),

]
