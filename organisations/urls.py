from django.urls import path

from organisations import views, views_site

app_name = 'organisations'

urlpatterns = [
    path('', views.organisations_list, name='organisations'),
    path('<uuid:pk>/', views.organisation_detail, name='organisation'),
    path('<uuid:org_pk>/sites', views_site.SiteViews.as_view(), name='sites'),
    path('<uuid:org_pk>/sites/<uuid:site_pk>', views_site.SiteViews.as_view(), name='site'),
    path('', views.OrganisationsList.as_view(), name='organisations'),
    path('<uuid:pk>/', views.OrganisationsDetail.as_view(), name='organisation'),
    path('validate/', views.Validate.as_view(), name='validate')
]
