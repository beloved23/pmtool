import os

from dateutil.relativedelta import relativedelta
from django.contrib.auth.models import User
from django.urls import reverse
from django.db import models
import datetime

from HRTool import settings, constants
from account.models import Profile


class Company(models.Model):
    name = models.CharField(max_length=255)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    # token = models.CharField(max_length=100, default=base64.b64encode(("%s" % time()).encode("utf-8")).decode("utf-8"))
    identifier = models.CharField(max_length=10, null=False, blank=False, unique=True)
    is_active = models.BooleanField(default=True)
    date_updated = models.DateTimeField(auto_now=True, null=True, blank=True)
    date_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    def __unicode__(self):
        return self.name

    def plan(self):
        if self.config.subscription is None:
            return None
        return self.config.subscription.plan

    def expires_soon(self):
        next_month = datetime.datetime.now().date() + relativedelta(months=1)
        expiry = self.config.subscription.expiry
        if expiry <= next_month:
            return (next_month - expiry).days
        return None

    def get_plan_usage(self):
        plan = self.plan()
        return ((self.members.count()/(plan.threshold if not plan.is_flexible else 1000)) if plan else 0) * 100

    def get_ceo(self):
        try:
            return self.members.get(is_ceo=True)
        except Profile.DoesNotExist:
            return None

    def get_hrd(self):
        try:
            return self.members.get(user__is_staff=True, is_ceo=False)
        except Profile.DoesNotExist:
            return None

    def get_absolute_url(self):
        return reverse('superuser:view-company', args=[str(self.id)])

    @property
    def open_buckets(self):
        return self.kra_buckets.filter(status=constants.KRA_BUCKET_OPEN_STATUS)

    @property
    def last_bucket(self):
        return self.kra_buckets.latest("date_created")


class Department(models.Model):
    name = models.CharField(max_length=255)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="departments")
    director = models.OneToOneField(Profile, on_delete=models.SET_NULL, null=True, blank=True, related_name="directing_department")
    date_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    def __unicode__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('company:view-department', args=[str(self.id)])


class Role(models.Model):
    name = models.CharField(max_length=200)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="roles")
    date_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    def __unicode__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('company:view-role', args=[str(self.id)])


def logo_upload_file_path(instance, filename):
    f, ext = os.path.splitext(filename)
    path = '%s/logo%s' % (instance.company.identifier, ext)
    if os.path.isfile(settings.MEDIA_ROOT + path) and os.path.exists(settings.MEDIA_ROOT + path):
        os.remove(path)
    return path


def bg_upload_file_path(instance, filename):
    f, ext = os.path.splitext(filename)
    path = '%s/background_image%s' % (instance.company.identifier, ext)
    if os.path.isfile(settings.MEDIA_ROOT + path) and os.path.exists(settings.MEDIA_ROOT + path):
        os.remove(path)
    return path


class Config(models.Model):
    from superuser.models import Subscription
    company = models.OneToOneField(Company, on_delete=models.CASCADE, related_name="config")
    logo = models.ImageField(null=True, blank=True, upload_to=logo_upload_file_path)
    theme = models.CharField(max_length=20, null=True, blank=True)
    background_image = models.ImageField(null=True, blank=True, upload_to=bg_upload_file_path)
    subscription = models.ForeignKey(Subscription, on_delete=models.SET_NULL, null=True, blank=True)
    # year_start = models.CharField(max_length=30, null=True, blank=True)
    pip_threshold = models.IntegerField(default=2,
                                        help_text="Maximum number of PIP allowed per staff before advised to withdraw")
    date_updated = models.DateTimeField(auto_now=True)
    date_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return "{}'s config".format(self.company.name)


class Rating(models.Model):
    config = models.ForeignKey(Config, on_delete=models.CASCADE, related_name="ratings")
    name = models.CharField(max_length=50)
    threshold = models.FloatField()
    date_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return "%s" % self.name

