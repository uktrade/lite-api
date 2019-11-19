from django.urls import path

from organisations.views import main, sites, external_locations, users, roles_views

app_name = "organisations"

urlpatterns = [
    # ex: /organisations/ - View all organisations
    path("", main.OrganisationsList.as_view(), name="organisations"),
    # ex: /organisations/<uuid:pk>/ - View a specific organisation
    path("<uuid:pk>/", main.OrganisationsDetail.as_view(), name="organisation"),
    # ex: /organisations/<uuid:org_pk>/users/ - View all users for that organisation
    path("<uuid:org_pk>/users/", users.UsersList.as_view(), name="users"),
    # ex: /organisations/<uuid:org_pk>/users/<uuid:user_pk> - View all users for that organisation
    path("<uuid:org_pk>/users/<uuid:user_pk>/", users.UserDetail.as_view(), name="user"),
    # ex: /organisations/<uuid:pk>/sites/ - View all sites belonging to an organisation
    path("<uuid:org_pk>/sites/", sites.SitesList.as_view(), name="sites"),
    # ex: /organisations/<uuid:pk>/sites/<uuid:pk>/ - View a specific site
    path("<uuid:org_pk>/sites/<uuid:site_pk>/", sites.SiteDetail.as_view(), name="site"),
    # ex: /organisations/external_locations/ - View all external locations belonging to the users organisation
    path(
        "<uuid:org_pk>/external_locations/",
        external_locations.ExternalLocationList.as_view(),
        name="external_locations",
    ),
    path("<uuid:org_pk>/roles/", roles_views.RolesViews.as_view(), name="roles_views"),
    path("<uuid:org_pk>/roles/<uuid:pk>/", roles_views.RoleDetail.as_view(), name="role"),
    path("permissions/", roles_views.PermissionsView.as_view(), name="permissions"),
]
