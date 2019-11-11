from django.urls import path

from applications.views import applications, goods, parties, party_documents, \
    external_locations, sites, countries, documents

app_name = 'applications'

urlpatterns = [
    # Applications
    path(route='', view=applications.ApplicationList.as_view(), name='applications'),
    path(route='<uuid:pk>/', view=applications.ApplicationDetail.as_view(), name='application'),
    path(route='<uuid:pk>/submit/', view=applications.ApplicationSubmission.as_view(), name='application_submit'),
    path(route='<uuid:pk>/status/', view=applications.ApplicationManageStatus.as_view(), name='manage_status'),

    # Goods
    path(route='<uuid:pk>/goods/', view=goods.ApplicationGoodsOnApplication.as_view(), name='application_goods'),
    path(route='good-on-application/<uuid:obj_pk>/', view=goods.ApplicationGoodOnApplication.as_view(), name='good_on_application'),

    # Goods types
    path(route='<uuid:pk>/goodstypes/', view=goods.ApplicationGoodsTypes.as_view(), name='application_goodstypes'),
    path(route='<uuid:pk>/goodstype/<uuid:goodstype_pk>/',  view=goods.ApplicationGoodsType.as_view(), name='application_goodstype'),
    path(route='<uuid:pk>/goodstype/<uuid:goods_type_pk>/document/',view=documents.GoodsTypeDocumentView.as_view(), name='goods_type_document'),
    path(route='<uuid:pk>/goodstype/<uuid:goodstype_pk>/assign-countries/', view=goods.ApplicationGoodsTypeCountries.as_view(),
         name='application_goodstype_assign_countries'),

    # End user
    path(route='<uuid:pk>/end-user/', view=parties.ApplicationEndUser.as_view(), name='end_user'),
    path(route='<uuid:pk>/end-user/document/', view=party_documents.EndUserDocumentView.as_view(), name='end_user_document'),

    # Ultimate end users
    path(route='<uuid:pk>/ultimate-end-users/', view=parties.ApplicationUltimateEndUsers.as_view(), name='ultimate_end_users'),
    path(route='<uuid:pk>/ultimate-end-users/<uuid:ueu_pk>', view=parties.RemoveApplicationUltimateEndUser.as_view(), name='remove_ultimate_end_user'),
    path(route='<uuid:pk>/ultimate-end-user/<uuid:ueu_pk>/document/', view=party_documents.UltimateEndUserDocumentsView.as_view(),
         name='ultimate_end_user_document'),

    # Consignee
    path(route='<uuid:pk>/consignee/', view=parties.ApplicationConsignee.as_view(), name='consignee'),
    path(route='<uuid:pk>/consignee/document/', view=party_documents.ConsigneeDocumentView.as_view(), name='consignee_document'),

    # Third parties
    path(route='<uuid:pk>/third-parties/', view=parties.ApplicationThirdParties.as_view(), name='third_parties'),
    path(route='<uuid:pk>/third-parties/<uuid:tp_pk>', view=parties.RemoveThirdParty.as_view(), name='remove_third_party'),
    path(route='<uuid:pk>/third-parties/<uuid:tp_pk>/document/', view=party_documents.ThirdPartyDocumentView.as_view(), name='third_party_document'),

    # Sites, locations and countries
    path(route='<uuid:pk>/sites/', view=sites.ApplicationSites.as_view(), name='application_sites'),
    path(route='<uuid:pk>/external_locations/', view=external_locations.ApplicationExternalLocations.as_view(), name='application_external_locations'),
    path(route='<uuid:pk>/external_locations/<uuid:ext_loc_pk>/', view=external_locations.ApplicationRemoveExternalLocation.as_view(),
         name='application_remove_external_location'),
    path(route='<uuid:pk>/countries/', view=countries.ApplicationCountries.as_view(), name='countries'),

    # Supporting Documents
    path(route='<uuid:pk>/documents/', view=documents.ApplicationDocumentView.as_view(), name='application_documents'),
    path(route='<uuid:pk>/documents/<uuid:doc_pk>/', view=documents.ApplicationDocumentDetailView.as_view(), name='application_document'),
]
