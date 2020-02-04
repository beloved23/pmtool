from django.urls import path
from .views import *

app_name = "task"
urlpatterns = [
    path("", TasksManagementView.as_view(), name="management"),
    path("update/<str:reference>", update_task, name="update"),
]
