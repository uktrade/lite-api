from django.urls import path, include
from rest_framework.routers import DefaultRouter

from api.data_workspace import (
    application_views,
    case_views,
    good_views,
    license_views,
    views,
    staticdata_views,
    external_data_views,
)

app_name = "data_workspace"

router_v0 = DefaultRouter()
router_v0.register("licences", license_views.LicencesListDW, basename="dw-licences-only")
router_v0.register("ogl", license_views.OpenGeneralLicenceListDW, basename="dw-ogl-only")

router_v1 = DefaultRouter()
router_v1.register(
    "standard-applications", application_views.StandardApplicationListView, basename="dw-standard-applications"
)
router_v1.register(
    "good-on-applications", application_views.GoodOnApplicationListView, basename="dw-good-on-applications"
)
router_v1.register(
    "good-on-application-control-list-entries",
    application_views.GoodOnApplicationControlListEntriesListView,
    basename="dw-good-on-applications-control-list-entries",
)
router_v1.register(
    "party-on-applications", application_views.PartyOnApplicationListView, basename="dw-party-on-applications"
)
router_v1.register(
    "denial-match-on-applications",
    application_views.DenialMatchOnApplicationListView,
    basename="dw-denial-match-on-applications",
)
router_v1.register(
    "control-list-entries", staticdata_views.ControlListEntriesListView, basename="dw-control-list-entries"
)
router_v1.register("countries", staticdata_views.CountriesListView, basename="dw-countries")
router_v1.register("case-statuses", staticdata_views.CaseStatusListView, basename="dw-case-statuses")
router_v1.register("goods", good_views.GoodListView, basename="dw-goods")
router_v1.register(
    "good-control-list-entries", good_views.GoodControlListEntryListView, basename="dw-good-control-list-entries"
)
router_v1.register("licences", license_views.LicencesList, basename="dw-licences")
router_v1.register("good-on-licences", license_views.GoodOnLicenceList, basename="dw-good-on-licences")
router_v1.register("organisations", views.OrganisationListView, basename="dw-organisations")
router_v1.register("parties", views.PartyListView, basename="dw-parties")
router_v1.register("queues", views.QueueListView, basename="dw-queues")
router_v1.register("teams", views.TeamListView, basename="dw-teams")
router_v1.register("case-assignment-slas", case_views.CaseAssignmentSlaList, basename="dw-case-assignment-sla")
router_v1.register("case-types", case_views.CaseTypeList, basename="dw-case-type")
router_v1.register("case-queues", case_views.CaseQueueList, basename="dw-case-queue")
router_v1.register("external-data", external_data_views.ExternalDataDenialView, basename="dw-external-data-denial")

urlpatterns = [
    path("v0/", include(router_v0.urls)),
    path("v1/", include(router_v1.urls)),
]
