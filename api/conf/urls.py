from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

from django.conf import settings

import api.core.views


urlpatterns = [
    path("healthcheck/", include("health_check.urls")),
    path("applications/", include("api.applications.urls")),
    path("audit-trail/", include("api.audit_trail.urls")),
    path("cases/", include("api.cases.urls")),
    path("compliance/", include("api.compliance.urls")),
    path("goods/", include("api.goods.urls")),
    path("goods-types/", include("api.goodstype.urls")),
    path("letter-templates/", include("api.letter_templates.urls")),
    path("organisations/", include("api.organisations.urls")),
    path("queues/", include("api.queues.urls")),
    path("static/", include("api.staticdata.urls")),
    path("users/", include("api.users.urls")),
    path("teams/", include("api.teams.urls")),
    path("gov-users/", include("api.gov_users.urls")),
    path("flags/", include("api.flags.urls")),
    path("picklist/", include("api.picklists.urls")),
    path("documents/", include("api.documents.urls")),
    path("queries/", include("api.queries.urls")),
    path("routing-rules/", include("api.workflow.routing_rules.urls")),
    path("licences/", include("api.licences.urls")),
    path("open-general-licences/", include("api.open_general_licences.urls")),
    path("data-workspace/", include("api.data_workspace.urls")),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

handler500 = "rest_framework.exceptions.server_error"
handler400 = "rest_framework.exceptions.bad_request"

if settings.LITE_API_ENABLE_ES:
    urlpatterns += (path("search/", include("api.search.urls")),)

if settings.ADMIN_ENABLED:
    urlpatterns += (path("admin/", admin.site.urls),)

    if settings.FEATURE_STAFF_SSO_ENABLED:
        urlpatterns = [
            path("admin/login/", api.core.views.LoginProviderView.as_view()),
            path("auth/", include("authbroker_client.urls")),
        ] + urlpatterns
