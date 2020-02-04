import datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpResponseRedirect, Http404, JsonResponse
from django.shortcuts import render, get_object_or_404
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from HRTool.notifications import NotificationManager
from task.forms import TaskCreateForm
from task.models import Task


@method_decorator(login_required, "dispatch")
class TasksManagementView(TemplateView):
    template_name = "task/management.html"

    def get_form(self):
        form = TaskCreateForm(self.request.POST or None)
        user = self.request.user
        if user.profile.is_ceo:
            queryset = user.profile.company.members.all().exclude(pk=user.profile.pk)
        else:
            queryset = user.profile.child_members.all()
        form.fields["assigned_to"].queryset = queryset
        return form

    def get_context_data(self, **kwargs):
        kwargs = super(TasksManagementView, self).get_context_data(**kwargs)
        kwargs["tasks"] = self.request.user.profile.tasks
        kwargs["now"] = datetime.datetime.now()
        if "form" not in kwargs:
            kwargs["form"] = self.get_form()
        return kwargs

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        if form.is_valid():
            messages.success(request, "Task created successfully")
            task = form.save(False)
            task.created_by = self.request.user.profile
            task.save()
            if task.assigned_to:
                NotificationManager.task_creation_notification(request, task)
            return HttpResponseRedirect(reverse_lazy("task:management"))
        return self.render_to_response(self.get_context_data(form=form))


@login_required()
def update_task(request, reference):
    task = get_object_or_404(Task, Q(created_by=request.user.profile, reference=reference,
                             status__iexact="pending") | Q(assigned_to=request.user.profile, reference=reference,
                             status__iexact="pending"))
    status = request.GET.get("status", None)
    if status is None or status.title() not in ["Cancelled", "Completed"]:
        raise Http404()
    task.status = status.title()
    if task.status == "Completed":
        task.date_completed = datetime.datetime.now()
    task.save()
    if task.assigned_to:
        NotificationManager.task_update_notification(request, task)
    return JsonResponse({"message": "Task %s successfully" % status.lower()})
