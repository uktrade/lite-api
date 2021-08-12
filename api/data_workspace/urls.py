from django.urls import path, include
from rest_framework.routers import DefaultRouter

from api.data_workspace import application_views, case_views, license_views

app_name = "data_workspace"

router = DefaultRouter()
router.register(
    "v1/standard-applications", application_views.StandardApplicationListView, basename="dw-standard-applications"
)
router.register(
    "v1/good-on-applications", application_views.GoodOnApplicationListView, basename="dw-good-on-applications"
)
router.register(
    "v1/party-on-applications", application_views.PartyOnApplicationListView, basename="dw-party-on-applications"
)
router.register(
    "v1/control-list-entries", staticdata_views.ControlListEntriesListView, basename="dw-control-list-entries"
)
router.register("v1/countries", staticdata_views.CountriesListView, basename="dw-countries")
router.register("v1/case-statuses", staticdata_views.CaseStatusListView, basename="dw-case-statuses")
router.register("v1/goods", good_views.GoodListView, basename="dw-goods")
router.register("v1/licences", license_views.LicencesListDW, basename="dw-licences")
router.register("v1/ogl", license_views.OpenGeneralLicenceListDW, basename="dw-ogl")
router.register("v1/good-on-licences", license_views.GoodOnLicenceList, basename="dw-good-on-licences")
router.register("v1/case-assignment-slas", case_views.CaseAssignmentSlaList, basename="dw-case-assignment-sla")
router.register("v1/case-types", case_views.CaseTypeList, basename="dw-case-type")
router.register("v1/case-queues", case_views.CaseQueueList, basename="dw-case-queue")

urlpatterns = [
    path("", include(router.urls)),
]
