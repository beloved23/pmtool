from django import forms
from django.contrib.auth.models import User

from account import logic


class UserLoginForm(forms.ModelForm):
    username = forms.CharField(max_length=20, help_text=u'', required=True,
                               widget=forms.TextInput(attrs={"placeholder": "Username"}))
    password = forms.CharField(min_length=6, max_length=20,
                               widget=forms.PasswordInput(attrs={'class':'form-control def-input',
                                                                 'placeholder': "Password"}),
                               label=u'Password', required=True)
    company_identity = forms.CharField(max_length=10, required=True, label="Company ID",
                                       widget=forms.TextInput(attrs={'placeholder': "Company ID"}))
    # captcha = NoReCaptchaField()

    class Meta:
        model = User
        fields = ['username', 'password']

    def clean(self):
        self.user_cache = None
        cd = self.cleaned_data
        username = cd.get('username')
        password = cd.get('password')
        company_identity = cd.get('company_identity')
        if username and password and company_identity:
            self.user_cache = logic.login_validation(username, password, company_identity, False)
        return cd

    def get_user(self):
        return self.user_cache


class UserCustomLoginForm(forms.ModelForm):
    username = forms.CharField(label=u'AUUID', max_length=20, help_text=u'', required=True,
                               widget=forms.TextInput(attrs={"placeholder": "AUUID"}))
    password = forms.CharField(min_length=6, max_length=20,
                               widget=forms.PasswordInput(attrs={'class':'form-control def-input',
                                                                 'placeholder': "Password"}),
                               label=u'Password', required=True)
    # captcha = NoReCaptchaField()

    class Meta:
        model = User
        fields = ['username', 'password']

    def clean(self):
        self.user_cache = None
        cd = self.cleaned_data
        username = cd.get('username')
        password = cd.get('password')
        company_identity = cd.get('company_identity')
        if username and password and company_identity:
            self.user_cache = logic.login_validation(username, password, company_identity, False)
        return cd

    def get_user(self):
        return self.user_cache


