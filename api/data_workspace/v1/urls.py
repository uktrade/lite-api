from rest_framework.routers import DefaultRouter

from api.data_workspace.v1 import (
    address_views,
    advice_views,
    application_views,
    audit_views,
    case_views,
    external_data_views,
    good_views,
    licence_views,
    organisations_views,
    staticdata_views,
    users_views,
    views,
)


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
    "good-on-application-regime-entries",
    application_views.GoodOnApplicationRegimeEntriesListView,
    basename="dw-good-on-applications-regime-entries",
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
router_v1.register("regimes", staticdata_views.RegimesListView, basename="dw-regimes")
router_v1.register("regime-subsections", staticdata_views.RegimeSubsectionsListView, basename="dw-regime-subsections")
router_v1.register("regime-entries", staticdata_views.RegimeEntriesListView, basename="dw-regime-entries")
router_v1.register("goods", good_views.GoodListView, basename="dw-goods")
router_v1.register(
    "good-control-list-entries", good_views.GoodControlListEntryListView, basename="dw-good-control-list-entries"
)
router_v1.register("licences", licence_views.LicencesList, basename="dw-licences")
router_v1.register("good-on-licences", licence_views.GoodOnLicenceList, basename="dw-good-on-licences")
router_v1.register("organisations", views.OrganisationListView, basename="dw-organisations")
router_v1.register("parties", views.PartyListView, basename="dw-parties")
router_v1.register("queues", views.QueueListView, basename="dw-queues")
router_v1.register("teams", views.TeamListView, basename="dw-teams")
router_v1.register("departments", views.DepartmentListView, basename="dw-departments")
router_v1.register("case-assignment", case_views.CaseAssignmentList, basename="dw-case-assignment")
router_v1.register("case-assignment-slas", case_views.CaseAssignmentSLAList, basename="dw-case-assignment-sla")
router_v1.register("case-types", case_views.CaseTypeList, basename="dw-case-type")
router_v1.register("case-queues", case_views.CaseQueueList, basename="dw-case-queue")
router_v1.register("case-department-slas", case_views.CaseDepartmentList, basename="dw-case-department-sla")
router_v1.register("ecju-queries", case_views.EcjuQueryList, basename="dw-ecju-query")
router_v1.register(
    "external-data-denials", external_data_views.ExternalDataDenialView, basename="dw-external-data-denial"
)
router_v1.register("users-base-users", users_views.BaseUserListView, basename="dw-users-base-users")
router_v1.register("users-gov-users", users_views.GovUserListView, basename="dw-users-gov-users")
router_v1.register("audit-move-case", audit_views.AuditMoveCaseListView, basename="dw-audit-move-case")
router_v1.register("advice", advice_views.AdviceListView, basename="dw-advice")
router_v1.register(
    "advice-denial-reasons", advice_views.AdviceDenialReasonListView, basename="dw-advice-denial-reasons"
)
router_v1.register(
    "audit-updated-status", audit_views.AuditUpdatedCaseStatusListView, basename="dw-audit-updated-status"
)
router_v1.register(
    "audit-bulk-approval-recommendations",
    audit_views.AuditBulkApprovalRecommendationListView,
    basename="dw-audit-bulk-approval",
)
router_v1.register(
    "audit-licence-updated-status",
    audit_views.AuditUpdatedLicenceStatusListView,
    basename="dw-audit-licence-updated-status",
)
router_v1.register("survey-response", views.SurveyResponseListView, basename="dw-survey-reponse")
router_v1.register("address", address_views.AddressView, basename="dw-address")
router_v1.register("site", organisations_views.SiteView, basename="dw-site")

urlpatterns = router_v1.urls
