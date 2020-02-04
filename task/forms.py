from django import forms

from task.models import Task


class TaskCreateForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ("title", "content", "assigned_to", "duration")

    # def clean(self):
    #     cd = super(TaskCreateForm, self).clean()
    #     duration = cd["duration"]
    #     try:
    #         duration = int(duration)
    #     except:
    #         self.add_error("duration", "Invalid duration specified")
    #     return cd
