from django.urls import path
from .views import *

app_name = "kra"
urlpatterns = [
    path("configuration/", KRAConfigView.as_view(), name="configuration"),
    path("company-setting/", CompanyKRASettingView.as_view(), name="company-setting"),
    path("setting/", KRASettingView.as_view(), name="setting"),
    path("report/<str:kra_identifier>/", download_kra_report, name="download_kra_report"),
    path("bucket-report/<str:reference>/", download_bucket_report, name="download_bucket_report"),
    path("setting/<str:kra_identifier>/", KRASettingView.as_view(), name="setting"),
    path("assessment/<str:kra_identifier>/", KRAAssessmentView.as_view(), name="assessment"),
    path("self-assessment/<str:kra_identifier>/", KRASelfAssessmentView.as_view(), name="self-assessment"),
    path("company-setting/<str:kra_identifier>/", CompanyKRASettingView.as_view(), name="company-setting"),
    path("management/", KRAManagementView.as_view(), name="management"),
    path("management/<str:reference>/", KRAManagementView.as_view(), name="management"),
    # path("send-message/<int:pk>/", KRASettingView.as_view(), name="send-message"),
    path("member/<int:pk>/", KRASettingView.as_view(), name="view-member-kras"),
    path("view-bucket/<str:reference>/", KRABucketView.as_view(), name="view-kra-bucket"),
    path("toggle-bucket/<str:reference>/", KRABucketToggle.as_view(), name="toggle-kra-bucket"),
    path("view/<str:kra_identifier>/", KRADetailView.as_view(), name="view-kra"),
    path("delete/<str:kra_identifier>/", DeleteKRA.as_view(), name="delete-kra"),
    path("company/<str:kra_identifier>/", CompanyKRADetailView.as_view(), name="view-company-kra"),
]
