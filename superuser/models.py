from django.contrib.auth.models import User
from django.db import models

from company.models import Company


class Config(models.Model):
    pass


class Plan(models.Model):
    name = models.CharField(max_length=100, unique=True)
    is_flexible = models.BooleanField(default=False)
    threshold = models.IntegerField(null=True, blank=True)
    # is_active = models.BooleanField(default=True)
    date_updated = models.DateTimeField(auto_now=True)
    date_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    def get_weight(self):
        total = Subscription.objects.count()
        return int((self.usage.count()/total) * 100) if total > 0 else 0


class Subscription(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="subscriptions")
    plan = models.ForeignKey(Plan, on_delete=models.SET_NULL, null=True, blank=True, related_name="usage")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    expiry = models.DateField(null=False, blank=False)
    is_expired = models.BooleanField(default=False)
    date_created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-pk", )
# class Permission(models.Model):
#     name