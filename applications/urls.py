from django.urls import path

from applications.views import applications, goods, parties, party_documents, \
    external_locations, sites, countries, documents

app_name = 'applications'

urlpatterns = [
    # ex: /applications/ - List all applications
    # ex: /applications/?submitted=true - List only submitted applications
    path(
        route='',
        view=applications.ApplicationList.as_view(),
        name='applications'
    ),
    # ex: /applications/<uuid:pk>/ - View an application
    path(
        route='<uuid:pk>/',
        view=applications.ApplicationDetail.as_view(),
        name='application'
    ),
    # ex: /applications/<uuid:pk>/submit/ - Submit an application
    path(
        route='<uuid:pk>/submit/',
        view=applications.ApplicationSubmission.as_view(),
        name='application_submit'
    ),
    # ex: /applications/<uuid:pk>/status/ - Manage application status
    path(
        route='<uuid:pk>/status/',
        view=applications.ApplicationManageStatus.as_view(),
        name='manage_status'
    ),
    # ex: /applications/<uuid:pk>/goods/
    path(
        route='<uuid:pk>/goods/',
        view=goods.ApplicationGoodsOnApplication.as_view(),
        name='application_goods'
    ),
    # ex: /applications/good-on-application/<uuid:good_on_application_pk>/
    path(
        route='good-on-application/<uuid:good_on_application_pk>/',
        view=goods.ApplicationGoodOnApplication.as_view(),
        name='good_on_application'
    ),
    # ex: /applications/<uuid:pk>/goodstype/
    path(
        route='<uuid:pk>/goodstypes/',
        view=goods.ApplicationGoodsTypes.as_view(),
        name='application_goodstypes'
    ),
    # ex: /applications/<uuid:pk>/goodstype/<uuid:goodstype_pk>/
    path(
        route='<uuid:pk>/goodstype/<uuid:goodstype_pk>/',
        view=goods.ApplicationGoodsType.as_view(),
        name='application_goodstype'
    ),
    # ex: /applications/<uuid:pk>/goodstype/<uuid:goodstype_pk>/document/
    path(route='<uuid:pk>/goodstype/<uuid:goodstype_pk>/document/',
         view=documents.GoodsTypeDocumentView.as_view(),
         name='documents'),
    # TODO: verify why this endpoint receiving a list of goodstypes
    # ex: /applications/<uuid:pk>/goodstype/<uuid:goodstype_pk>/assign-countries/
    path(
        route='<uuid:pk>/goodstype/<uuid:goodstype_pk>/assign-countries/',
        view=goods.ApplicationGoodsTypeCountries.as_view(),
        name='application_goodstype_assign_countries'
    ),
    # ex: /applications/<uuid:pk>/end-user/
    path(
        route='<uuid:pk>/end-user/',
        view=parties.ApplicationEndUser.as_view(),
        name='end_user'
    ),
    # ex: /applications/<uuid:pk>/end-user/document/
    path(
        route='<uuid:pk>/end-user/document/',
        view=party_documents.EndUserDocumentView.as_view(),
        name='end_user_document'
    ),
    # ex: /applications/<uuid:pk>/ultimate-end-users/
    path(
        route='<uuid:pk>/ultimate-end-users/',
        view=parties.ApplicationUltimateEndUsers.as_view(),
        name='ultimate_end_users'
    ),
    # ex: /applications/<uuid:pk>/ultimate-end-users/<uuid:ueu_pk>
    path(
        route='<uuid:pk>/ultimate-end-users/<uuid:ueu_pk>',
        view=parties.RemoveApplicationUltimateEndUser.as_view(),
        name='remove_ultimate_end_user'
    ),
    # ex: /applications/<uuid:pk>/ultimate-end-user/<uuid:ueu_pk>/document/
    path(
        route='<uuid:pk>/ultimate-end-user/<uuid:ueu_pk>/document/',
        view=party_documents.UltimateEndUserDocumentsView.as_view(),
        name='ultimate_end_user_document'
    ),
    # ex: /applications/<uuid:pk>/consignee/
    path(
        route='<uuid:pk>/consignee/',
        view=parties.ApplicationConsignee.as_view(),
        name='consignee'
    ),
    # ex: /applications/<uuid:pk>/consignee/document/
    path(
        route='<uuid:pk>/consignee/document/',
        view=party_documents.ConsigneeDocumentView.as_view(),
        name='consignee_document'
    ),
    # ex: /applications/<uuid:pk>/third-parties/
    path(
        route='<uuid:pk>/third-parties/',
        view=parties.ApplicationThirdParties.as_view(),
        name='third_parties'
    ),
    # ex: /applications/<uuid:pk>/third-parties/<uuid:tp_pk>
    path(
        route='<uuid:pk>/third-parties/<uuid:tp_pk>',
        view=parties.RemoveThirdParty.as_view(),
        name='remove_third_party'
    ),
    # ex: /applications/<uuid:pk>/third-parties/<uuid:tp_pk>/document/
    path(
        route='<uuid:pk>/third-parties/<uuid:tp_pk>/document/',
        view=party_documents.ThirdPartyDocumentView.as_view(),
        name='third_party_document'
    ),
    # ex: /applications/<uuid:pk>/sites/
    path(
        route='<uuid:pk>/sites/',
        view=sites.ApplicationSites.as_view(),
        name='application_sites'
    ),
    # ex: /applications/<uuid:pk>/external_locations/
    path(
        route='<uuid:pk>/external_locations/',
        view=external_locations.ApplicationExternalLocations.as_view(),
        name='application_external_locations'
    ),
    # ex: /applications/<uuid:pk>/external_locations/<uuid:ext_loc_pk>/
    path(
        route='<uuid:pk>/external_locations/<uuid:ext_loc_pk>/',
        view=external_locations.ApplicationRemoveExternalLocation.as_view(),
        name='application_remove_external_location'
    ),
    # ex: /applications/<uuid:pk>/countries/
    path(
        route='<uuid:pk>/countries/',
        view=countries.ApplicationCountries.as_view(),
        name='countries'
    ),
    # ex: /applications/<uuid:pk>/documents/
    path(
        route='<uuid:pk>/documents/',
        view=documents.ApplicationDocumentView.as_view(),
        name='application_documents'
    ),
    # ex: /applications/<uuid:pk>/documents/<uuid:doc_pk>/
    path(
        route='<uuid:pk>/documents/<uuid:doc_pk>/',
        view=documents.ApplicationDocumentDetailView.as_view(),
        name='application_document'
    ),
]
