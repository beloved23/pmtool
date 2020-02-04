from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.models import User, Permission
from django.core.mail import send_mail
from django.template.loader import render_to_string

from HRTool import utils, settings
from account.models import Profile
from company.models import Company, Config
from superuser.models import Plan, Subscription


class LoginForm(forms.ModelForm):
    username = forms.CharField(max_length=20, help_text=u'', required=True)
    password = forms.CharField(min_length=6, max_length=20,
                               widget=forms.PasswordInput(attrs={'class': 'form-control def-input'}),
                               label=u'Password', required=True)

    class Meta:
        model = User
        fields = ['username', 'password']

    def clean(self):
        self.user_cache = None
        cd = self.cleaned_data
        username = cd.get('username')
        password = cd.get('password')
        if username and password:
            self.user_cache = authenticate(username=username, password=password)
            if self.user_cache is None:
                raise forms.ValidationError("Invalid login details")
            elif self.user_cache is not None and not self.user_cache.is_superuser:
                raise forms.ValidationError('Sorry, you do not have access to view this page')
            elif self.user_cache is not None and not self.user_cache.is_active:
                raise forms.ValidationError('Your Account has been deactivated.')
        return cd

    def get_user(self):
        return self.user_cache


class PlanForm(forms.ModelForm):
    class Meta:
        model = Plan
        fields = ("name", "is_flexible", "threshold")


class CompanyForm(forms.ModelForm):

    class Meta:
        model = Company
        fields = ("name", "identifier",)

    def clean(self):
        cd = self.cleaned_data
        identifier = cd["identifier"].strip()
        cd['identifier'] = identifier
        if " " in identifier:
            self.add_error("identifier", "Company's identifier should not contain space character")
        return cd


class CompanyConfigForm(forms.ModelForm):

    plan = forms.ModelChoiceField(queryset=Plan.objects.all(), required=True)

    class Meta:
        model = Config
        fields = ("plan",)


class SubscriptionForm(forms.ModelForm):
    plan = forms.ModelChoiceField(queryset=Plan.objects.all(), required=True)

    class Meta:
        model = Subscription
        fields = ("plan", "expiry")


class CreateCompanyMemberForm(forms.ModelForm):
    first_name = forms.CharField(max_length=100, required=True)
    last_name = forms.CharField(max_length=100, required=True)
    email = forms.EmailField(max_length=255, required=True)
    gender = forms.CharField(max_length=100, required=True, widget=forms.Select(choices=[("", "-- Please select --"), ("Male", "Male"), ("Female", "Female")]))

    class Meta:
        model = Profile
        fields = ("first_name", "last_name", "auuid", "gender", "email", "phone", "photo", "appointment_date")

    def clean(self):
        cd = super(CreateCompanyMemberForm, self).clean()
        utils.verify_attachments(self, cd, "photo")
        return cd

    def save(self, company, request):
        cd = self.cleaned_data
        profile = super(CreateCompanyMemberForm, self).save(False)
        user = User.objects.create(first_name=cd["first_name"], last_name=cd["last_name"], email=cd["email"],
                                   is_staff=True, is_active=True, username=profile.auuid+"_"+company.identifier)
        password = utils.random_string()
        user.set_password(password)
        user.user_permissions.set(Permission.objects.all())
        user.save()
        # utils.send_password_mail(user.email, password)
        profile.company = company
        profile.user = user
        profile.save()
        mail = render_to_string("account/emails/user-creation.html", {
            "user": user,
            "password": password,
            "request": request
        })
        utils.send_mail("Login Credentials", mail, user.email)
        return profile


class SuperuserForm(forms.ModelForm):
    first_name = forms.CharField(max_length=100, required=True)
    last_name = forms.CharField(max_length=100, required=True)
    email = forms.EmailField(max_length=255, required=True)

    class Meta:
        model = User
        fields = ("first_name", "last_name", "username", "email")
