from django.urls import path
from .views import *

app_name = "p_i_p"
urlpatterns = [
    path("create/<str:auuid>/", PipCreateView.as_view(), name="create"),
    path("management/", PipManagementView.as_view(), name="management"),
    path("view/<str:reference>/", PipDetailView.as_view(), name="view"),
    path("report/<str:reference>/", download_pip_report, name="download_pip_report"),
]
