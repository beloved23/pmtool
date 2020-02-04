import csv
import datetime
import math

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.db.models import Q
from django.http import HttpResponseRedirect, JsonResponse, Http404, HttpResponse
from django.shortcuts import render, get_object_or_404

# Create your views here.
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView, ListView, UpdateView, CreateView, RedirectView, DetailView, FormView

from HRTool import utils, settings
from HRTool.mixins import UserPermissionsMixin
from account.models import Profile
from company.forms import DepartmentCreateFormSet, DepartmentCreateForm, RoleCreateFormSet, MemberCreateFormSet, \
    MemberCreateForm, RatingConfigFormSet, CreateCompanyCEOForm
from company.models import Department, Company, Role, Config, Rating
from kra.models import KraBucket
from task.models import Task


class DepartmentListView(UserPermissionsMixin, ListView):
    model = Department
    template_name = "company/departments.html"
    permissions = ("company.view_role", "company.add_role", "company.delete_role")

    def get_queryset(self):
        company = self.request.user.profile.company
        return company.departments.all()


class RoleListView(UserPermissionsMixin, ListView):
    model = Role
    template_name = "company/roles.html"
    permissions = ("company.view_role", "company.add_role", "company.delete_role")

    def get_queryset(self):
        company = self.request.user.profile.company
        return company.roles.all()


class StaffListView(UserPermissionsMixin, ListView):
    model = Profile
    template_name = "company/members.html"
    permissions = ("account.view_profile", "account.add_profile", "account.delete_profile")

    def get_queryset(self):
        company = self.request.user.profile.company
        return company.members.all()


class CreateDepartmentView(UserPermissionsMixin, CreateView):
    model = Department
    template_name = "company/create_department.html"
    permissions = ("company.view_department", "company.add_department", "company.delete_department")
    success_url = reverse_lazy("company:departments")
    form_class = DepartmentCreateFormSet

    def form_valid(self, form):
        form.instance = self.request.user.profile.company
        form.save()
        messages.success(self.request, "Department(s) created successfully")
        return HttpResponseRedirect(self.success_url)

    def get_form_kwargs(self):
        kwargs1 = super(CreateDepartmentView, self).get_form_kwargs()
        kwargs = {
            "members": self.request.user.profile.company.members.all()
        }
        kwargs1["form_kwargs"] = kwargs
        return kwargs1


class CreateRoleView(UserPermissionsMixin, CreateView):
    model = Role
    template_name = "company/create_role.html"
    permissions = ("company.add_role",)
    success_url = reverse_lazy("company:roles")
    form_class = RoleCreateFormSet

    def form_valid(self, form):
        form.instance = self.request.user.profile.company
        form.save()
        messages.success(self.request, "Role(s) created successfully")
        return HttpResponseRedirect(self.success_url)


class CreateMemberView(UserPermissionsMixin, CreateView):
    model = Profile
    template_name = "company/create_member.html"
    permissions = ("account.add_profile",)
    success_url = reverse_lazy("company:members")
    form_class = MemberCreateFormSet

    def get_form_kwargs(self):
        kwargs1 = super(CreateMemberView, self).get_form_kwargs()
        kwargs = {"departments": self.request.user.profile.company.departments.all(),
                  "roles": self.request.user.profile.company.roles.all(),
                  "members": self.request.user.profile.company.members.all()}
        kwargs1["form_kwargs"] = kwargs
        return kwargs1

    def form_valid(self, form):
        company = self.request.user.profile.company
        if not company.config.subscription.plan.is_flexible:
            count = company.members.count()
            total = count + len(form.forms)
            threshold = company.config.subscription.plan.threshold
            if total > threshold:
                form._non_form_errors = form.error_class([
                                                             "Sorry, you've exceeded your subscription quota by {}. You have just {} slots left.'".format(
                                                                 total - threshold, threshold - count)])
                return self.form_invalid(form)
        form.instance = company
        members = form.save(commit=False)
        i = 0

        for f in form.forms:
            cd = f.cleaned_data
            if "auuid" in cd:
                username = cd["auuid"] + "_" + form.instance.identifier
                user = User.objects.create(username=username, first_name=cd["first_name"], last_name=cd["last_name"],
                                           email=cd["email"], is_active=True)
                password = utils.random_string()
                user.set_password(password)
                if cd["permissions"]:
                    user.user_permissions.set(cd["permissions"])
                user.save()
                members[i].user = user
                members[i].save()
                mail = render_to_string("account/emails/user-creation.html", {
                    "user": user,
                    "password": password,
                    "request": self.request
                })
                utils.send_mail("Login Credentials", mail, user.email)
            i += 1
        messages.success(self.request, "Member(s) created successfully")
        return HttpResponseRedirect(self.success_url)


