from django.urls import path

from gov_users.views import gov_user_views
from gov_users.views import roles_views

app_name = 'gov_users'
urlpatterns = [
    path('', gov_user_views.GovUserList.as_view(), name='gov_users'),
    path('authenticate/', gov_user_views.AuthenticateGovUser.as_view(), name='authenticate'),
    path('<uuid:pk>/', gov_user_views.GovUserDetail.as_view(), name='gov_user'),
    path('roles/', roles_views.RolesViews.as_view(), name='roles_views'),
    path('roles/<uuid:pk>/', roles_views.RoleDetail.as_view(), name='role'),
    path('permissions/', roles_views.PermissionsView.as_view(), name='permissions'),
    # ex: /users/me/
    path('me/', gov_user_views.UserMeDetail.as_view(), name='me'),
]
