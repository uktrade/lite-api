from django.urls import path

from applications.views import (
    applications,
    existing_parties,
    goods,
    parties,
    party_documents,
    external_locations,
    sites,
    countries,
    documents,
)

app_name = "applications"

urlpatterns = [
    # Applications
    path("", applications.ApplicationList.as_view(), name="applications"),
    path("<uuid:pk>/", applications.ApplicationDetail.as_view(), name="application"),
    path("<uuid:pk>/submit/", applications.ApplicationSubmission.as_view(), name="application_submit",),
    path("<uuid:pk>/finalise/", applications.ApplicationFinaliseView.as_view(), name="finalise"),
    path("<uuid:pk>/duration/", applications.ApplicationDurationView.as_view(), name="duration"),
    path("<uuid:pk>/status/", applications.ApplicationManageStatus.as_view(), name="manage_status",),
    # Goods
    path("<uuid:pk>/goods/", goods.ApplicationGoodsOnApplication.as_view(), name="application_goods",),
    path(
        "good-on-application/<uuid:obj_pk>/", goods.ApplicationGoodOnApplication.as_view(), name="good_on_application",
    ),
    # Goods types
    path("<uuid:pk>/goodstypes/", goods.ApplicationGoodsTypes.as_view(), name="application_goodstypes",),
    path(
        "<uuid:pk>/goodstype/<uuid:goodstype_pk>/", goods.ApplicationGoodsType.as_view(), name="application_goodstype",
    ),
    path(
        "<uuid:pk>/goodstype/<uuid:goods_type_pk>/document/",
        documents.GoodsTypeDocumentView.as_view(),
        name="goods_type_document",
    ),
    path(
        "<uuid:pk>/goodstype/assign-countries/",
        goods.ApplicationGoodsTypeCountries.as_view(),
        name="application_goodstype_assign_countries",
    ),
    # Parties
    path("<uuid:pk>/parties/", parties.ApplicationPartyView.as_view(), name="parties"),
    path("<uuid:pk>/parties/<uuid:party_pk>/", parties.ApplicationPartyView.as_view(), name="party"),
    path("<uuid:pk>/parties/<uuid:party_pk>/copy", parties.CopyPartyView.as_view(), name="copy_party"),
    path(
        "<uuid:pk>/parties/<uuid:party_pk>/document/",
        party_documents.PartyDocumentView.as_view(),
        name="party_document",
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
    path("<uuid:pk>/countries/", countries.ApplicationCountries.as_view(), name="countries",),
    # Supporting Documents
    path("<uuid:pk>/documents/", documents.ApplicationDocumentView.as_view(), name="application_documents",),
    path(
        "<uuid:pk>/documents/<uuid:doc_pk>/",
        documents.ApplicationDocumentDetailView.as_view(),
        name="application_document",
    ),
    # Case-related information
    path(
        "<uuid:pk>/generated-documents/",
        documents.GeneratedDocuments.as_view(),
        name="application_generated_documents",
    ),
    path(
        "<uuid:pk>/generated-documents/<uuid:gcd_pk>/",
        documents.GeneratedDocument.as_view(),
        name="application_generated_document",
    ),
    # Existing parties
    path("<uuid:pk>/existing-parties/", existing_parties.ExistingParties.as_view(), name="existing_parties",),
]
