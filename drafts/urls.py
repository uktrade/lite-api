from django.urls import path

from drafts import views, draft_sites_views


app_name = 'drafts'

urlpatterns = [
    path('', views.DraftList.as_view(), name='drafts'),
    path('<uuid:pk>/', views.DraftDetail.as_view(), name='draft'),
    path('<uuid:pk>/goods/', views.DraftGoods.as_view(), name='draft_goods'),
    path('<uuid:pk>/sites/', draft_sites_views.DraftSites.as_view(), name='draft_sites'),
]
