import csv
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.http import HttpResponseRedirect, Http404, JsonResponse, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.template.loader import render_to_string
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import CreateView, TemplateView, DetailView, RedirectView, UpdateView

from HRTool import constants
from HRTool.mixins import UserPermissionsMixin
from HRTool.notifications import NotificationManager
from kra.forms import KraItemFormSet, CompanyKraItemFormFormSet, KraItemAssessmentFormSet, KraItemSelfAssessmentFormSet, \
    KraBucketForm, MessageForm, ManagerRatingForm, HODRatingForm
from kra.models import Kra, KraBucket, CompanyKra


class KRAConfigView(UserPermissionsMixin, CreateView):
    form_class = KraBucketForm
    template_name = "kra/configuration.html"
    permissions = ("kra.add_krabucket", "kra.view_krabucket", "kra.add_companykra",
                   "kra.view_companykra", "kra.delete_companykra")

    def get_context_data(self, **kwargs):
        kwargs = super(KRAConfigView, self).get_context_data(**kwargs)
        kwargs["buckets"] = self.request.user.profile.company.kra_buckets.all()
        kwargs["kras"] = self.request.user.profile.company.kras.all()
        return kwargs

    def form_valid(self, form):
        cd = form.cleaned_data
        try:
            bucket = form.save(commit=False)
            bucket.created_by = self.request.user
            bucket.company = self.request.user.profile.company
            bucket.save()
            self.object = bucket
            messages.success(self.request, "KRA bucket for year '%s' created successfully" % cd['year'])
            NotificationManager.bucket_update_notification(self.request, bucket)
            return HttpResponseRedirect(self.get_success_url())
        except IntegrityError:
            form.add_error("year", "Sorry, your company already have a KRA bucket for year '%s'" % cd['year'])
            return self.render_to_response(self.get_context_data(form=form))