class UpdateDepartmentView(UserPermissionsMixin, UpdateView):
    model = Department
    template_name = "company/update_department.html"
    permissions = ("company.view_department", "company.add_department", "company.delete_department")
    success_url = reverse_lazy("company:departments")
    fields = ["name", "director"]

    def get_queryset(self):
        return self.request.user.profile.company.departments.all()

    def form_valid(self, form):
        messages.success(self.request, "Department updated successfully")
        resp = super(UpdateDepartmentView, self).form_valid(form)
        if self.object.director:
            self.object.director.manager = self.object.company.get_ceo()
            self.object.director.save()
        return resp

    def get_form(self, form_class=None):
        form = super(UpdateDepartmentView, self).get_form(form_class)
        form.fields['director'].queryset = self.object.members.all()
        return form


class UpdateRoleView(UserPermissionsMixin, UpdateView):
    model = Role
    template_name = "company/update_role.html"
    permissions = ("company.add_department",)
    success_url = reverse_lazy("company:roles")
    fields = ["name", ]

    def get_queryset(self):
        return self.request.user.profile.company.roles.all()

    def form_valid(self, form):
        messages.success(self.request, "Role updated successfully")
        return super(UpdateRoleView, self).form_valid(form)


class UpdateMemberView(UserPermissionsMixin, UpdateView):
    model = Profile
    template_name = "company/update_member.html"
    permissions = ("account.add_profile",)
    form_class = MemberCreateForm

    def get_queryset(self):
        return self.request.user.profile.company.members.all()

    def get_form_kwargs(self):
        kwargs = super(UpdateMemberView, self).get_form_kwargs()
        profile = self.get_object()
        if "initial" in kwargs:
            kwargs["initial"].update({
                "first_name": profile.user.first_name,
                "last_name": profile.user.last_name,
                "email": profile.user.email,
                "permissions": profile.user.user_permissions.all()
            })
        else:
            kwargs["initial"] = {
                "first_name": profile.user.first_name,
                "last_name": profile.user.last_name,
                "email": profile.user.email,
                "permissions": profile.user.user_permissions.all()
            }
        kwargs["departments"] = profile.company.departments.all()
        kwargs["roles"] = profile.company.roles.all()
        kwargs["members"] = profile.company.members.all()
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, "Member updated successfully")
        response = super(UpdateMemberView, self).form_valid(form)
        profile = self.object
        profile.user.first_name = form.cleaned_data["first_name"]
        profile.user.last_name = form.cleaned_data["last_name"]
        profile.user.email = form.cleaned_data["email"]
        profile.user.user_permissions.set(form.cleaned_data["permissions"])
        profile.user.save()
        return response


