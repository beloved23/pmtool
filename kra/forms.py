import datetime

from django import forms
from django.forms import inlineformset_factory, BaseInlineFormSet

from kra.models import KraItem, Kra, CompanyKraItem, CompanyKra, KraBucket, Message


class KraBucketForm(forms.ModelForm):
    year = forms.IntegerField(min_value=datetime.datetime.today().year, initial=datetime.datetime.today().year)
    # year = datetime.datetime.now().year
    # kwargs["years"] = [year for year in range(year, year + 10)]

    class Meta:
        model = KraBucket
        fields = ("year", )


class KraItemForm(forms.ModelForm):
    weight = forms.FloatField(min_value=1, max_value=100, required=True)
    target = forms.FloatField(min_value=1, max_value=100, required=True)

    class Meta:
        model = KraItem
        fields = ("name", "weight", "target", "description")


class KraItemSelfAssessmentForm(forms.ModelForm):
    actual = forms.FloatField(min_value=1, max_value=100, required=True)
    achievement = forms.FloatField(min_value=1, max_value=100, required=True, label="Achievement %")

    def __init__(self, *args, **kwargs):
        super(KraItemSelfAssessmentForm, self).__init__(*args, **kwargs)
        self.fields["name"].disabled = True
        self.fields["weight"].disabled = True
        self.fields["target"].disabled = True
        self.fields["description"].disabled = True
        self.fields["comment"].required = True

    class Meta:
        model = KraItem
        fields = ("name", "weight", "target", "description", "actual", "achievement", "comment")


class KraItemAssessmentForm(forms.ModelForm):
    manager_achievement = forms.FloatField(min_value=1, max_value=100, required=True, label="Manager's achievement %")

    def __init__(self, *args, **kwargs):
        super(KraItemAssessmentForm, self).__init__(*args, **kwargs)
        self.fields["name"].disabled = True
        self.fields["weight"].disabled = True
        self.fields["target"].disabled = True
        self.fields["description"].disabled = True
        self.fields["comment"].disabled = True
        self.fields["actual"].disabled = True
        self.fields["achievement"].disabled = True
        self.fields["manager_comment"].required = True

    class Meta:
        model = KraItem
        fields = ("name", "weight", "target", "description", "actual", "achievement", "comment",
                  "manager_achievement", "manager_comment")


class ManagerRatingForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        company = kwargs.pop("company")
        super(ManagerRatingForm, self).__init__(*args, **kwargs)
        self.fields["rating"].required = True
        self.fields["rating"].queryset = company.config.ratings.all()

    class Meta:
        model = Kra
        fields = ("rating", )


class HODRatingForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        company = kwargs.pop("company")
        super(HODRatingForm, self).__init__(*args, **kwargs)
        self.fields["hod_rating"].required = True
        self.fields["hod_rating"].queryset = company.config.ratings.all()

    class Meta:
        model = Kra
        fields = ("hod_rating", )

    # def clean(self):
    #     rating = self.cleaned_data.get("hod_rating")
    #     threshold = rating.threshold * 0.01 * self.department.members.count()
    #     count = 0 if not hasattr(rating, "hod_rating_kras") else rating.hod_rating_kras.count()
    #     if count+1 > threshold:
    #         self.add_error("hod_rating", "Sorry, this rating has gotten to its usage threshold")
    #     return self.cleaned_data


class CompanyKraItemForm(forms.ModelForm):
    weight = forms.FloatField(min_value=1, max_value=100, required=True)
    target = forms.FloatField(min_value=1, max_value=100, required=True)

    class Meta:
        model = CompanyKraItem
        fields = ("name", "weight", "target", "description")


class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ("text", "file")

    def clean(self):
        cd = self.cleaned_data
        if not cd.get("file") and not cd.get("text"):
            forms.ValidationError("Message cannot be empty")
        return cd


class BaseKraItemFormSet(BaseInlineFormSet):

    def clean(self):
        super().clean()
        forms_to_delete = self.deleted_forms
        valid_forms = [form for form in self.forms if form.is_valid() and form not in forms_to_delete]
        total_weight = sum(f.cleaned_data['weight'] for f in valid_forms)
        if total_weight != 100:
            raise forms.ValidationError("KRA weight must sum up to 100, you have %s" % total_weight)


KraItemFormSet = inlineformset_factory(Kra, KraItem, form=KraItemForm, formset=BaseKraItemFormSet,
                                       extra=0, max_num=10, min_num=4, can_delete=False, validate_min=True,
                                       validate_max=True)


KraItemSelfAssessmentFormSet = inlineformset_factory(Kra, KraItem, form=KraItemSelfAssessmentForm, extra=0, max_num=10,
                                                     min_num=4, can_delete=False, validate_min=True, validate_max=True)


KraItemAssessmentFormSet = inlineformset_factory(Kra, KraItem, form=KraItemAssessmentForm, extra=0, max_num=10,
                                                 min_num=4, can_delete=False, validate_min=True, validate_max=True)


CompanyKraItemFormFormSet = inlineformset_factory(CompanyKra, CompanyKraItem, form=KraItemForm,
                                                  formset=BaseKraItemFormSet, extra=0, max_num=10, min_num=4,
                                                  can_delete=True, validate_min=True, validate_max=True)
