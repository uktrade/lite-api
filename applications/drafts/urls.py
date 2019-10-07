from django.urls import path

from applications.drafts.views import draft_external_locations_views, draft_sites_views, draft_documents, \
    draft_countries, views, draft_goods, draft_party_document_views, draft_parties

app_name = 'drafts'

urlpatterns = [
    # ex: /drafts/<uuid:pk>/
    path(
        route='<uuid:pk>/',
        view=views.DraftDetail.as_view(),
        name='draft'
    ),
    # ex: /drafts/<uuid:pk>/goods/
    path(
        route='<uuid:pk>/goods/',
        view=draft_goods.DraftGoods.as_view(),
        name='draft_goods'
    ),
    # ex: /drafts/<uuid:pk>/goods/<uuid:good_pk>/
    path(
        route='<uuid:pk>/goods/<uuid:good_pk>/',
        view=draft_goods.DraftGoods.as_view(),
        name='draft_good'
    ),
    # ex: /drafts/<uuid:pk>/goodstype/
    path(
        route='<uuid:pk>/goodstype/',
        view=draft_goods.DraftGoodsType.as_view(),
        name='draft_goodstype'
    ),
    # ex: /drafts/<uuid:pk>/end-user/
    path(
        route='<uuid:pk>/end-user/',
        view=draft_parties.DraftEndUser.as_view(),
        name='end_user'
    ),
    # ex: /drafts/<uuid:pk>/end-user/document/
    path(
        route='<uuid:pk>/end-user/document/',
        view=draft_party_document_views.EndUserDocumentView.as_view(),
        name='end_user_document'
    ),
    # ex: /drafts/<uuid:pk>/ultimate-end-users/
    path(
        route='<uuid:pk>/ultimate-end-users/',
        view=draft_parties.DraftUltimateEndUsers.as_view(),
        name='ultimate_end_users'
    ),
    # ex: /drafts/<uuid:pk>/ultimate-end-users/<uuid:ueu_pk>
    path(
        route='<uuid:pk>/ultimate-end-users/<uuid:ueu_pk>',
        view=draft_parties.RemoveDraftUltimateEndUser.as_view(),
        name='remove_ultimate_end_user'
    ),
    # ex: /drafts/<uuid:pk>/ultimate-end-user/<uuid:ueu_pk>/document/
    path(
        route='<uuid:pk>/ultimate-end-user/<uuid:ueu_pk>/document/',
        view=draft_party_document_views.UltimateEndUserDocumentsView.as_view(),
        name='ultimate_end_user_document'
    ),
    # ex: /drafts/<uuid:pk>/consignee/
    path(
        route='<uuid:pk>/consignee/',
        view=draft_parties.DraftConsignee.as_view(),
        name='consignee'
    ),
    # ex: /drafts/<uuid:pk>/consignee/document/
    path(
        route='<uuid:pk>/consignee/document/',
        view=draft_party_document_views.ConsigneeDocumentView.as_view(),
        name='consignee_document'
    ),
    # ex: /drafts/<uuid:pk>/third-parties/
    path(
        route='<uuid:pk>/third-parties/',
        view=draft_parties.DraftThirdParties.as_view(),
        name='third_parties'
    ),
    # ex: /drafts/<uuid:pk>/third-parties/<uuid:tp_pk>
    path(
        route='<uuid:pk>/third-parties/<uuid:tp_pk>',
        view=draft_parties.RemoveThirdParty.as_view(),
        name='remove_third_party'
    ),
    # ex: /drafts/<uuid:pk>/third-parties/<uuid:tp_pk>/document/
    path(
        route='<uuid:pk>/third-parties/<uuid:tp_pk>/document/',
        view=draft_party_document_views.ThirdPartyDocumentView.as_view(),
        name='third_party_document'
    ),
    # ex: /drafts/<uuid:pk>/sites/
    path(
        route='<uuid:pk>/sites/',
        view=draft_sites_views.DraftSites.as_view(),
        name='draft_sites'
    ),
    # ex: /drafts/<uuid:pk>/external_locations/
    path(
        route='<uuid:pk>/external_locations/',
        view=draft_external_locations_views.DraftExternalLocations.as_view(),
        name='draft_external_locations'
    ),
    # ex: /drafts/<uuid:pk>/countries/
    path(
        route='<uuid:pk>/countries/',
        view=draft_countries.DraftCountries.as_view(),
        name='countries'
    ),
    # ex: /drafts/<uuid:pk>/documents/
    path(
        route='<uuid:pk>/documents/',
        view=draft_documents.DraftDocumentView.as_view(),
        name='draft_documents'
    ),
    # ex: /drafts/<uuid:pk>/documents/<uuid:doc_pk>/
    path(
        route='<uuid:pk>/documents/<uuid:doc_pk>/',
        view=draft_documents.DraftDocumentDetailView.as_view(),
        name='draft_document'
    )
]