class DepartmentDetailView(DetailView):
    model = Department
    template_name = "company/view_department.html"
    permissions = ("company.view_department",)

    def dispatch(self, request, *args, **kwargs):
        user = self.request.user
        if user.is_anonymous:
            raise Http404()
        has_permissions = []
        department = self.get_object()
        if hasattr(user.profile, 'directing_department') and user.profile.directing_department == department:
            return super(DepartmentDetailView, self).dispatch(request, *args, **kwargs)
        elif user.is_staff or user.is_superuser or (hasattr(user, "profile") and user.profile.is_ceo):
            return super(DepartmentDetailView, self).dispatch(request, *args, **kwargs)
        else:
            if not (user.is_staff or user.is_superuser or (hasattr(user, "profile") and user.profile.is_ceo)):
                for permission in self.permissions:
                    has_permissions.append(user.has_perm(permission))
                if True not in has_permissions:
                    raise Http404()
            else:
                if not hasattr(user.profile, 'directing_department'):
                    raise Http404()

        return super(DepartmentDetailView, self).dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        resp = super(DepartmentDetailView, self).get(request, *args, **kwargs)
        if "generate-kra" in request.GET:
            department = self.get_object()
            bucket = get_object_or_404(KraBucket, reference=request.GET.get("bucket", None))
            if bucket.company != request.user.profile.company:
                raise Http404()
            headers = ("name", "description", "weight", "target", "actual", "achievement", "manager_achievement",
                       "comment", "manager_comment")
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment;filename=%s-%s-kras.csv' % (bucket.title.replace(" ", "-"), department.name.replace(" ", "-"))
            writer = csv.writer(response)
            kras = bucket.kras.filter(user__profile__department=department)
            if request.GET.get("rating", None) != "all":
                kras = kras.filter(rating=get_object_or_404(Rating, pk=request.GET.get("rating")))
            for kra in kras:
                writer.writerow(["Title:", kra.bucket.title])
                writer.writerow(['Staff:', kra.user.get_full_name() + "(" + kra.profile.auuid + ")"])
                department = kra.profile.department
                writer.writerow(['Department:', kra.profile.department.name if kra.profile.department else "-"])
                writer.writerow(['Line Manager:',
                                 kra.profile.manager.user.get_full_name() + "(" + kra.profile.manager.auuid + ")" if kra.profile.manager else "-"])
                writer.writerow(['Department Director:',
                                 department.director.user.get_full_name() + "(" + department.director.auuid + ")" if department and department.director else "-"])
                writer.writerow([""])
                writer.writerow([header.upper() for header in headers])
                for item in kra.items.all():
                    line = [getattr(item, header) for header in headers]
                    writer.writerow(line)
                writer.writerow([""])
                writer.writerow(["Status", kra.status])
                writer.writerow(["Line Manager's Rating", kra.rating.name if kra.rating else "-"])
                writer.writerow(["HOD's Rating", kra.hod_rating.name if kra.hod_rating else "-"])
                writer.writerow(["Date Created", kra.date_created])
                writer.writerow(["Last Updated", kra.date_updated])
                writer.writerow([""])
                writer.writerow([""])
                writer.writerow([""])
            return response
        elif "generate-tasks" in request.GET:
            department = self.get_object()
            headers = ("Task", "Description", "Created by", "Assigned to", "Status", "Date Created", "Date Completed",
                       "Assigned Duration (hours)", "Actual Duration (hours)")
            response = HttpResponse(content_type='text/csv')
            writer = csv.writer(response)
            writer.writerow([header.upper() for header in headers])
            response['Content-Disposition'] = 'attachment;filename=%s-%s-to-%s-tasks.csv' % (
                department.name.replace(" ", "-"), request.GET.get("start").replace("/", "_"), request.GET.get("end").replace("/", "_"))
            date_start = datetime.datetime.strptime(request.GET.get("start"), "%m/%d/%Y")
            date_end = datetime.datetime.strptime(request.GET.get("end"), "%m/%d/%Y")
            for task in Task.objects.filter(
                    Q(assigned_to__department=department, date_created__gte=date_start, date_created__lte=date_end) | Q(created_by__department=department, date_created__gte=date_start, date_created__lte=date_end)
            ):
                assigned_to = task.assigned_to.user.get_full_name() + "(" + task.created_by.auuid + ")" if task.assigned_to else "-"
                actual_duration = math.ceil(0 if task.status.lower() != "completed" else (
                            (task.date_completed - task.date_created).total_seconds() / 3600))
                line = [task.title, task.content,
                        task.created_by.user.get_full_name() + "(" + task.created_by.auuid + ")",
                        assigned_to, task.status, task.date_created, task.date_completed, task.duration,
                        actual_duration]
                writer.writerow(line)
            return response
        return resp

    def get_queryset(self):
        return self.request.user.profile.company.departments.all()

    def get_chart_data(self):
        ratings = self.request.user.profile.company.config.ratings.all()
        data = []
        for rating in ratings:
            data.append(
                (rating.name, rating.hod_rating_kras.filter(bucket=self.request.user.profile.company.last_bucket,
                                                            user__profile__department=self.object).count()))
        return data

    def get_context_data(self, **kwargs):
        kwargs = super(DepartmentDetailView, self).get_context_data(**kwargs)
        kwargs["chart_data"] = self.get_chart_data()
        return kwargs


