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
    countries,
    documents,
    end_use_details,
    temporary_export_details,
)

app_name = "applications"

urlpatterns = [
    path("", applications.ApplicationList.as_view(), name="applications"),
    path("<uuid:pk>/", applications.ApplicationDetail.as_view(), name="application"),
    path("existing/", applications.ApplicationExisting.as_view(), name="existing"),
    path("<uuid:pk>/activity/", activities.ActivityView.as_view(), name="activities"),
    path("<uuid:pk>/route-of-goods/", applications.ApplicationRouteOfGoods.as_view(), name="route_of_goods"),
    path("<uuid:pk>/submit/", applications.ApplicationSubmission.as_view(), name="application_submit",),
    path("<uuid:pk>/final-decision/", applications.ApplicationFinaliseView.as_view(), name="finalise"),
    path("<uuid:pk>/duration/", applications.ApplicationDurationView.as_view(), name="duration"),
    path("<uuid:pk>/status/", applications.ApplicationManageStatus.as_view(), name="manage_status"),
    path("<uuid:pk>/copy/", applications.ApplicationCopy.as_view(), name="copy",),
    path("<uuid:pk>/end-use-details/", end_use_details.EndUseDetails.as_view(), name="end_use_details"),
    path(
        "<uuid:pk>/temporary-export-details/",
        temporary_export_details.TemporaryExportDetails.as_view(),
        name="temporary_export_details",
    ),
    # Goods
    path("<uuid:pk>/goods/", goods.ApplicationGoodsOnApplication.as_view(), name="application_goods"),
    path(
        "good-on-application/<uuid:obj_pk>/", goods.ApplicationGoodOnApplication.as_view(), name="good_on_application",
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
    # Goods types
    path("<uuid:pk>/goodstypes/", goods.ApplicationGoodsTypes.as_view(), name="application_goodstypes"),
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
    path("<uuid:pk>/parties/<uuid:party_pk>/copy/", parties.CopyPartyView.as_view(), name="copy_party"),
    path(
        "<uuid:pk>/parties/<uuid:party_pk>/document/",
        party_documents.PartyDocumentView.as_view(),
        name="party_document",
    ),
    # Sites, locations and countries
    path("<uuid:pk>/sites/", sites.ApplicationSites.as_view(), name="application_sites"),
    path("<uuid:pk>/contract-types/", countries.ApplicationContractTypes.as_view(), name="contract_types"),
    path("<uuid:pk>/countries-contract-types/", countries.LightCountries.as_view(), name="country_contract_types"),
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
    path("<uuid:pk>/countries/", countries.ApplicationCountries.as_view(), name="countries"),
    # Supporting Documents
    path("<uuid:pk>/documents/", documents.ApplicationDocumentView.as_view(), name="application_documents"),
    path(
        "<uuid:pk>/documents/<uuid:doc_pk>/",
        documents.ApplicationDocumentDetailView.as_view(),
        name="application_document",
    ),
    # Existing parties
    path("<uuid:pk>/existing-parties/", existing_parties.ExistingParties.as_view(), name="existing_parties"),
    path("<uuid:pk>/exhibition-details/", applications.ExhibitionDetails.as_view(), name="exhibition"),
]
