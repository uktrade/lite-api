from django.urls import path

from organisations.views import main, sites, external_locations, users, roles_views

app_name = "organisations"

urlpatterns = [
    path("", main.OrganisationsList.as_view(), name="organisations"),
    path("<uuid:pk>/", main.OrganisationsDetail.as_view(), name="organisation"),
    path("<uuid:org_pk>/users/", users.UsersList.as_view(), name="users"),
    path("<uuid:org_pk>/users/<uuid:user_pk>/", users.UserDetail.as_view(), name="user"),
    path("<uuid:org_pk>/sites/", sites.SitesList.as_view(), name="sites"),
    path("<uuid:org_pk>/sites/<uuid:site_pk>/", sites.SiteDetail.as_view(), name="site"),
    path(
        "<uuid:org_pk>/external_locations/",
        external_locations.ExternalLocationList.as_view(),
        name="external_locations",
    ),
    path("<uuid:org_pk>/roles/", roles_views.RolesViews.as_view(), name="roles_views"),
    path("<uuid:org_pk>/roles/<uuid:pk>/", roles_views.RoleDetail.as_view(), name="role"),
    path("permissions/", roles_views.PermissionsView.as_view(), name="permissions"),
]
