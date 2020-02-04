from rest_framework import serializers

from account.serializers import ProfileSerializer
from task.models import Task


class TaskSerializer(serializers.ModelSerializer):
    created_by = ProfileSerializer()
    assigned_to = ProfileSerializer()

    class Meta:
        model = Task
        fields = "__all__"


class CreateTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = ("title", "content", "assigned_to", "duration")


class UpdateTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = ("status", )

    def validate(self, attrs):
        if self.context["request"].user.profile not in [self.instance.assigned_to, self.instance.created_by]:
            raise serializers.ValidationError("Task could not be found")
        if attrs["status"].lower() not in ["cancelled", "completed"]:
            raise serializers.ValidationError("Invalid status")
        if self.instance.status != "Pending":
            raise serializers.ValidationError("Sorry, task could not be updated")
        return attrs
