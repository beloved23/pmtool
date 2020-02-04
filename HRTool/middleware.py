from django.shortcuts import redirect
from django.urls import resolve
from django.utils.deprecation import MiddlewareMixin


class PasswordChangedMiddleware(MiddlewareMixin):

    def process_request(self, request):
        current_url = resolve(request.path_info).url_name
        exempt_urls = ['logout', "change-password"]
        if current_url not in exempt_urls:
            if request.user.is_authenticated:
                if hasattr(request.user, "profile") and not request.user.profile.password_changed:
                    return redirect("change-password")
