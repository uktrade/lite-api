from django.urls import path

from applications.views import views, application_goods, application_parties, application_party_document_views, \
    application_external_locations_views, application_sites_views, application_countries, application_documents

app_name = 'applications'

urlpatterns = [
    # ex: /applications/ - List all/application/submitted applications
    # ex: /applications/?submitted=
    path(
        route='',
        view=views.ApplicationList.as_view(),
        name='applications'
    ),
    # ex: /applications/<uuid:pk>/ - View an application
    path(
        route='<uuid:pk>/',
        view=views.ApplicationDetail.as_view(),
        name='application'
    ),
    # ex: /applications/<uuid:pk>/submit/ - Submit an application
    path(
        route='<uuid:pk>/submit/',
        view=views.ApplicationSubmission.as_view(),
        name='application_submit'
    ),
    # ex: /applications/<uuid:pk>/goods/
    path(
        route='<uuid:pk>/goods/',
        view=application_goods.ApplicationGoods.as_view(),
        name='application_goods'
    ),
    # ex: /applications/<uuid:pk>/goods/<uuid:good_pk>/
    path(
        route='<uuid:pk>/goods/<uuid:good_pk>/',
        view=application_goods.ApplicationGoods.as_view(),
        name='application_good'
    ),
    path(
        route='<uuid:pk>/goodstype/',
        view=application_goods.ApplicationGoodsType.as_view(),
        name='application_goodstype'
    ),
    # ex: /applications/<uuid:pk>/end-user/
    path(
        route='<uuid:pk>/end-user/',
        view=application_parties.ApplicationEndUser.as_view(),
        name='end_user'
    ),
    # ex: /applications/<uuid:pk>/end-user/document/
    path(
        route='<uuid:pk>/end-user/document/',
        view=application_party_document_views.EndUserDocumentView.as_view(),
        name='end_user_document'
    ),
    # ex: /applications/<uuid:pk>/ultimate-end-users/
    path(
        route='<uuid:pk>/ultimate-end-users/',
        view=application_parties.ApplicationUltimateEndUsers.as_view(),
        name='ultimate_end_users'
    ),
    # ex: /applications/<uuid:pk>/ultimate-end-users/<uuid:ueu_pk>
    path(
        route='<uuid:pk>/ultimate-end-users/<uuid:ueu_pk>',
        view=application_parties.RemoveApplicationUltimateEndUser.as_view(),
        name='remove_ultimate_end_user'
    ),
    # ex: /applications/<uuid:pk>/ultimate-end-user/<uuid:ueu_pk>/document/
    path(
        route='<uuid:pk>/ultimate-end-user/<uuid:ueu_pk>/document/',
        view=application_party_document_views.UltimateEndUserDocumentsView.as_view(),
        name='ultimate_end_user_document'
    ),
    # ex: /applications/<uuid:pk>/consignee/
    path(
        route='<uuid:pk>/consignee/',
        view=application_parties.ApplicationConsignee.as_view(),
        name='consignee'
    ),
    # ex: /applications/<uuid:pk>/consignee/document/
    path(
        route='<uuid:pk>/consignee/document/',
        view=application_party_document_views.ConsigneeDocumentView.as_view(),
        name='consignee_document'
    ),
    # ex: /applications/<uuid:pk>/third-parties/
    path(
        route='<uuid:pk>/third-parties/',
        view=application_parties.ApplicationThirdParties.as_view(),
        name='third_parties'
    ),
    # ex: /applications/<uuid:pk>/third-parties/<uuid:tp_pk>
    path(
        route='<uuid:pk>/third-parties/<uuid:tp_pk>',
        view=application_parties.RemoveThirdParty.as_view(),
        name='remove_third_party'
    ),
    # ex: /applications/<uuid:pk>/third-parties/<uuid:tp_pk>/document/
    path(
        route='<uuid:pk>/third-parties/<uuid:tp_pk>/document/',
        view=application_party_document_views.ThirdPartyDocumentView.as_view(),
        name='third_party_document'
    ),
    # ex: /applications/<uuid:pk>/sites/
    path(
        route='<uuid:pk>/sites/',
        view=application_sites_views.ApplicationSites.as_view(),
        name='application_sites'
    ),
    # ex: /applications/<uuid:pk>/external_locations/
    path(
        route='<uuid:pk>/external_locations/',
        view=application_external_locations_views.ApplicationExternalLocations.as_view(),
        name='application_external_locations'
    ),
    # ex: /applications/<uuid:pk>/countries/
    path(
        route='<uuid:pk>/countries/',
        view=application_countries.ApplicationCountries.as_view(),
        name='countries'
    ),
    # ex: /applications/<uuid:pk>/documents/
    path(
        route='<uuid:pk>/documents/',
        view=application_documents.ApplicationDocumentView.as_view(),
        name='application_documents'
    ),
    # ex: /applications/<uuid:pk>/documents/<uuid:doc_pk>/
    path(
        route='<uuid:pk>/documents/<uuid:doc_pk>/',
        view=application_documents.ApplicationDocumentDetailView.as_view(),
        name='application_document'
    ),
]
