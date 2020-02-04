import base64
import os
import time

from django.contrib.auth.models import AbstractUser, User
from django.db import models
from django.db.models import Q
from django.urls import reverse

from HRTool import settings


def profile_upload_file_path(instance, filename):
    f, ext = os.path.splitext(filename)
    path = '%s/%s%s' % (instance.company.identifier, instance.auuid, ext)
    if os.path.isfile(settings.MEDIA_ROOT + path) and os.path.exists(settings.MEDIA_ROOT + path):
        os.remove(path)
    return path


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    auuid = models.CharField(max_length=20, verbose_name="Username")
    phone = models.CharField(max_length=11)
    photo = models.ImageField(upload_to=profile_upload_file_path)
    gender = models.CharField(max_length=20, null=False, blank=False, default="-")
    appointment_date = models.DateField(null=False, blank=False)
    company = models.ForeignKey("company.Company", on_delete=models.SET_NULL, null=True, blank=True, related_name="members")
    department = models.ForeignKey("company.Department", on_delete=models.SET_NULL, null=True, blank=True, related_name="members")
    role = models.ForeignKey("company.Role", on_delete=models.SET_NULL, null=True, blank=True, related_name="members")
    manager = models.ForeignKey("self", on_delete=models.SET_NULL, null=True, blank=True, related_name="child_members")
    is_ceo = models.BooleanField(default=False)
    password_changed = models.BooleanField(default=False)
    token = models.CharField(max_length=100, null=True, blank=True)
    date_updated = models.DateTimeField(auto_now=True)
    date_created = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = (("auuid", "company"), )

    @property
    def first_name(self):
        return self.user.first_name

    @property
    def last_name(self):
        return self.user.last_name

    @property
    def tasks(self):
        from task.models import Task
        return Task.objects.filter(Q(created_by=self) | Q(assigned_to=self))

    @property
    def completed_tasks(self):
        return self.tasks.filter(status="Completed")

    @property
    def pending_tasks(self):
        return self.tasks.filter(status="Pending")

    @property
    def unseen_tasks(self):
        return self.pending_tasks.filter(seen=False)

    def __str__(self):
        return "{0} ({1})".format(self.user.get_full_name().title(), self.auuid.upper())

    def get_absolute_url(self):
        return reverse('company:view-member', args=[str(self.pk)])

    def get_last_submitted_kra(self):
        return self.user.kras.filter(is_draft=False).first()

    def save(self, *args, **kwargs):
        if not self.token:
            self.token = base64.b64encode(("%s" % time.time()).encode("utf-8")).decode("utf-8")
        super(Profile, self).save(*args, **kwargs)

    @property
    def get_tasks_progress(self):
        completed = self.completed_tasks.count() * 100
        total = self.tasks.count()
        return (completed / total) if total > 0 else 0

    @property
    def pip_progress(self):
        count = self.user.pips.count() * 100
        total = self.company.config.pip_threshold or 2
        return (count / total) if total > 0 else 0
