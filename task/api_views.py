import datetime

from django.template.loader import render_to_string
from rest_framework.generics import CreateAPIView, UpdateAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from HRTool import utils
from HRTool.notifications import NotificationManager
from task.models import Task
from task.serializers import CreateTaskSerializer, UpdateTaskSerializer, TaskSerializer


class TaskListAPIView(APIView):
    def get(self, request, *args, **kwargs):
        return Response(utils.build_response(True, None, TaskSerializer(request.user.profile.tasks, many=True).data))


class CreateTaskAPIView(CreateAPIView):
    serializer_class = CreateTaskSerializer

    def create(self, request, *args, **kwargs):
        super(CreateTaskAPIView, self).create(request, *args, **kwargs)
        return Response(utils.build_response(True, "Task created successfully", []))

    def perform_create(self, serializer):
        task = serializer.save(created_by=self.request.user.profile)
        data = serializer.validated_data
        if data.get('assigned_to', None) and data['assigned_to'].user != self.request.user:
            NotificationManager.task_creation_notification(self.request, task)


class UpdateTaskAPIView(UpdateAPIView):
    serializer_class = UpdateTaskSerializer
    lookup_field = "reference"
    lookup_url_kwarg = "reference"
    queryset = Task.objects.filter(status="Pending")

    def update(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_object(), data=request.data)
        if serializer.is_valid():
            validated_data = serializer.validated_data
            task = self.perform_update(serializer)
            # task = self.get_object()
            if task.status.lower() == "completed":
                task.date_completed = datetime.datetime.now()
                task.save()
            if task.assigned_to:
                NotificationManager.task_update_notification(request, task)
            return Response(utils.build_response(True, "Task %s successfully" % validated_data["status"].lower(), TaskSerializer(task).data))
        return Response(utils.build_response(False, None, serializer.errors))

    def perform_update(self, serializer):
        return serializer.save()
