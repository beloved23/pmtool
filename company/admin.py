from django.contrib import admin

# Register your models here.
from company.models import Company, Department, Role, Config, Rating

admin.site.register(Company)
admin.site.register(Department)
admin.site.register(Role)
admin.site.register(Config)
admin.site.register(Rating)
