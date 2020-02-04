from django.urls import path
from .views import *

app_name = "company"
urlpatterns = [
    path("configuration/", ConfigView.as_view(), name="config"),
    path("roles/", RoleListView.as_view(), name="roles"),
    path("roles/add/", CreateRoleView.as_view(), name="add-roles"),
    path("roles/delete/<int:pk>/", DeleteRole.as_view(), name="delete-role"),
    path("roles/edit/<int:pk>/", UpdateRoleView.as_view(), name="edit-role"),
    path("roles/view/<int:pk>/", RoleDetailView.as_view(), name="view-role"),
    path("departments/", DepartmentListView.as_view(), name="departments"),
    path("departments/add/", CreateDepartmentView.as_view(), name="add-departments"),
    path("departments/delete/<int:pk>/", DeleteDepartment.as_view(), name="delete-department"),
    path("departments/edit/<int:pk>/", UpdateDepartmentView.as_view(), name="edit-department"),
    path("departments/view/<int:pk>/", DepartmentDetailView.as_view(), name="view-department"),
    path("members/", StaffListView.as_view(), name="members"),
    path("members/add/", CreateMemberView.as_view(), name="add-members"),
    path("members/delete/<int:pk>/", DeleteMember.as_view(), name="delete-member"),
    path("members/edit/<int:pk>/", UpdateMemberView.as_view(), name="edit-member"),
    path("members/view/<int:pk>/", MemberDetailView.as_view(), name="view-member"),
    path("members/pips-report/<int:pk>/", download_bulk_pip_report, name="download_bulk_pip_report"),
    path("members/kras-report/<int:pk>/", download_bulk_kra_report, name="download_bulk_kra_report"),
    path("members/tasks-report/<int:pk>/", download_task_report, name="download_task_report"),
]
