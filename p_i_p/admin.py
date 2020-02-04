from django.contrib import admin

# Register your models here.
from p_i_p.models import Pip, Issue, Expectation

admin.site.register(Pip)
admin.site.register(Issue)
admin.site.register(Expectation)
