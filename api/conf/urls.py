from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include, re_path
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions

from django.conf import settings

import api.core.views


api_info = openapi.Info(
    title="LITE API",
    default_version="v0.3",
    description="Service for handling backend calls in LITE.",
    terms_of_service="https://github.com/uktrade/lite-api/blob/master/LICENSE",
    contact=openapi.Contact(url="https://github.com/uktrade/lite-api/", email="tbd@local"),
    license=openapi.License(name="MIT License"),
)
schema_view = get_schema_view(api_info, public=True, permission_classes=(permissions.AllowAny,),)

urlpatterns = [
    path("applications/", include("applications.urls")),
    path("audit-trail/", include("audit_trail.urls")),
    path("cases/", include("cases.urls")),
    path("compliance/", include("compliance.urls")),
    path("goods/", include("goods.urls")),
    path("goods-types/", include("goodstype.urls")),
    path("letter-templates/", include("letter_templates.urls")),
    path("organisations/", include("organisations.urls")),
    path("queues/", include("queues.urls")),
    path("static/", include("static.urls")),
    path("users/", include("users.urls")),
    path("teams/", include("teams.urls")),
    path("gov-users/", include("gov_users.urls")),
    path("flags/", include("flags.urls")),
    path("picklist/", include("picklists.urls")),
    path("documents/", include("documents.urls")),
    path("queries/", include("queries.urls")),
    path("routing-rules/", include("workflow.routing_rules.urls")),
    path("licences/", include("licences.urls")),
    path("open-general-licences/", include("open_general_licences.urls")),
    path("search/", include("search.urls")),
    re_path(r"^swagger(?P<format>\.json|\.yaml)$", schema_view.without_ui(cache_timeout=0), name="schema-json",),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

if settings.ADMIN_ENABLED:
    urlpatterns += (path("admin/", admin.site.urls),)

    if settings.FEATURE_STAFF_SSO_ENABLED:
        urlpatterns = [
            path("admin/login/", api.core.views.LoginProviderView.as_view()),
            path("auth/", include("authbroker_client.urls")),
        ] + urlpatterns
