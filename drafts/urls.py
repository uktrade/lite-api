from django.urls import path

from drafts.views import draft_sites_views, draft_end_user_views, views, draft_external_locations_views, draft_goods

app_name = 'drafts'

urlpatterns = [
    path('', views.DraftList.as_view(), name='drafts'),
    path('<uuid:pk>/', views.DraftDetail.as_view(), name='draft'),
    path('<uuid:pk>/goods/', draft_goods.DraftGoods.as_view(), name='draft_goods'),
    path('<uuid:pk>/goods/<uuid:good_pk>/', draft_goods.DraftGoods.as_view(), name='draft_good'),
    path('<uuid:pk>/end-user/', draft_end_user_views.DraftEndUser.as_view(), name='end_user'),
    path('<uuid:pk>/sites/', draft_sites_views.DraftSites.as_view(), name='draft_sites'),
    path('<uuid:pk>/external_locations', draft_external_locations_views.DraftExternalLocations.as_view(), name='draft_external_locations')
]
