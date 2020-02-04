from django import forms
from django.forms import inlineformset_factory

from p_i_p.models import Issue, Expectation, Pip


class PipIssueForm(forms.ModelForm):

    class Meta:
        model = Issue
        fields = ("description", )


class PipExpectationForm(forms.ModelForm):

    class Meta:
        model = Expectation
        fields = ("description", )


PipIssueFormSet = inlineformset_factory(Pip, Issue, form=PipIssueForm, extra=0, max_num=10, min_num=2, can_delete=False,
                                        validate_min=True, validate_max=True)


PipExpectationFormSet = inlineformset_factory(Pip, Expectation, form=PipExpectationForm, extra=0, max_num=10, min_num=2,
                                              can_delete=False, validate_min=True, validate_max=True)
