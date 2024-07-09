from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.shortcuts import redirect
from django.urls import include, path, re_path
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAdminUser

swagger_info = openapi.Info(
    title="WaveView API",
    default_version="v1",
    description="WaveView API endpoints",
    terms_of_service="https://www.google.com/policies/terms/",
    contact=openapi.Contact(email="bpptkg@esdm.go.id"),
    license=openapi.License(name="(c) 2024 BPPTKG"),
)

schema_view = get_schema_view(
    public=True,
    permission_classes=[IsAdminUser],
    authentication_classes=[SessionAuthentication],
)

urlpatterns = [
    path("admin/", admin.site.urls),
    re_path(
        r"^waveview-api(?P<format>\.json|\.yaml)$",
        schema_view.without_ui(cache_timeout=0),
        name="schema-json",
    ),
    re_path(
        r"^swagger/$",
        schema_view.with_ui("swagger", cache_timeout=0),
        name="schema-swagger-ui",
    ),
    re_path(
        r"^redoc/$",
        schema_view.with_ui("redoc", cache_timeout=0),
        name="schema-redoc",
    ),
    path("api/v1/", include("waveview.api.urls")),
    re_path(r"^$", lambda _: redirect("redoc/", permanent=False)),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
