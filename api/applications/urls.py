from django.urls import path

from api.applications.views import (
    applications,
    activities,
    existing_parties,
    goods,
    parties,
    party_documents,
    external_locations,
    sites,
    documents,
    end_use_details,
    temporary_export_details,
    denials,
    amendments,
)

from api.exporter.applications.views import ApplicationQuantityValueUpdateView

app_name = "applications"

urlpatterns = [
    path("", applications.ApplicationList.as_view(), name="applications"),
    path(
        "require-serial-numbers/",
        applications.ApplicationsRequireSerialNumbersList.as_view(),
        name="require_serial_numbers",
    ),
    path("<uuid:pk>/", applications.ApplicationDetail.as_view(), name="application"),
    path("existing/", applications.ApplicationExisting.as_view(), name="existing"),
    path("<uuid:pk>/activity/", activities.ActivityView.as_view(), name="activities"),
    path("<uuid:pk>/route-of-goods/", applications.ApplicationRouteOfGoods.as_view(), name="route_of_goods"),
    path(
        "<uuid:pk>/submit/",
        applications.ApplicationSubmission.as_view(),
        name="application_submit",
    ),
    path("<uuid:pk>/final-decision/", applications.ApplicationFinaliseView.as_view(), name="finalise"),
    path("<uuid:pk>/duration/", applications.ApplicationDurationView.as_view(), name="duration"),
    path("<uuid:pk>/sub-status/", applications.ApplicationManageSubStatus.as_view(), name="manage_sub_status"),
    path("<uuid:pk>/sub-statuses/", applications.ApplicationSubStatuses.as_view(), name="application_sub_statuses"),
    path(
        "<uuid:pk>/copy/",
        applications.ApplicationCopy.as_view(),
        name="copy",
    ),
    path("<uuid:pk>/end-use-details/", end_use_details.EndUseDetails.as_view(), name="end_use_details"),
    path(
        "<uuid:pk>/temporary-export-details/",
        temporary_export_details.TemporaryExportDetails.as_view(),
        name="temporary_export_details",
    ),
    # Goods
    path("<uuid:pk>/goods/", goods.ApplicationGoodsOnApplication.as_view(), name="application_goods"),
    path(
        "<uuid:pk>/goods-on-application/",
        goods.ApplicationGoodOnApplicationUpdateViewInternal.as_view(),
        name="good_on_application_update_internal",
    ),
    path(
        "good-on-application/<uuid:obj_pk>/",
        goods.ApplicationGoodOnApplication.as_view(),
        name="good_on_application",
    ),
    path(
        "<uuid:pk>/goods/<uuid:good_pk>/documents/",
        goods.ApplicationGoodOnApplicationDocumentView.as_view(),
        name="application-goods-documents",
    ),
    path(
        "<uuid:pk>/goods/<uuid:good_pk>/documents/<uuid:doc_pk>/",
        goods.ApplicationGoodOnApplicationDocumentDetailView.as_view(),
        name="application-goods-document-detail",
    ),
    path(
        "<uuid:pk>/good-on-application/<uuid:good_on_application_pk>/update-serial-numbers/",
        goods.ApplicationGoodOnApplicationUpdateSerialNumbers.as_view(),
        name="good_on_application_update_serial_numbers",
    ),
    # Parties
    path("<uuid:pk>/parties/", parties.ApplicationPartyView.as_view(), name="parties"),
    path("<uuid:pk>/parties/<uuid:party_pk>/", parties.ApplicationPartyView.as_view(), name="party"),
    path("<uuid:pk>/parties/<uuid:party_pk>/copy/", parties.CopyPartyView.as_view(), name="copy_party"),
    path(
        "<uuid:pk>/parties/<uuid:party_pk>/document/",
        party_documents.PartyDocumentView.as_view(),
        name="party_document",
    ),
    path(
        "<uuid:pk>/parties/<uuid:party_pk>/document/<uuid:document_pk>/",
        party_documents.PartyDocumentView.as_view(),
        name="party_document_view",
    ),
    path(
        "<uuid:pk>/parties/<uuid:party_pk>/document/<uuid:document_pk>/stream/",
        party_documents.PartyDocumentStream.as_view(),
        name="party_document_stream",
    ),
    # Sites, locations and countries
    path("<uuid:pk>/sites/", sites.ApplicationSites.as_view(), name="application_sites"),
    path(
        "<uuid:pk>/external_locations/",
        external_locations.ApplicationExternalLocations.as_view(),
        name="application_external_locations",
    ),
    path(
        "<uuid:pk>/external_locations/<uuid:ext_loc_pk>/",
        external_locations.ApplicationRemoveExternalLocation.as_view(),
        name="application_remove_external_location",
    ),
    # Supporting Documents
    path("<uuid:pk>/documents/", documents.ApplicationDocumentView.as_view(), name="application_documents"),
    path(
        "<uuid:pk>/documents/<uuid:doc_pk>/",
        documents.ApplicationDocumentDetailView.as_view(),
        name="application_document",
    ),
    # Existing parties
    path("<uuid:pk>/existing-parties/", existing_parties.ExistingParties.as_view(), name="existing_parties"),
    # Denial matches
    path(
        "<uuid:pk>/denial-matches/",
        denials.ApplicationDenialMatchesOnApplication.as_view(),
        name="application_denial_matches",
    ),
    path(
        "<uuid:pk>/appeals/",
        applications.ApplicationAppeals.as_view(),
        name="appeals",
    ),
    path(
        "<uuid:pk>/appeals/<uuid:appeal_pk>/",
        applications.ApplicationAppeal.as_view(),
        name="appeal",
    ),
    path(
        "<uuid:pk>/amendment/",
        amendments.CreateApplicationAmendment.as_view(),
        name="create_amendment",
    ),
    # Exporter specific endpoints
    path(
        "<uuid:pk>/good-on-application/<uuid:good_on_application_pk>/quantity-value/",
        ApplicationQuantityValueUpdateView.as_view(),
        name="application_goods_quantity_value",
    ),
]
