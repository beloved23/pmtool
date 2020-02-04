"""HRTool URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from rest_framework_swagger.views import get_swagger_view

from HRTool import settings

schema_view = get_swagger_view(title='Right Seat API Documentation')
urlpatterns = [
    path('api/', include("HRTool.api_urls"))
]

urlpatterns += [
    path('api-docs/', schema_view),
    path('company/', include('company.urls', namespace="company")),
    path('django/', admin.site.urls),
    path('admin/', include('superuser.urls', namespace="superuser")),
    path('kra/', include('kra.urls', namespace="kra")),
    path('tasks/', include('task.urls', namespace="task")),
    path('pip/', include('p_i_p.urls', namespace="pip")),
    path('', include('account.urls')),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
