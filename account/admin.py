import csv

from django.contrib import admin

# Register your models here.
from account.models import Profile

admin.site.register(Profile)
# from django.contrib.auth.admin import UserAdmin
# from django.contrib.auth.models import User
# from django.http import HttpResponse
#
#
# class CustomUserAdmin(UserAdmin):
#     actions = ['download_selected', ]
#
#     def download_selected(self, request, queryset):
#         headers = ("username", "email", "first_name", "last_name", "last_login")
#         response = HttpResponse(content_type='text/csv')
#         response['Content-Disposition'] = 'attachment;filename=Users.csv'
#         writer = csv.writer(response)
#         writer.writerow([header.upper() for header in headers])
#         for obj in queryset:
#             line = []
#             for header in headers:
#                 line.append(getattr(obj, header))
#             writer.writerow(line)
#         return response
#
#
# admin.site.unregister(User)
# admin.site.register(User, CustomUserAdmin)