class RoleDetailView(UserPermissionsMixin, DetailView):
    model = Role
    template_name = "company/view_role.html"
    permissions = ("company.view_role",)

    def get_queryset(self):
        return self.request.user.profile.company.roles.all()

    def get(self, request, *args, **kwargs):
        resp = super(RoleDetailView, self).get(request, *args, **kwargs)
        if "generate-kra" in request.GET:
            role = self.get_object()
            bucket = get_object_or_404(KraBucket, reference=request.GET.get("bucket", None))
            if bucket.company != request.user.profile.company:
                raise Http404()
            headers = ("name", "description", "weight", "target", "actual", "achievement", "manager_achievement",
                       "comment", "manager_comment")
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment;filename=%s-%s-kras.csv' % (bucket.title.replace(" ", "-"), role.name.replace(" ", "-"))
            writer = csv.writer(response)
            kras = bucket.kras.filter(user__profile__role=role)
            if request.GET.get("rating", None) != "all":
                kras = kras.filter(rating=get_object_or_404(Rating, pk=request.GET.get("rating")))
            for kra in kras:
                writer.writerow(["Title:", kra.bucket.title])
                writer.writerow(['Staff:', kra.user.get_full_name() + "(" + kra.profile.auuid + ")"])
                department = kra.profile.department
                writer.writerow(['Department:', kra.profile.department.name if kra.profile.department else "-"])
                writer.writerow(['Line Manager:',
                                 kra.profile.manager.user.get_full_name() + "(" + kra.profile.manager.auuid + ")" if kra.profile.manager else "-"])
                writer.writerow(['Department Director:',
                                 department.director.user.get_full_name() + "(" + department.director.auuid + ")" if department and department.director else "-"])
                writer.writerow([""])
                writer.writerow([header.upper() for header in headers])
                for item in kra.items.all():
                    line = [getattr(item, header) for header in headers]
                    writer.writerow(line)
                writer.writerow([""])
                writer.writerow(["Status", kra.status])
                writer.writerow(["Line Manager's Rating", kra.rating.name if kra.rating else "-"])
                writer.writerow(["HOD's Rating", kra.hod_rating.name if kra.hod_rating else "-"])
                writer.writerow(["Date Created", kra.date_created])
                writer.writerow(["Last Updated", kra.date_updated])
                writer.writerow([""])
                writer.writerow([""])
                writer.writerow([""])
            return response
        elif "generate-tasks" in request.GET:
            role = self.get_object()
            headers = ("Task", "Description", "Created by", "Assigned to", "Status", "Date Created", "Date Completed",
                       "Assigned Duration (hours)", "Actual Duration (hours)")
            response = HttpResponse(content_type='text/csv')
            writer = csv.writer(response)
            writer.writerow([header.upper() for header in headers])
            response['Content-Disposition'] = 'attachment;filename=%s-%s-to-%s-tasks.csv' % (
            role.name.replace(" ", "-"), request.GET.get("start").replace("/", "_"), request.GET.get("end").replace("/", "_"))
            date_start = datetime.datetime.strptime(request.GET.get("start"), "%m/%d/%Y")
            date_end = datetime.datetime.strptime(request.GET.get("end"), "%m/%d/%Y")
            for task in Task.objects.filter(
                    Q(assigned_to__role=role, date_created__gte=date_start, date_created__lte=date_end) | Q(created_by__role=role, date_created__gte=date_start, date_created__lte=date_end)
            ):
                assigned_to = task.assigned_to.user.get_full_name() + "(" + task.created_by.auuid + ")" if task.assigned_to else "-"
                actual_duration = math.ceil(0 if task.status.lower() != "completed" else (
                            (task.date_completed - task.date_created).total_seconds() / 3600))
                line = [task.title, task.content,
                        task.created_by.user.get_full_name() + "(" + task.created_by.auuid + ")",
                        assigned_to, task.status, task.date_created, task.date_completed, task.duration,
                        actual_duration]
                writer.writerow(line)
            return response
        return resp


class MemberDetailView(DetailView):
    model = Profile
    template_name = "company/view_member.html"
    permissions = ("account.add_profile", "account.view_profile",)

    def dispatch(self, request, *args, **kwargs):
        user = self.request.user
        if user.is_anonymous:
            raise Http404()
        has_permissions = []
        viewed_profile = self.get_object()
        if hasattr(user.profile, 'directing_department') and user.profile.directing_department.members.filter(
                pk=viewed_profile.pk).exists():
            return super(MemberDetailView, self).dispatch(request, *args, **kwargs)
        elif user.is_staff or user.is_superuser or (hasattr(user, "profile") and user.profile.is_ceo):
            return super(MemberDetailView, self).dispatch(request, *args, **kwargs)
        else:
            if not (user.is_staff or user.is_superuser or (hasattr(user, "profile") and user.profile.is_ceo)):
                for permission in self.permissions:
                    has_permissions.append(user.has_perm(permission))
                if True not in has_permissions:
                    raise Http404()
            elif not hasattr(user.profile, 'directing_department'):
                raise Http404()
        return super(MemberDetailView, self).dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return self.request.user.profile.company.members.all()

    def get_context_data(self, **kwargs):
        kwargs = super(MemberDetailView, self).get_context_data(**kwargs)
        kwargs["now"] = datetime.datetime.now()
        return kwargs


