import time

from django.contrib.auth.models import User
from django.db import models
from django.urls import reverse


class Pip(models.Model):
    staff = models.ForeignKey(User, on_delete=models.CASCADE, related_name="pips")
    line_manager = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="raised_pips")
    reference = models.CharField(max_length=30, null=True, blank=True, editable=False, unique=True)
    description = models.TextField()
    date_created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-pk", )

    @property
    def manager(self):
        return self.line_manager.profile

    def save(self, *args, **kwargs):
        if not self.reference:
            self.reference = str(time.time()).replace(".", "")
        super(Pip, self).save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("pip:view", args=(self.reference,))


class Issue(models.Model):
    pip = models.ForeignKey(Pip, on_delete=models.CASCADE, related_name='issues')
    description = models.TextField()
    date_created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-pk", )


class Expectation(models.Model):
    pip = models.ForeignKey(Pip, on_delete=models.CASCADE, related_name='expectations')
    description = models.TextField()
    date_created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-pk", )
