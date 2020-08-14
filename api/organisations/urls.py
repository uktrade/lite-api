from django.urls import path

from api.organisations.views import organisations, sites, external_locations, users, roles, activities

app_name = "organisations"

urlpatterns = [
    path("", organisations.OrganisationsList.as_view(), name="organisations"),
    path("<uuid:pk>/", organisations.OrganisationsDetail.as_view(), name="organisation"),
    path(
        "<uuid:pk>/matching_details/",
        organisations.OrganisationsMatchingDetail.as_view(),
        name="organisation_matching_details",
    ),
    path("<uuid:pk>/status/", organisations.OrganisationStatusView.as_view(), name="organisation_status"),
    path("<uuid:org_pk>/users/", users.UsersList.as_view(), name="users"),
    path("<uuid:org_pk>/users/<uuid:user_pk>/", users.UserDetail.as_view(), name="user"),
    path("<uuid:org_pk>/sites/", sites.SitesList.as_view(), name="sites"),
    path("<uuid:org_pk>/sites/<uuid:pk>/", sites.SiteRetrieveUpdate.as_view(), name="site"),
    path(
        "<uuid:org_pk>/external_locations/",
        external_locations.ExternalLocationList.as_view(),
        name="external_locations",
    ),
    path("<uuid:org_pk>/roles/", roles.RolesViews.as_view(), name="roles_views"),
    path("<uuid:org_pk>/roles/<uuid:pk>/", roles.RoleDetail.as_view(), name="role"),
    path("permissions/", roles.PermissionsView.as_view(), name="permissions"),
    path("<uuid:pk>/activity/", activities.OrganisationActivityView.as_view(), name="activities"),
    path("<uuid:pk>/sites-activity/", activities.SitesActivityView.as_view(), name="sites-activity"),
]