class DeleteDepartment(UserPermissionsMixin, RedirectView):
    permissions = ("company.delete_department",)
    pattern_name = "company:departments"

    def get(self, request, *args, **kwargs):
        department = get_object_or_404(Department, pk=kwargs["pk"], company=request.user.profile.company)
        department.delete()
        messages.success(request, "Department deleted successfully")
        return HttpResponseRedirect(reverse_lazy(self.pattern_name))


class DeleteRole(UserPermissionsMixin, RedirectView):
    permissions = ("company.delete_role",)
    pattern_name = "company:roles"

    def get(self, request, *args, **kwargs):
        role = get_object_or_404(Role, pk=kwargs["pk"], company=request.user.profile.company)
        role.delete()
        messages.success(request, "Role deleted successfully")
        return HttpResponseRedirect(reverse_lazy(self.pattern_name))


class DeleteMember(UserPermissionsMixin, RedirectView):
    permissions = ("account.delete_profile",)
    pattern_name = "company:members"

    def get(self, request, *args, **kwargs):
        user = get_object_or_404(User, pk=kwargs["pk"], company=request.user.profile.company)
        user.delete()
        messages.success(request, "Member deleted successfully")
        return HttpResponseRedirect(reverse_lazy(self.pattern_name))


class ConfigView(UserPermissionsMixin, UpdateView):
    permissions = ("company.can_view_config", "company.can_change_config")
    fields = ["logo", "theme", "background_image", "pip_threshold", ]
    template_name = "company/config.html"
    model = Config
    success_url = reverse_lazy("company:config")

    def dispatch(self, request, *args, **kwargs):
        self.kwargs["pk"] = request.user.profile.company.config.pk
        return super(ConfigView, self).dispatch(request, *args, **kwargs)

    def get_formset(self):
        return RatingConfigFormSet(self.request.POST or None, instance=self.get_object())

    def get_ceo_form(self):
        return CreateCompanyCEOForm(self.request.POST or None, files=self.request.FILES or None)

    def has_ceo(self):
        ceo = self.object.company.get_ceo()
        return ceo is not None

    def get_chart_data(self):
        ratings = self.get_object().ratings.all()
        members_count = self.request.user.profile.company.members.count()
        data = []
        count = 0
        i = 0
        for rating in ratings:
            _count = int(0.01 * rating.threshold * members_count)
            if i == len(ratings) - 1:
                _count = members_count - count
            else:
                count += _count
            data.append((rating.name, _count))
            i += 1
        return data

    def get_context_data(self, **kwargs):
        kwargs = super(ConfigView, self).get_context_data(**kwargs)
        if "ratings" not in kwargs:
            kwargs["ratings"] = self.get_formset()
        if not self.has_ceo():
            if "ceo_form" not in kwargs:
                kwargs["ceo_form"] = self.get_ceo_form()
        else:
            kwargs["ceo_form"] = None
        kwargs["chart_data"] = self.get_chart_data()
        return kwargs

    def form_valid(self, form):
        ratings = self.get_formset()
        has_ceo = self.has_ceo()
        if has_ceo:
            if ratings.is_valid():
                resp = super(ConfigView, self).form_valid(form)
                ratings.save()
                messages.success(self.request, "Configurations updated successfully")
                return resp
        else:
            ceo_form = self.get_ceo_form()
            if ratings.is_valid() and ceo_form.is_valid():
                resp = super(ConfigView, self).form_valid(form)
                ratings.save()
                ceo = ceo_form.save(self.object.company, self.request)
                departments = self.object.company.departments.filter(director__isnull=False)
                for department in departments:
                    director = department.director
                    director.manager = ceo
                    director.save()
                messages.success(self.request, "Configurations updated successfully")
                return resp
        return self.render_to_response(
            self.get_context_data(ratings=ratings, ceo_form=ceo_form if not has_ceo else None))


def get_department_members(request, pk):
    department = get_object_or_404(Department, pk=pk)
    members = department.members.all()
    resp = []
    for member in members:
        resp.append({"id": member.pk, "name": member.__str__()})
    return JsonResponse(resp)


