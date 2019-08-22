from django.urls import path

from organisations.views import main, sites, external_locations, users

app_name = 'organisations'

urlpatterns = [
    # ex: /organisations/<uuid:org_pk>/users/ - View all users for that organisation
    path('<uuid:org_pk>/users/', users.OrganisationUsersList.as_view(), name='users'),
    # ex: /organisations/ - View all organisations
    path('', main.OrganisationsList.as_view(), name='organisations'),
    # ex: /organisations/<uuid:pk>/ - View a specific organisation
    path('<uuid:pk>/', main.OrganisationsDetail.as_view(), name='organisation'),
    # ex: /organisations/<uuid:pk>/sites/ - View all sites belonging to an organisation
    path('<uuid:org_pk>/sites/', sites.OrgSiteList.as_view(), name='organisation_sites'),
    # ex: /organisations/<uuid:pk>/sites/<uuid:pk> - View a specific site
    path('<uuid:org_pk>/sites/<uuid:site_pk>/', sites.OrgSiteDetail.as_view(), name='organisation_site'),
    # ex: /organisations/sites/ - View all sites belonging to the users organisation
    path('sites/', sites.SiteList.as_view(), name='sites'),
    # ex: /organisations/sites/<uuid:pk> - View a specific site
    path('sites/<uuid:pk>/', sites.SiteDetail.as_view(), name='site'),
    # ex: /organisations/<uuid:pk>/ - View all external locations belonging to an organisation
    path('external_locations/', external_locations.ExternalLocationList.as_view(), name='external_locations'),
]
