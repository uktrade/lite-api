from django.urls import path

from organisations import views, views_site

app_name = 'organisations'

urlpatterns = [
    path('', views.OrganisationsList.as_view(), name='organisations'),
    path('<uuid:pk>/', views.OrganisationsDetail.as_view(), name='organisation'),
    path('<uuid:org_pk>/sites/', views_site.OrgSiteList.as_view(), name='organisation_sites'),
    path('<uuid:org_pk>/sites/<uuid:site_pk>/', views_site.SiteDetail.as_view(), name='organisation_site'),
    path('sites/', views_site.SiteList.as_view(), name='sites'),
    path('sites/<uuid:pk>/', views_site.SiteDetail.as_view(), name='site'),
]