@method_decorator(login_required, "dispatch")
class KRASettingView(CreateView):
    model = Kra
    template_name = "kra/setting.html"
    form_class = KraItemFormSet

    def dispatch(self, request, *args, **kwargs):
        if "kra_identifier" in kwargs:
            self.kra = get_object_or_404(Kra, identifier=kwargs["kra_identifier"], user=request.user, status=constants.KRA_OPEN_STATUS)
            self.bucket = None
            # self.form_class = KraItemUpdateFormSet
        else:
            if "bucket" in request.GET:
                self.bucket = get_object_or_404(KraBucket, reference=self.request.GET.get("bucket"),
                                                company=self.request.user.profile.company,
                                                status=constants.KRA_BUCKET_OPEN_STATUS)
            else:
                self.bucket = None
            draft = request.user.kras.filter(status=constants.KRA_OPEN_STATUS, bucket=self.bucket)
            if draft:
                return HttpResponseRedirect(reverse("kra:setting", args=(draft.first().identifier, )))
            elif "bucket" not in request.GET:
                raise Http404()
            self.kra = None
        return super(KRASettingView, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        try:
            if self.kra:
                bucket = self.kra.bucket
            else:
                bucket = KraBucket.objects.get(reference=self.request.GET.get("bucket"),
                                               company=self.request.user.profile.company,
                                               status=constants.KRA_BUCKET_OPEN_STATUS)
            # , kras__user = self.request.user,
            # kras__is_accepted = True
            has_kra_already = False
            if self.kra is None:
                try:
                    has_kra_already = bucket.kras.filter(user=self.request.user, status__in=[constants.KRA_OPEN_STATUS,
                                                                                             constants.KRA_LOCKED_STATUS,
                                                                                             constants.KRA_CLOSED_STATUS], is_draft=False).exists()
                except:
                    has_kra_already = False
            if has_kra_already:
                form._non_form_errors = form.error_class(["Sorry, you already have a KRA setting for '"+bucket.title+"'"])
                return self.form_invalid(form)
            if self.kra is None:
                self.object = Kra.objects.create(user=self.request.user, bucket=bucket,
                                                 is_draft=self.request.POST.get("action", "submit").lower() != "submit",
                                                 status=constants.KRA_OPEN_STATUS if self.request.POST.get("action", "submit").lower() != "submit" else constants.KRA_LOCKED_STATUS)
                form.instance = self.object
            else:
                self.object = self.kra
                self.object.status = constants.KRA_OPEN_STATUS if self.request.POST.get("action", "submit").lower() != "submit" else constants.KRA_LOCKED_STATUS
                self.object.is_draft = self.request.POST.get("action", "submit").lower() != "submit"
                self.object.save()
            form.save()
            if self.object.is_draft:
                messages.success(self.request, "KRA setting saved as draft")
            else:
                if self.request.user.profile.manager:
                    NotificationManager.kra_setting_notification(self.request, self.object)
                messages.success(self.request, "KRA setting submitted for assessment")
            return HttpResponseRedirect(self.get_success_url())
        except KraBucket.DoesNotExist:
            form._non_form_errors = form.error_class(["Sorry, the KRA bucket could not be found"])
            return self.form_invalid(form)

    def get_form_kwargs(self):
        kwargs = super(KRASettingView, self).get_form_kwargs()
        kwargs["instance"] = self.kra
        return kwargs

    def get_context_data(self, **kwargs):
        kwargs = super(KRASettingView, self).get_context_data(**kwargs)
        kwargs["kra"] = self.kra
        kwargs["bucket"] = self.bucket or self.kra.bucket
        try:
            kwargs["manager_kra"] = kwargs['bucket'].kras.get(user=self.request.user.profile.manager.user, status__in=[
                    constants.KRA_LOCKED_STATUS, constants.KRA_OPEN_STATUS, constants.KRA_CLOSED_STATUS], is_draft=False)
        except Exception:
            kwargs["manager_kra"] = None
        return kwargs


@method_decorator(login_required, "dispatch")
class KRADetailView(DetailView):
    model = Kra
    template_name = "kra/view.html"
    slug_url_kwarg = "kra_identifier"
    slug_field = "identifier"

    def get_object(self, queryset=None):
        kra = super(KRADetailView, self).get_object(queryset)
        is_hod = kra.user.profile.department.director == self.request.user.profile if kra.user.profile.department else False
        self.is_hod = is_hod if kra.user.profile != self.request.user.profile else False
        if not (is_hod or self.request.user.is_staff or self.request.user.profile.is_ceo or kra.user == self.request.user or self.request.user.has_perm("kra.view_kra")):
            raise Http404()
        self.new_messages = kra.messages.filter(read=False).exclude(user=self.request.user)
        return kra

    def get_context_data(self, **kwargs):
        kwargs = super(KRADetailView, self).get_context_data(**kwargs)
        kwargs["is_hod"] = self.object.user.profile.department.director == self.request.user.profile if self.object.user.profile.department else False
        if (not self.object.hod_rating or self.request.user.profile.is_ceo) and "ratingForm" not in kwargs:
            kwargs["ratingForm"] = HODRatingForm(self.request.POST or None, instance=self.object, company=self.request.user.profile.company)
        return kwargs

    def get(self, request, *args, **kwargs):
        resp = super(KRADetailView, self).get(request, *args, **kwargs)
        if "get_messages" in request.GET:
            resp = {"success": True,
                    "messages": render_to_string("kra/messages.html", {"messages": self.new_messages, "user": request.user})}
            self.new_messages.update(read=True)
            return JsonResponse(resp)
        self.new_messages.update(read=True)
        return resp

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.new_messages.update(read=True)
        kra = self.object
        resp = {"error": True, "message": "Unexpected data"}
        if "message" in request.GET:
            form = MessageForm(request.POST, files=request.FILES)
            if form.is_valid():
                message = form.save(commit=False)
                message.kra = kra
                message.user = request.user
                if form.cleaned_data.get("file"):
                    message.file_type = form.cleaned_data.get("file").content_type
                    message.filename = form.cleaned_data.get("file").name
                message.save()
                msgs = kra.messages.filter(pk__gte=message.pk)
                resp = {"success": True,
                        "messages": render_to_string("kra/messages.html", {"messages": msgs, "user": request.user})}
        elif "modify" in request.GET:
            kra.status = constants.KRA_OPEN_STATUS
            kra.save()
            resp = {"success": True, "message": "KRA setting has been opened for modifications successfully"}
        elif "reject" in request.GET:
            kra.status = constants.KRA_REJECTED_STATUS
            kra.save()
            resp = {"success": True, "message": "KRA setting has been rejected successfully"}
        elif "accept" in request.GET:
            kra.is_accepted = True
            kra.save()
            resp = {"success": True, "message": "KRA setting has been accepted successfully"}
        else:
            if (self.object.hod_rating and not (self.is_hod or request.user.profile.is_ceo)) or (self.object.hod_rating and not request.user.profile.is_ceo):
                raise Http404()
            ratingForm = HODRatingForm(self.request.POST or None, instance=self.object, company=self.request.user.profile.company)
            if ratingForm.is_valid():
                ratingForm.save()
                messages.success(request, "Rating updated successfully")
                return HttpResponseRedirect(request.META["HTTP_REFERER"])
            return self.render_to_response(self.get_context_data(ratingForm=ratingForm))
        if not kra.is_draft:
            NotificationManager.kra_update_notification(request, kra)
        return JsonResponse(resp)


@method_decorator(login_required, "dispatch")
class KRAManagementView(TemplateView):
    template_name = "kra/management.html"

    def get_context_data(self, **kwargs):
        kwargs = super(KRAManagementView, self).get_context_data(**kwargs)
        if "reference" in self.kwargs:
            bucket = get_object_or_404(KraBucket, reference=self.kwargs["reference"],
                                       company=self.request.user.profile.company)
        else:
            bucket = self.request.user.profile.company.kra_buckets.first()
        if hasattr(bucket, "kras"):
            kwargs["descendants_kras"] = bucket.kras.filter(user__profile__in=self.request.user.profile.child_members.all(), is_draft=False)
            kwargs["kras"] = bucket.kras.filter(user=self.request.user)
        else:
            kwargs["descendants_kras"] = []
            kwargs["kras"] = []
        try:
            kwargs["manager_kra"] = bucket.kras.get(user=self.request.user.profile.manager.user, status__in=[
                    constants.KRA_LOCKED_STATUS, constants.KRA_OPEN_STATUS, constants.KRA_CLOSED_STATUS], is_draft=False)
        except Exception:
            kwargs["manager_kra"] = None
        try:
            kwargs["company_kra"] = bucket.company_kra
        except Exception:
            kwargs["company_kra"] = None
        kwargs["bucket"] = bucket
        return kwargs


@method_decorator(login_required, "dispatch")
class KRAAssessmentView(UpdateView):
    template_name = "kra/assessment.html"
    model = Kra
    slug_field = "identifier"
    slug_url_kwarg = "kra_identifier"
    form_class = KraItemAssessmentFormSet
    queryset = Kra.objects.filter(status=constants.KRA_LOCKED_STATUS, is_accepted=True)

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        bucket = self.get_object().bucket
        if not bucket.allow_final_assessment:
            raise Http404()
        if request.user.profile != self.object.user.profile.manager and not request.user.profile.is_ceo:
            raise Http404()
        if (
                self.object.status != constants.KRA_LOCKED_STATUS and not self.object.is_accepted) and not request.user.profile.is_ceo:
            raise Http404()
        resp = super(KRAAssessmentView, self).dispatch(request, *args, **kwargs)
        return resp

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        ratingForm = self.get_rating_form()
        if form.is_valid() and ratingForm.is_valid():
            form.save()
            self.object = ratingForm.save()
            self.object.status = constants.KRA_CLOSED_STATUS
            self.object.save()
            messages.success(self.request, "KRA Assessment completed successfully")
            NotificationManager.kra_update_notification(request, self.object)
            return redirect(self.get_success_url())
        else:
            return self.render_to_response(self.get_context_data(form=form, ratingForm=ratingForm))

    def get_rating_form(self):
        return ManagerRatingForm(self.request.POST or None, instance=self.get_object(), company=self.request.user.profile.company)

    def get_context_data(self, **kwargs):
        kwargs = super(KRAAssessmentView, self).get_context_data(**kwargs)
        if "ratingForm" not in kwargs:
            kwargs["ratingForm"] = self.get_rating_form()
        return kwargs


@method_decorator(login_required, "dispatch")
class KRASelfAssessmentView(UpdateView):
    template_name = "kra/self-assessment.html"
    model = Kra
    slug_field = "identifier"
    slug_url_kwarg = "kra_identifier"
    form_class = KraItemSelfAssessmentFormSet

    def get_queryset(self):
        return self.request.user.kras.filter(status=constants.KRA_LOCKED_STATUS, is_accepted=True)

    def dispatch(self, request, *args, **kwargs):
        bucket = self.get_object().bucket
        if not bucket.allow_self_assessment:
            raise Http404()
        resp = super(KRASelfAssessmentView, self).dispatch(request, *args, **kwargs)
        return resp

    def form_valid(self, form):
        form.save()
        self.object.self_assessed = True
        self.object.save()
        NotificationManager.kra_update_notification(self.request, self.object)
        messages.success(self.request, "KRA Self-assessment completed successfully")
        return HttpResponseRedirect(self.object.get_absolute_url())


class KRABucketView(UserPermissionsMixin, DetailView):
    slug_url_kwarg = "reference"
    slug_field = "reference"
    model = KraBucket
    template_name = "kra/kra_bucket_detail.html"

    def get_queryset(self):
        return self.request.user.profile.company.kra_buckets.all()

    def get_chart_data(self):
        ratings = self.request.user.profile.company.config.ratings.all()
        data = []
        for rating in ratings:
            data.append((rating.name, rating.hod_rating_kras.filter(bucket=self.object).count()))
        return data

    def get_context_data(self, **kwargs):
        kwargs = super(KRABucketView, self).get_context_data(**kwargs)
        kwargs["chart_data"] = self.get_chart_data()
        return kwargs


class KRABucketToggle(UserPermissionsMixin, RedirectView):
    url = reverse_lazy("kra:configuration")
    permissions = ("kra.change_krabucket", )

    def get(self, request, *args, **kwargs):
        bucket = get_object_or_404(KraBucket, reference=kwargs.get("reference"))
        if "assessment" in request.GET:
            bucket.allow_final_assessment = not bucket.allow_final_assessment
        elif "self-assessment" in request.GET:
            bucket.allow_self_assessment = not bucket.allow_self_assessment
        else:
            if bucket.status == constants.KRA_BUCKET_CLOSED_STATUS:
                bucket.status = constants.KRA_BUCKET_OPEN_STATUS
            else:
                bucket.status = constants.KRA_BUCKET_CLOSED_STATUS
        bucket.updated_by = request.user
        bucket.save()
        NotificationManager.bucket_update_notification(request, bucket)
        messages.success(request, "KRA Bucket updated successfully")
        return super(KRABucketToggle, self).get(request, *args, **kwargs)


@method_decorator(login_required, "dispatch")
class CompanyKRASettingView(UserPermissionsMixin, CreateView):
    model = CompanyKra
    template_name = "kra/company-setting.html"
    form_class = CompanyKraItemFormFormSet
    permissions = ("kra.add_companykra", "kra.change_companykra")

    def dispatch(self, request, *args, **kwargs):
        if "kra_identifier" in kwargs:
            self.kra = get_object_or_404(CompanyKra, identifier=kwargs["kra_identifier"], company=request.user.profile.company)
            # self.form_class = KraItemUpdateFormSet
        else:
            draft = request.user.profile.company.kras.filter(is_draft=True)
            if draft:
                return HttpResponseRedirect(reverse("kra:company-setting", args=(draft.first().identifier, )))
            self.kra = None
        return super(CompanyKRASettingView, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        try:
            if self.kra:
                bucket = self.kra.bucket
            else:
                bucket = KraBucket.objects.get(reference=self.request.POST.get("bucket"), company=self.request.user.profile.company, status=constants.KRA_BUCKET_OPEN_STATUS)
            kra_exists = CompanyKra.objects.filter(bucket=bucket).exists()
            print(bucket)
            print(kra_exists)
            # print(hasattr(bucket, "company_kra"))
            # print(self.request.POST.get("action", "submit").lower())
            # print(bucket.company_kra.is_draft)
            if kra_exists and not self.kra and not (hasattr(bucket, "company_kra") and bucket.company_kra.is_draft):
                form._non_form_errors = form.error_class(
                    ["Sorry, you already have a Company's KRA setting for '" + bucket.title + "'"])
                return self.form_invalid(form)
            if self.kra is None:
                self.object = CompanyKra.objects.create(
                    is_draft=self.request.POST.get("action", "submit").lower() != "submit",
                    created_by=self.request.user,
                    company=self.request.user.profile.company,
                    bucket=bucket,
                    status=constants.KRA_OPEN_STATUS if self.request.POST.get("action", "submit").lower() != "submit" else constants.KRA_LOCKED_STATUS)
                form.instance = self.object
            else:
                self.object = self.kra
                self.object.status = constants.KRA_OPEN_STATUS if self.request.POST.get("action", "submit").lower() != "submit" else constants.KRA_LOCKED_STATUS
                self.object.is_draft = self.request.POST.get("action", "submit").lower() != "submit"
                self.object.updated_by = self.request.user
                self.object.save()
            form.save()
            if self.object.is_draft:
                messages.success(self.request, "Company's KRA setting saved as draft")
            else:
                messages.success(self.request, "Company's KRA setting created successfully")
            return HttpResponseRedirect(self.get_success_url())
        except KraBucket.DoesNotExist:
            form._non_form_errors = form.error_class(["Sorry, the KRA bucket could not be found"])
            return self.form_invalid(form)

    def get_form_kwargs(self):
        kwargs = super(CompanyKRASettingView, self).get_form_kwargs()
        kwargs["instance"] = self.kra
        return kwargs

    def get_context_data(self, **kwargs):
        kwargs = super(CompanyKRASettingView, self).get_context_data(**kwargs)
        kwargs["kra"] = self.kra
        return kwargs


@method_decorator(login_required, "dispatch")
class CompanyKRADetailView(UserPermissionsMixin, DetailView):
    model = CompanyKra
    template_name = "kra/company-kra-view.html"
    slug_url_kwarg = "kra_identifier"
    slug_field = "identifier"
    permissions = ("kra.view_companykra", )


class DeleteKRA(RedirectView):
    url = reverse_lazy("kra:management")

    def get(self, request, *args, **kwargs):
        kra = get_object_or_404(Kra, identifier=kwargs.get("kra_identifier"), user=request.user, is_draft=True)
        self.url = reverse_lazy("kra:management", kwargs={"reference": kra.bucket.reference})
        kra.delete()
        messages.success(request, "KRA deleted successfully")
        return super(DeleteKRA, self).get(request, *args, **kwargs)


@login_required()
def download_bucket_report(request, reference):
    bucket = get_object_or_404(KraBucket, reference=reference)
    if bucket.company != request.user.profile.company:
        raise Http404()
    headers = ("name", "description", "weight", "target", "actual", "achievement", "manager_achievement",
               "comment", "manager_comment")
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment;filename=%s-kras.csv' % bucket.title.replace(" ", "-")
    writer = csv.writer(response)
    for kra in bucket.kras.all():
        writer.writerow(["Title:", kra.bucket.title])
        writer.writerow(['Staff:', kra.user.get_full_name() + "("+kra.profile.auuid+")"])
        department = kra.profile.department
        writer.writerow(['Department:', kra.profile.department.name if kra.profile.department else "-"])
        writer.writerow(['Line Manager:', kra.profile.manager.user.get_full_name() + "("+kra.profile.manager.auuid+")" if kra.profile.manager else "-"])
        writer.writerow(['Department Director:', department.director.user.get_full_name() + "("+department.director.auuid+")" if department and department.director else "-"])
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
def download_kra_report(request, kra_identifier):
    kra = get_object_or_404(Kra, identifier=kra_identifier)
    if kra.profile.company != request.user.profile.company:
        raise Http404()
    headers = ("name", "description", "weight", "target", "actual", "achievement", "manager_achievement",
               "comment", "manager_comment")
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment;filename=%s-%s-%s-%s-kra.csv' % (kra.user.first_name, kra.user.last_name, kra.user.profile.auuid, kra.bucket.year)
    writer = csv.writer(response)
    writer.writerow(["Title:", kra.bucket.title])
    writer.writerow(['Staff:', kra.user.get_full_name() + "("+kra.profile.auuid+")"])
    department = kra.profile.department
    writer.writerow(['Department:', kra.profile.department.name if kra.profile.department else "-"])
    writer.writerow(['Line Manager:', kra.profile.manager.user.get_full_name() + "("+kra.profile.manager.auuid+")" if kra.profile.manager else "-"])
    writer.writerow(['Department Director:', department.director.user.get_full_name() + "("+department.director.auuid+")" if department and department.director else "-"])
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
    return response
