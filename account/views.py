from dateutil.relativedelta import relativedelta
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.http import JsonResponse
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy
import datetime
from django.utils.decorators import method_decorator
from django.views.generic import FormView
from django.contrib.auth import login as auth_login, logout as auth_logout, update_session_auth_hash
from account.forms import UserLoginForm
from django.views.generic import TemplateView

from account.models import Profile
from company.models import Company
from django.contrib.auth.forms import PasswordChangeForm as AuthPasswordChangeForm


@method_decorator(login_required, "dispatch")
class PasswordChangeView(FormView):
    form_class = AuthPasswordChangeForm
    success_url = reverse_lazy("dashboard")
    template_name = "account/password-change.html"

    def get_form_kwargs(self):
        kwargs = super(PasswordChangeView, self).get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        user = form.save()
        user.profile.password_changed = True
        user.profile.save()
        user.save()
        update_session_auth_hash(self.request, user)  # Important!
        messages.success(self.request, "Password changed successfully")
        return super(PasswordChangeView, self).form_valid(form)


class LoginView(FormView):
    template_name = 'account/login.old.html'
    form_class = UserLoginForm
    success_url = reverse_lazy('dashboard')

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("dashboard") if not request.user.is_superuser else redirect("superuser:dashboard")
        if "company_identifier" in kwargs:
            self.company = get_object_or_404(Company, identifier=kwargs["company_identifier"])
        return super(LoginView, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        user = form.get_user()
        auth_login(self.request, user)
        if not user.profile.password_changed:
            return redirect("change-password")
        return redirect('dashboard')

    def get_context_data(self, **kwargs):
        kwargs = super(LoginView, self).get_context_data(**kwargs)
        if "company_identifier" in self.kwargs:
            kwargs["company"] = self.company
        return kwargs


@method_decorator(login_required, "dispatch")
class DashboardView(TemplateView):
    template_name = "account/dashboard.html"

    def get_daily_chart_data(self):
        today = datetime.datetime.now()
        labels = []
        values = []
        i = 3
        while i >= 0:
            dt = today + relativedelta(today, days=-i)
            labels.append(dt.strftime("%A") if i != 0 else "Today")
            values.append(self.request.user.profile.tasks.filter(date_created__year=dt.year, date_created__month=dt.month, date_created__day=dt.day).count())
            i -= 1
        return labels, values

    def get_context_data(self, **kwargs):
        kwargs = super(DashboardView, self).get_context_data(**kwargs)
        kwargs["now"] = datetime.datetime.now()
        labels, values = self.get_daily_chart_data()
        kwargs["task_chart_labels"] = labels
        kwargs["task_chart_values"] = values
        return kwargs


def activate_account(request, auuid, token):
    if request.user.is_authenticated:
        return redirect("dashboard") if not request.user.is_superuser else redirect("superuser:dashboard")
    profile = get_object_or_404(Profile, auuid=auuid, token=token, user__is_active=False)
    profile.user.is_active = True
    profile.token = None
    profile.user.save()
    profile.save()
    messages.success(request, "Your account has been activated successfully")
    return redirect("custom-login", permanent=True, kwargs={"company_identifier": profile.company.identifier})


def logout(request):
    auth_logout(request)
    return redirect("login")


def test_mail(request):
    email = request.GET["email"]
    response = send_mail(
        'Test',
        'Test mail',
        'info@pat.tabtech.com.ng',
        ["simonethenerd@gmail.com"],
        fail_silently=False,
    )
    return JsonResponse({"email": email, "response": response})
