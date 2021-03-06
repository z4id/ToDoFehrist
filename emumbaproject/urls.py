"""emumbaproject URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
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
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

from emumbaproject.views import RootView

# OpenAPI/Swagger based REST API Doc
SchemaView = get_schema_view(
    openapi.Info(
        title="ToDoFehrist Restful API",
        default_version='v1',
        description="A ToDo App BackEnd built on top of Django-Python-PostgreSQL stack",
        terms_of_service="https://www.emumba.com",
        contact=openapi.Contact(email="zaid.afzal@emumba.com"),
        license=openapi.License(name="MIT"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)


urlpatterns = [

    # Swagger API Doc Generator Routes
    re_path(r'^doc(?P<format>\.json|\.yaml)$',
            SchemaView.without_ui(cache_timeout=0), name='schema-json'),
    path('doc/', SchemaView.with_ui('swagger', cache_timeout=0),
         name='schema-swagger-ui'),
    path('redoc/', SchemaView.with_ui('redoc', cache_timeout=0),
         name='schema-redoc'),

    path('', RootView.as_view()),
    path('admin/', admin.site.urls),
    path(f'{settings.API_URL}/', include('todofehrist.urls')),
]
