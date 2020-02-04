from django.urls import path
from .views import *

app_name = "superuser"
urlpatterns = [
    path("", LoginView.as_view(), name="login"),
    path("logout/", logout, name="logout"),
    path("dashboard/", DashboardView.as_view(), name="dashboard"),

    path("companies/", CompanyListView.as_view(), name="companies"),
    path("companies/add/", CompanyCreateView.as_view(), name="add-company"),
    path("companies/view/<int:pk>/", CompanyDetailView.as_view(), name="view-company"),
    path("companies/subscribe/<int:pk>/", create_company_subscription, name="subscribe-company"),
    path("companies/toggle-status/<int:pk>/", toggle_company_status, name="toggle-company-status"),
    path("companies/delete/<int:pk>/", delete_company, name="delete-company"),
    path("companies/edit/<int:pk>/", CompanyUpdateView.as_view(), name="edit-company"),

    path("plans/", PlanListView.as_view(), name="plans"),
    path("plans/add/", PlanCreateView.as_view(), name="add-plans"),
    path("plans/delete/<int:pk>/", delete_plan, name="delete-plan"),
    path("plans/edit/<int:pk>/", PlanUpdateView.as_view(), name="edit-plan"),

    path("users/", SuperuserListView.as_view(), name="users"),
    path("users/add/", SuperuserCreateView.as_view(), name="add-user"),
    path("users/toggle-status/<int:pk>/", toggle_superuser_status, name="toggle-user-status"),
    path("users/delete/<int:pk>/", delete_user, name="delete-user"),
    path("users/edit/<int:pk>/", SuperuserUpdateView.as_view(), name="edit-user"),
    # path("plans/add/", toggle_company_status, name="add-plans"),
]
