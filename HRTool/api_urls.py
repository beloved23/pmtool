from django.urls import path
from fcm_django.api.rest_framework import FCMDeviceAuthorizedViewSet

from account.api_views import LoginView, LogoutView, ChangePasswordView, DashboardView, NotificationsAPIView, \
    ViewMemberProfile
from company.api_views import CompanyConfigView, CompanyRatingList
from kra.api_views import KraBucketAPIView, KraCreateAPIView, KraUpdateAPIView, KraMessagesAPIView, \
    KraDeleteAPIView, KraSelfAssessmentAPIView, KraToggleAPIView, KraAssessmentAPIView, KraHodRatingAPIView
from p_i_p.api_views import PipCreateAPIView
from task.api_views import CreateTaskAPIView, UpdateTaskAPIView, TaskListAPIView

from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'devices', FCMDeviceAuthorizedViewSet)

urlpatterns = [
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("change-password/", ChangePasswordView.as_view(), name="change-password"),
    path("dashboard/", DashboardView.as_view(), name="dashboard"),
    path("notifications/", NotificationsAPIView.as_view(), name="notifications"),
    path("company-ratings/", CompanyRatingList.as_view(), name="company-ratings"),
    path("company-config/<str:identifier>/", CompanyConfigView.as_view(), name="company-config"),
    path("view-profile/<int:id>/", ViewMemberProfile.as_view(), name="view-profile"),
    path("task/list/", TaskListAPIView.as_view(), name="list-tasks"),
    path("task/create/", CreateTaskAPIView.as_view(), name="create-task"),
    path("task/update/<str:reference>/", UpdateTaskAPIView.as_view(), name="update-task"),
    path("kra/create/", KraCreateAPIView.as_view(), name="create-kra"),
    path("kra/update/<str:identifier>/", KraUpdateAPIView.as_view(), name="update-kra"),
    path("kra/messages/<str:identifier>/", KraMessagesAPIView.as_view(), name="kra-messages"),
    path("kra/delete/<str:identifier>/", KraDeleteAPIView.as_view(), name="delete-kra"),
    path("kra/self-assessment/<str:identifier>/", KraSelfAssessmentAPIView.as_view(), name="kra-self-assess"),
    path("kra/assessment/<str:identifier>/", KraAssessmentAPIView.as_view(), name="kra-assess"),
    path("kra/toggle/<str:identifier>/", KraToggleAPIView.as_view(), name="kra-toggle"),
    path("kra/buckets/", KraBucketAPIView.as_view(), name="kra-buckets"),
    path("kra/buckets/<str:reference>/", KraBucketAPIView.as_view(), name="view-kra-bucket"),
    path("kra/hod-rating/<str:identifier>/", KraHodRatingAPIView.as_view(), name="kra-hod-rating"),
    path("pip/create/", PipCreateAPIView.as_view(), name="create-pip"),
] + router.urls
