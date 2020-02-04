from django import forms
from django.contrib.auth.models import User, Permission
from django.forms import inlineformset_factory, BaseInlineFormSet
from django.template.loader import render_to_string

from HRTool import utils, settings
from account.models import Profile
from company.models import Department, Company, Role, Rating, Config


class RoleCreateForm(forms.ModelForm):
    class Meta:
        model = Role
        exclude = ("date_created", )


class DepartmentCreateForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        members = kwargs.pop('members')
        super(DepartmentCreateForm, self).__init__(*args, **kwargs)
        self.fields['director'].queryset = members

    class Meta:
        model = Department
        exclude = ("date_created", )

    def save(self, commit=True):
        department = super(DepartmentCreateForm, self).save(commit=commit)
        if department.director:
            director = department.director
            director.department = department
            ceo = department.company.get_ceo()
            if ceo:
                director.manager = ceo
            director.save()
        return department


class CreateCompanyCEOForm(forms.ModelForm):
    first_name = forms.CharField(max_length=100, required=True)
    last_name = forms.CharField(max_length=100, required=True)
    gender = forms.CharField(max_length=100, required=True, widget=forms.Select(choices=[("", "-- Please select --"), ("Male", "Male"), ("Female", "Female")]))
    email = forms.EmailField(max_length=255, required=True)

    class Meta:
        model = Profile
        fields = ("first_name", "last_name", "auuid", "email", "gender", "phone", "photo", "appointment_date")

    def clean(self):
        cd = super(CreateCompanyCEOForm, self).clean()
        utils.verify_attachments(self, cd, "photo")
        return cd

    def save(self, company, request):
        cd = self.cleaned_data
        profile = super(CreateCompanyCEOForm, self).save(False)
        user = User.objects.create(first_name=cd["first_name"], last_name=cd["last_name"], email=cd["email"],
                                   is_staff=True, is_active=True, username=profile.auuid+"_"+company.identifier)
        password = utils.random_string()
        user.set_password(password)
        user.user_permissions.set(Permission.objects.all())
        user.save()
        # utils.send_password_mail(user.email, password)
        profile.company = company
        profile.user = user
        profile.is_ceo = True
        profile.save()
        mail = render_to_string("account/emails/user-creation.html", {
            "user": user,
            "password": password,
            "request": request
        })
        utils.send_mail("Login Credentials", mail, user.email)
        return profile


class MemberCreateForm(forms.ModelForm):
    first_name = forms.CharField(max_length=255, required=True)
    last_name = forms.CharField(max_length=255, required=True)
    email = forms.EmailField(required=True)
    gender = forms.CharField(max_length=100, required=True, widget=forms.Select(choices=[("", "-- Please select --"), ("Male", "Male"), ("Female", "Female")]))
    permissions = forms.ModelMultipleChoiceField(
        queryset=Permission.objects.filter(content_type__app_label__in=["account", "company"]),
        required=False
    )

    def __init__(self, *args, **kwargs):
        departments = kwargs.pop('departments')
        roles = kwargs.pop('roles')
        members = kwargs.pop('members')
        super(MemberCreateForm, self).__init__(*args, **kwargs)
        self.fields['department'].queryset = departments
        self.fields['role'].queryset = roles
        self.fields['manager'].queryset = members

    class Meta:
        model = Profile
        fields = ("photo", "auuid", "first_name", "last_name", "email", "phone", "gender", "department", "role",
                  "manager", "permissions", "appointment_date", )


class CEOForm(forms.ModelForm):
    first_name = forms.CharField(max_length=255, required=True)
    last_name = forms.CharField(max_length=255, required=True)
    email = forms.EmailField(required=True)

    class Meta:
        model = Profile
        fields = ("photo", "auuid", "first_name", "last_name", "email", "phone", )


class RatingConfigForm(forms.ModelForm):
    class Meta:
        model = Rating
        exclude = ("date_created", "config")


class BaseRatingConfigFormSet(BaseInlineFormSet):

    def clean(self):
        super().clean()
        forms_to_delete = self.deleted_forms
        valid_forms = [form for form in self.forms if form.is_valid() and form not in forms_to_delete]
        total_threshold = sum(f.cleaned_data['threshold'] for f in valid_forms)
        if total_threshold != 100:
            raise forms.ValidationError("Total threshold must sum up to 100")


DepartmentCreateFormSet = inlineformset_factory(Company, Department, form=DepartmentCreateForm, min_num=1, max_num=10,
                                                extra=1, can_delete=False)

RoleCreateFormSet = inlineformset_factory(Company, Role, form=RoleCreateForm, min_num=1, max_num=10,
                                          extra=1, can_delete=False)

MemberCreateFormSet = inlineformset_factory(Company, Profile, form=MemberCreateForm, min_num=1, max_num=10,
                                            extra=1, can_delete=False, validate_min=True)

RatingConfigFormSet = inlineformset_factory(Config, Rating, form=RatingConfigForm, min_num=3, max_num=5,
                                            extra=0, can_delete=True, validate_min=True, formset=BaseRatingConfigFormSet)
