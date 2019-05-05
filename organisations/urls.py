from django.urls import path

from organisations import views, views_site

app_name = 'organisations'

urlpatterns = [
    path('', views.organisations_list, name='organisations'),
    path('<uuid:pk>/', views.organisation_detail, name='organisation'),
    path('<uuid:pk>/sites', views_site.SiteList.as_view(), name='sites'),
    path('validate/', views.Validate.as_view(), name='validate')
]