@login_required()
def download_task_report(request, pk):
    headers = ("Task", "Description", "Created by", "Assigned to", "Status", "Date Created", "Date Completed",
               "Assigned Duration (hours)", "Actual Duration (hours)")
    response = HttpResponse(content_type='text/csv')
    writer = csv.writer(response)
    writer.writerow([header.upper() for header in headers])
    user = get_object_or_404(Profile, pk=pk)
    response['Content-Disposition'] = 'attachment;filename=%s-%s-%s-tasks.csv' % (user.user.first_name, user.user.last_name, user.auuid)
    for task in user.tasks:
        assigned_to = task.assigned_to.user.get_full_name()+"("+task.created_by.auuid+")" if task.assigned_to else "-"
        actual_duration = math.ceil(0 if task.status.lower() != "completed" else ((task.date_completed - task.date_created).total_seconds()/3600))
        line = [task.title, task.content, task.created_by.user.get_full_name()+"("+task.created_by.auuid+")",
                assigned_to, task.status, task.date_created, task.date_completed, task.duration, actual_duration]
        writer.writerow(line)
    return response


@login_required()
def download_bulk_kra_report(request, pk):
    profile = get_object_or_404(Profile, pk=pk, company=request.user.profile.company)
    headers = ("name", "description", "weight", "target", "actual", "achievement", "manager_achievement",
               "comment", "manager_comment")
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment;filename=%s-%s-%s-all-kra.csv' % (profile.first_name, profile.last_name, profile.auuid)
    writer = csv.writer(response)
    writer.writerow(['Staff:', profile.user.get_full_name() + "("+profile.auuid+")"])
    department = profile.department
    writer.writerow(['Department:', profile.department.name if profile.department else "-"])
    writer.writerow(['Line Manager:', profile.manager.user.get_full_name() + "("+profile.manager.auuid+")" if profile.manager else "-"])
    writer.writerow(['Department Director:', department.director.user.get_full_name() + "("+department.director.auuid+")" if department and department.director else "-"])
    writer.writerow([""])
    writer.writerow([""])
    for kra in profile.user.kras.all():
        writer.writerow(["Title:", kra.bucket.title])
        writer.writerow([""])
        writer.writerow([header.upper() for header in headers])
        for item in kra.items.all():
            line = [getattr(item, header) for header in headers]
            writer.writerow(line)
        writer.writerow([""])
        writer.writerow(["Status", kra.status])
        writer.writerow(["Line Manager's Rating", kra.rating.name if kra.rating else "-"])
        writer.writerow(["HOD's Rating", kra.hod_rating.name if kra.hod_rating else "-"])
        writer.writerow(["Date Created", kra.date_created])
        writer.writerow(["Last Updated", kra.date_updated])
        writer.writerow([""])
        writer.writerow([""])
        writer.writerow([""])
    return response


@login_required()
def download_bulk_pip_report(request, pk):
    profile = get_object_or_404(Profile, pk=pk, company=request.user.profile.company)
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment;filename=%s-%s-%s-all-pips.csv' % (profile.first_name, profile.last_name, profile.auuid)
    writer = csv.writer(response)
    writer.writerow(['Staff:', profile.user.get_full_name() + "("+profile.auuid+")"])
    department = profile.department
    writer.writerow(['Department:', profile.department.name if profile.department else "-"])
    writer.writerow(['Line Manager:', profile.manager.user.get_full_name() + "("+profile.manager.auuid+")" if profile.manager else "-"])
    writer.writerow(['Department Director:', department.director.user.get_full_name() + "("+department.director.auuid+")" if department and department.director else "-"])
    writer.writerow([""])
    writer.writerow([""])
    for pip in profile.user.pips.all():
        writer.writerow(["Raised by:", pip.line_manager.get_full_name() + "("+pip.line_manager.profile.auuid+")"])
        writer.writerow(["Description:", pip.description])
        writer.writerow(["Date Created", pip.date_created])
        writer.writerow([""])
        writer.writerow(["Issues ("+str(pip.issues.count())+")"])
        for issue in pip.issues.all():
            writer.writerow([issue.description])
        writer.writerow([""])
        writer.writerow(["Expectations ("+str(pip.expectations.count())+")"])
        for expectation in pip.expectations.all():
            writer.writerow([expectation.description])
        writer.writerow([""])
        writer.writerow([""])
        writer.writerow([""])
    return response
