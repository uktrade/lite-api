from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include, re_path
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions

from conf import settings
from conf.settings import ADMIN_ENABLED

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
    path("cases/", include("cases.urls")),
    path("goods/", include("goods.urls")),
    path("goodstype/", include("goodstype.urls")),
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
    path("licences/", include("licences.urls")),
    re_path(r"^swagger(?P<format>\.json|\.yaml)$", schema_view.without_ui(cache_timeout=0), name="schema-json",),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

if ADMIN_ENABLED:
    urlpatterns += (path("admin/", admin.site.urls),)
