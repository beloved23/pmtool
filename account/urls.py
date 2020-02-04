from django.urls import path
from .views import *

urlpatterns = [
    path("", LoginView.as_view(), name="login"),
    path("test-mail/", test_mail, name="test-mail"),
    path("logout/", logout, name="logout"),
    path("change-password/", PasswordChangeView.as_view(), name="change-password"),
    path("dashboard/", DashboardView.as_view(), name="dashboard"),
    path("activation/<str:auuid>/<str:token>/", activate_account, name="account-activation"),
    path("<str:company_identifier>/", LoginView.as_view(), name="custom-login"),
]
