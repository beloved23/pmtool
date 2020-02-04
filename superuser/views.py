from dateutil.relativedelta import relativedelta
from django.contrib import messages
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.models import User, Permission
from django.db import transaction, IntegrityError
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import redirect, get_object_or_404
from django.template.loader import render_to_string
from django.urls import reverse_lazy
import datetime
from django.views.generic import FormView, TemplateView, ListView, CreateView, DetailView, UpdateView
from HRTool import utils, settings
from account.models import Profile
from company.models import Company, Config
from superuser.forms import LoginForm, CreateCompanyMemberForm, CompanyForm, CompanyConfigForm, PlanForm, SuperuserForm, \
    SubscriptionForm
from superuser.mixins import AllowSuperuserMixin
from superuser.models import Plan


class LoginView(FormView):
    template_name = 'superuser/login.html'
    form_class = LoginForm
    success_url = reverse_lazy('superuser:dashboard')

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect(self.success_url)
        return super(LoginView, self).get(request, *args, **kwargs)

    def form_valid(self, form):
        user = form.get_user()
        auth_login(self.request, user)
        return redirect('superuser:dashboard')


class DashboardView(AllowSuperuserMixin, TemplateView):
    template_name = "superuser/dashboard.html"

    def get_monthly_chart_data(self):
        today = datetime.datetime.now()
        labels = []
        values = []
        i = 5
        while i >= 0:
            dt = today + relativedelta(today, months=-i)
            labels.append(dt.strftime("%B") if i != 0 else "This month")
            values.append(Company.objects.filter(date_created__year=dt.year, date_created__month=dt.month).count())
            i -= 1
        return labels, values

    def get_context_data(self, **kwargs):
        kwargs = super(DashboardView, self).get_context_data(**kwargs)
        labels, values = self.get_monthly_chart_data()
        kwargs["total_companies"] = Company.objects.count()
        kwargs["plans"] = Plan.objects.all()
        kwargs["total_superusers"] = User.objects.filter(is_superuser=True).exclude(username="developer").count()
        kwargs["total_users"] = Profile.objects.count()
        kwargs["companies_analysis_labels"] = labels
        kwargs["companies_analysis_values"] = values
        kwargs["recent_companies"] = Company.objects.all().order_by("-pk")[:5]
        total = Company.objects.count()
        kwargs["active_companies_analysis"] = ((Company.objects.filter(is_active=True).count()/total) * 100) if total != 0 else 0
        kwargs["inactive_companies_analysis"] = (100 - kwargs["active_companies_analysis"]) if total != 0 else 0
        return kwargs


class CompanyListView(AllowSuperuserMixin, ListView):
    model = Company
    template_name = "superuser/companies.html"

    def get_context_data(self, *args, **kwargs):
        kwargs = super(CompanyListView, self).get_context_data(*args, **kwargs)
        kwargs["plans"] = Plan.objects.all()
        return kwargs


class CompanyCreateView(AllowSuperuserMixin, CreateView):
    model = Company
    form_class = CompanyForm
    template_name = "superuser/add-company.html"
    # success_url = reverse_lazy("")

    def get_context_data(self, **kwargs):
        kwargs = super(CompanyCreateView, self).get_context_data(**kwargs)
        kwargs["member_form"] = self.get_member_form()
        kwargs["subscription_form"] = self.get_subscription_form()
        return kwargs

    def get_member_form(self):
        return CreateCompanyMemberForm(data=self.request.POST or None, files=self.request.FILES or None)

    def get_subscription_form(self):
        return SubscriptionForm(data=self.request.POST or None)

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        member_form = self.get_member_form()
        subscription_form = self.get_subscription_form()
        self.object = None
        if form.is_valid() and member_form.is_valid() and subscription_form.is_valid():
            try:
                with transaction.atomic():
                    self.object = form.save()
                    self.object.created_by = request.user
                    self.object.save()
                    member_form.save(self.object, request)
                    subscription = subscription_form.save(commit=False)
                    subscription.created_by = request.user
                    subscription.company = self.object
                    subscription.save()
                    Config.objects.create(company=self.object, subscription=subscription)
                return HttpResponseRedirect(self.get_success_url())
            except IntegrityError:
                form.add_error("identifier", "A company with this identifier already exist")
        return self.render_to_response(self.get_context_data(form=form, member_form=member_form,
                                                             subscription_form=subscription_form))


class CompanyDetailView(AllowSuperuserMixin, DetailView):
    model = Company
    template_name = "superuser/view-company.html"

    def get_context_data(self, **kwargs):
        kwargs = super(CompanyDetailView, self).get_context_data(**kwargs)
        kwargs['subscriptionForm'] = SubscriptionForm()
        return kwargs


