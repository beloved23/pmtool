import datetime
import time
from datetime import timedelta

from django.db import models
from django.utils import timezone

from account.models import Profile


class Task(models.Model):
    created_by = models.ForeignKey(Profile, on_delete=models.SET_NULL, null=True, blank=True, related_name="my_tasks")
    assigned_to = models.ForeignKey(Profile, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name="todo_tasks", verbose_name="Assign To",
                                    help_text="Leave empty to assign task to yourself")
    title = models.CharField(max_length=255)
    status = models.CharField(max_length=50, default="Pending")
    content = models.TextField(verbose_name="description")
    reference = models.CharField(max_length=30, unique=True)
    duration = models.PositiveIntegerField(default=1, help_text="How long this task should take in hours")
    seen = models.BooleanField(default=False)
    date_completed = models.DateTimeField(null=True, blank=True)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-pk", )

    @property
    def end_time(self):
        return self.date_created + timedelta(hours=self.duration)

    @property
    def out_of_time(self):
        return timezone.now() > self.end_time

    def save(self, *args, **kwargs):
        if not self.reference:
            self.reference = str(time.time()).replace(".", "")
        if not self.assigned_to:
            self.seen = True
        super(Task, self).save(*args, **kwargs)
