from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

from django.conf import settings

import api.core.views
from api.healthcheck.views import HealthCheckPingdomView, ServiceAvailableHealthCheckView

urlpatterns = [
    path("healthcheck/", include("health_check.urls")),
    path("pingdom/ping.xml", HealthCheckPingdomView.as_view(), name="healthcheck-pingdom"),
    path("service-available-check/", ServiceAvailableHealthCheckView.as_view(), name="service-available-check"),
    path("applications/", include("api.applications.urls")),
    path("assessments/", include("api.assessments.urls")),
    path("audit-trail/", include("api.audit_trail.urls")),
    path("cases/", include("api.cases.urls")),
    path("compliance/", include("api.compliance.urls")),
    path("goods/", include("api.goods.urls")),
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
    path(
        "data-workspace/", include("api.data_workspace.urls")
    ),  # when changing this value please update schema_generator_urls.py
    path("external-data/", include("api.external_data.urls")),
    path("bookmarks/", include("api.bookmarks.urls")),
    path("appeals/", include("api.appeals.urls")),
    path("survey/", include("api.survey.urls")),
    path("caseworker/", include("api.conf.caseworker_urls")),
    path("exporter/", include("api.conf.exporter_urls")),
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

if settings.ENABLE_DJANGO_SILK:
    urlpatterns += [path("silk/", include("silk.urls", namespace="silk"))]

if settings.MOCK_VIRUS_SCAN_ACTIVATE_ENDPOINTS:
    urlpatterns += [path("mock_virus_scan/", include("mock_virus_scan.urls"))]