class CompanyUpdateView(AllowSuperuserMixin, UpdateView):
    model = Company
    template_name = "superuser/update-company.html"
    form_class = CompanyForm

    def get_context_data(self, **kwargs):
        kwargs = super(CompanyUpdateView, self).get_context_data(**kwargs)
        kwargs["config_form"] = self.get_config_form()
        return kwargs

    def get_config_form(self):
        return CompanyConfigForm(data=self.request.POST or None, instance=self.object.config)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()
        config_form = self.get_config_form()
        if form.is_valid() and config_form.is_valid():
            form.save()
            config_form.save()
            return HttpResponseRedirect(self.get_success_url())
        else:
            return self.render_to_response(self.get_context_data(form=form, config_form=config_form))


@user_passes_test(lambda user: user.is_authenticated and user.is_superuser and user.is_active)
def create_company_subscription(request, pk):
    company = get_object_or_404(Company, pk=pk)
    form = SubscriptionForm(request.POST)
    response = {}
    if form.is_valid():
        company.subscriptions.update(is_expired=True)
        subscription = form.save(commit=False)
        subscription.company = company
        subscription.created_by = request.user
        subscription.save()
        company.is_active = True
        company.config.subscription = subscription
        company.config.save()
        company.save()
        response["success"] = True
    else:
        response["error"] = True
    return JsonResponse(response)


@user_passes_test(lambda user: user.is_authenticated and user.is_superuser and user.is_active)
def toggle_company_status(request, pk):
    company = get_object_or_404(Company, pk=pk)
    if company.is_active:
        company.subscriptions.update(is_expired=True)
    else:
        last_subscription = company.subscriptions.latest("pk")
        last_subscription.is_expired = False
        last_subscription.save()
    company.is_active = not company.is_active
    company.save()
    messages.success(request, "Company updated successfully")
    return redirect(request.META["HTTP_REFERER"])


@user_passes_test(lambda user: user.is_authenticated and user.is_superuser and user.is_active)
def delete_company(request, pk):
    company = get_object_or_404(Company, pk=pk)
    company.delete()
    messages.success(request, "Company deleted successfully")
    return redirect("superuser:companies")


class PlanListView(AllowSuperuserMixin, ListView):
    model = Plan
    template_name = "superuser/plans.html"


class PlanCreateView(AllowSuperuserMixin, CreateView):
    model = Plan
    success_url = reverse_lazy("superuser:plans")
    form_class = PlanForm
    template_name = "superuser/add-plan.html"


class PlanUpdateView(AllowSuperuserMixin, UpdateView):
    model = Plan
    template_name = "superuser/update-plan.html"
    form_class = PlanForm
    success_url = reverse_lazy("superuser:plans")


@user_passes_test(lambda user: user.is_authenticated and user.is_superuser and user.is_active)
def delete_plan(request, pk):
    plan = get_object_or_404(Plan, pk=pk)
    plan.delete()
    messages.success(request, "Plan deleted successfully")
    return redirect("superuser:plans")


class SuperuserListView(AllowSuperuserMixin, ListView):
    model = User
    template_name = "superuser/users.html"

    def get_queryset(self):
        return User.objects.filter(is_superuser=True).exclude(username="developer")


class SuperuserCreateView(AllowSuperuserMixin, CreateView):
    model = User
    success_url = reverse_lazy("superuser:users")
    form_class = SuperuserForm
    template_name = "superuser/add-user.html"

    def form_valid(self, form):
        user = form.save()
        password = utils.random_string()
        user.set_password(password)
        user.is_active = True
        user.is_staff = True
        user.is_superuser = True
        user.user_permissions.set(Permission.objects.all())
        user.save()
        # utils.send_password_mail(user.email, password)
        mail = render_to_string("account/emails/user-creation.html", {
            "user": user,
            "password": password,
            "request": self.request
        })
        utils.send_mail("Login Credentials", mail, user.email)
        messages.success(self.request, "User account created successfully")
        return HttpResponseRedirect(self.success_url)


class SuperuserUpdateView(AllowSuperuserMixin, UpdateView):
    model = User
    template_name = "superuser/update-user.html"
    form_class = SuperuserForm
    success_url = reverse_lazy("superuser:users")


@user_passes_test(lambda user: user.is_authenticated and user.is_superuser and user.is_active)
def toggle_superuser_status(request, pk):
    user = get_object_or_404(User, pk=pk)
    user.is_active = not user.is_active
    user.save()
    messages.success(request, "User updated successfully")
    if request.user == user and not user.is_active:
        return logout(request)
    return redirect("superuser:users")


@user_passes_test(lambda user: user.is_authenticated and user.is_superuser and user.is_active)
def delete_user(request, pk):
    user = get_object_or_404(User, pk=pk)
    user.delete()
    messages.success(request, "User deleted successfully")
    return redirect("superuser:users")


def logout(request):
    auth_logout(request)
    return redirect("superuser:login")
