from django.contrib import admin

# Register your models here.
from kra.models import Kra, KraItem, Message, KraBucket, CompanyKra, CompanyKraItem

admin.site.register(KraBucket)
admin.site.register(Kra)
admin.site.register(KraItem)
admin.site.register(Message)
admin.site.register(CompanyKra)
admin.site.register(CompanyKraItem)
