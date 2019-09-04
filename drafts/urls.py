from django.urls import path

from drafts.views import draft_sites_views, draft_end_user_views, views, draft_external_locations_views, draft_goods, \
    draft_countries, draft_end_user_document_views

app_name = 'drafts'

urlpatterns = [
    path('', views.DraftList.as_view(), name='drafts'),
    path('<uuid:pk>/', views.DraftDetail.as_view(), name='draft'),
    path('<uuid:pk>/goods/', draft_goods.DraftGoods.as_view(), name='draft_goods'),
    path('<uuid:pk>/goods/<uuid:good_pk>/', draft_goods.DraftGoods.as_view(), name='draft_good'),
    path('<uuid:pk>/goodstype/', draft_goods.DraftGoodsType.as_view(), name='draft_goodstype'),
    path('<uuid:pk>/end-user/', draft_end_user_views.DraftEndUser.as_view(), name='end_user'),
    path('<uuid:pk>/end-user/<uuid:eu_pk>/document/', draft_end_user_document_views.EndUserDocuments.as_view(), name='end_user_document'),
    path('<uuid:pk>/ultimate-end-users/', draft_end_user_views.DraftUltimateEndUsers.as_view(), name='ultimate_end_users'),
    path('<uuid:pk>/ultimate-end-user/<uuid:ueu_pk>/document/', draft_end_user_document_views.EndUserDocuments.as_view(), name='ultimate_end_user_document'),
    path('<uuid:pk>/ultimate-end-users/<uuid:ueu_pk>', draft_end_user_views.RemoveDraftUltimateEndUsers.as_view(), name='remove_ultimate_end_users'),
    path('<uuid:pk>/sites/', draft_sites_views.DraftSites.as_view(), name='draft_sites'),
    path('<uuid:pk>/external_locations/', draft_external_locations_views.DraftExternalLocations.as_view(), name='draft_external_locations'),
    path('<uuid:pk>/countries/', draft_countries.DraftCountries.as_view(), name='countries'),
]
