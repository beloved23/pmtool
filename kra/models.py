import time

from django.contrib.auth.models import User
from django.db import models
from django.urls import reverse
import datetime

from HRTool import constants
from company.models import Company, Rating


class KraBucket(models.Model):
    title = models.CharField(max_length=255)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="kra_buckets")
    reference = models.CharField(max_length=30, null=True, blank=True, editable=False, unique=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name="buckets_created")
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name="buckets_updated")
    # kra_setting_duration = models.PositiveIntegerField(default=1,
    #                                                    help_text="How long this bucket should be open for staff members to set their KRA")
    # mid_year_assessment_month = models.CharField(max_length=30, help_text="When this bucket should open for staff members' self-assessment")
    # mid_year_assessment_duration = models.PositiveIntegerField(default=1, help_text="How long this bucket should be open for staff members' self-assessment")
    # final_assessment_month = models.CharField(max_length=30, help_text="When this bucket should open for staff members' final assessment")
    # final_assessment_duration = models.PositiveIntegerField(default=1, help_text="How long this bucket should be open for staff members' final assessment")
    status = models.CharField(max_length=30, choices=constants.KRA_BUCKET_STATUSES,
                              default=constants.KRA_BUCKET_OPEN_STATUS)
    year = models.IntegerField(default=datetime.datetime.now().date().year)
    allow_self_assessment = models.BooleanField(default=False)
    allow_final_assessment = models.BooleanField(default=False)
    date_updated = models.DateTimeField(auto_now=True)
    date_created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-pk", )
        unique_together = (("company", "year"), )

    def get_absolute_url(self):
        return reverse("kra:view-kra-bucket", args=(self.reference,))

    def __str__(self):
        return self.company.name+" "+self.title

    def save(self, *args, **kwargs):
        if not self.reference:
            self.reference = str(time.time()).replace(".", "")
        if not self.title:
            self.title = "Financial Year %s" % self.year
        super(KraBucket, self).save(*args, **kwargs)


class CompanyKra(models.Model):
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="kras")
    bucket = models.OneToOneField(KraBucket, on_delete=models.CASCADE, related_name="company_kra")
    identifier = models.CharField(max_length=30, null=True, blank=True, unique=True)
    is_draft = models.BooleanField(default=False)
    status = models.CharField(max_length=30, choices=constants.KRA_STATUSES, default=constants.KRA_LOCKED_STATUS)
    date_updated = models.DateTimeField(auto_now=True)
    date_created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-pk",)

    def get_absolute_url(self):
        return reverse("kra:view-company-kra", args=(self.identifier,))

    @property
    def bucket_title(self):
        return self.bucket.title

    def save(self, *args, **kwargs):
        if not self.identifier:
            self.identifier = str(time.time()).replace(".", "")
        super(CompanyKra, self).save(*args, **kwargs)


class CompanyKraItem(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(null=False, blank=False)
    weight = models.FloatField()
    target = models.FloatField()
    actual = models.FloatField(null=True, blank=True)
    kra = models.ForeignKey(CompanyKra, on_delete=models.CASCADE, related_name="items")
    # comment = models.TextField(null=True, blank=True)
    date_created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("pk", )


class Kra(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="kras")
    bucket = models.ForeignKey(KraBucket, on_delete=models.CASCADE, related_name="kras", null=True, blank=True)
    identifier = models.CharField(max_length=30, null=True, blank=True, unique=True)
    rating = models.ForeignKey(Rating, null=True, blank=True, on_delete=models.SET_NULL)
    hod_rating = models.ForeignKey(Rating, null=True, blank=True, on_delete=models.SET_NULL, related_name="hod_rating_kras")
    is_accepted = models.BooleanField(default=False)
    is_draft = models.BooleanField(default=False)
    self_assessed = models.BooleanField(default=False)
    status = models.CharField(max_length=30, choices=constants.KRA_STATUSES, default=constants.KRA_LOCKED_STATUS)
    date_updated = models.DateTimeField(auto_now=True)
    date_created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-pk", )

    @property
    def manager_kra(self):
        try:
            return Kra.objects.get(user=self.user.profile.manager.user, bucket=self.bucket, status__in=[
                constants.KRA_LOCKED_STATUS, constants.KRA_OPEN_STATUS, constants.KRA_CLOSED_STATUS], is_draft=False)
        except Kra.DoesNotExist:
            return None

    def get_absolute_url(self):
        return reverse("kra:view-kra", args=(self.identifier,))

    @property
    def bucket_title(self):
        return self.bucket.title

    def save(self, *args, **kwargs):
        if not self.identifier:
            self.identifier = str(time.time()).replace(".", "")
        super(Kra, self).save(*args, **kwargs)

    @property
    def profile(self):
        return self.user.profile


class KraItem(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(null=False, blank=False)
    weight = models.FloatField()
    target = models.FloatField()
    actual = models.FloatField(null=True, blank=True)
    achievement = models.FloatField(null=True, blank=True, verbose_name="Achievement %")
    manager_achievement = models.FloatField(null=True, blank=True, verbose_name="Manager's achievement %")
    kra = models.ForeignKey(Kra, on_delete=models.CASCADE, related_name="items")
    comment = models.TextField(null=True, blank=True)
    manager_comment = models.TextField(null=True, blank=True, verbose_name="Manager's comment")
    date_created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("pk", )


class Message(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="messages")
    kra = models.ForeignKey(Kra, on_delete=models.CASCADE, related_name="messages")
    file = models.FileField(null=True, blank=True)
    file_type = models.CharField(null=True, blank=True, max_length=100)
    filename = models.CharField(null=True, blank=True, max_length=255)
    text = models.TextField(null=True, blank=True)
    read = models.BooleanField(default=False)
    date_created = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("pk", )

    @property
    def profile(self):
        return self.user.profile
