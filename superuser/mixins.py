from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import UserPassesTestMixin
from django.http import Http404
from django.shortcuts import redirect


class AllowSuperuserMixin(UserPassesTestMixin):

    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_superuser and self.request.user.is_active

    # def dispatch(self, request, *args, **kwargs):
    #     if request.user.is_anonymous:
    #         return redirect("superuser:login")
    #     if not (request.user.is_superuser and request.user.is_active):
    #         raise Http404()
    #     return super(AllowSuperuserMixin, self).dispatch(request, *args, **kwargs)
