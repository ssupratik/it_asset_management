from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

urlpatterns = [
    path("", views.dashboard_view, name="dashboard"),  # homepage
    path("assets/", views.asset_list, name="asset_list"),
    path("assets/create/", views.asset_create, name="asset_create"),
    path("<int:pk>/", views.asset_detail, name="asset_detail"),
    path("employees/", views.employee_list, name="employee_list"),
    path("employees/create/", views.employee_create, name="employee_create"),
    path("assets/history/", views.asset_history_list, name="asset_history_list"),
    path(
        "login/",
        auth_views.LoginView.as_view(template_name="assets/login.html"),
        name="login",
    ),
    path("logout/", auth_views.LogoutView.as_view(next_page="login"), name="logout"),
]
