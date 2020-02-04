import csv
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.template.loader import render_to_string
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView, CreateView, DetailView
from rest_framework.generics import get_object_or_404

from HRTool import utils
from HRTool.notifications import NotificationManager
from account.models import Profile
from p_i_p.forms import PipIssueFormSet, PipExpectationFormSet
from p_i_p.models import Pip


@method_decorator(login_required, "dispatch")
class PipCreateView(CreateView):
    template_name = "pip/create.html"
    model = Pip
    fields = ("description", )

    def dispatch(self, request, *args, **kwargs):
        self.member = get_object_or_404(Profile, auuid=kwargs["auuid"], company=request.user.profile.company,
                                        manager=request.user.profile)
        return super(PipCreateView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        kwargs = super(PipCreateView, self).get_context_data(**kwargs)
        kwargs["member"] = self.member
        if self.member.company.config.pip_threshold and self.member.company.config.pip_threshold != 0:
            kwargs["pip_progress"] = 100 * (self.member.user.pips.count() / self.member.company.config.pip_threshold)
        else:
            kwargs["pip_progress"] = 100 * (self.member.user.pips.count() / 2)
        if "issuesForm" not in kwargs:
            kwargs["issuesForm"] = self.get_issues_form()
        if "expectationsForm" not in kwargs:
            kwargs["expectationsForm"] = self.get_expectations_form()
        return kwargs

    def form_valid(self, form):
        issuesForm = self.get_issues_form()
        expectationsForm = self.get_expectations_form()
        if issuesForm.is_valid() and expectationsForm.is_valid():
            with transaction.atomic():
                pip = form.save(commit=False)
                pip.staff = self.member.user
                pip.line_manager = self.request.user
                pip.save()
                self.object = pip
                issuesForm.instance = pip
                expectationsForm.instance = pip
                issuesForm.save()
                expectationsForm.save()
            messages.success(self.request, "PIP created successfully")
            NotificationManager.pip_notification(self.request, self.member.user, pip)
            return HttpResponseRedirect(self.get_success_url())
        return self.form_invalid(form=form, issuesForm=issuesForm, expectationsForm=expectationsForm)

    def form_invalid(self, **forms):
        return self.render_to_response(self.get_context_data(**forms))

    def get_issues_form(self):
        return PipIssueFormSet(self.request.POST or None)

    def get_expectations_form(self):
        return PipExpectationFormSet(self.request.POST or None)


@method_decorator(login_required, "dispatch")
class PipManagementView(TemplateView):
    template_name = "pip/management.html"

    def get_context_data(self, **kwargs):
        kwargs = super(PipManagementView, self).get_context_data(**kwargs)
        return kwargs


@method_decorator(login_required, "dispatch")
class PipDetailView(DetailView):
    template_name = "pip/detail.html"
    slug_url_kwarg = "reference"
    slug_field = "reference"
    model = Pip

    def get_context_data(self, **kwargs):
        kwargs = super(PipDetailView, self).get_context_data(**kwargs)
        return kwargs


@login_required()
def download_pip_report(request, reference):
    pip = get_object_or_404(Pip, reference=reference)
    if pip.staff.profile.company != request.user.profile.company:
        raise Http404()
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment;filename=%s-%s-%s-%s-pips.csv' % (pip.staff.first_name, pip.staff.last_name, pip.staff.profile.auuid, pip.reference)
    writer = csv.writer(response)
    writer.writerow(['Staff:', pip.staff.get_full_name() + "("+pip.staff.profile.auuid+")"])
    department = pip.staff.profile.department
    writer.writerow(['Department:', department.name if department else "-"])
    writer.writerow(['Line Manager:', pip.staff.profile.manager.user.get_full_name() + "("+pip.staff.profile.manager.auuid+")" if pip.staff.profile.manager else "-"])
    writer.writerow(['Department Director:', department.director.user.get_full_name() + "("+department.director.auuid+")" if department and department.director else "-"])
    writer.writerow([""])
    writer.writerow([""])
    writer.writerow(["Raised by:", pip.line_manager.get_full_name() + "(" + pip.line_manager.profile.auuid + ")"])
    writer.writerow(["Description:", pip.description])
    writer.writerow(["Date Created", pip.date_created])
    writer.writerow([""])
    writer.writerow(["Issues (" + str(pip.issues.count()) + ")"])
    for issue in pip.issues.all():
        writer.writerow([issue.description])
    writer.writerow([""])
    writer.writerow(["Expectations (" + str(pip.expectations.count()) + ")"])
    for expectation in pip.expectations.all():
        writer.writerow([expectation.description])
    return response
