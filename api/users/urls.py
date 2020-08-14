from django.urls import path

from api.users import views

app_name = "users"

urlpatterns = [
    path("", views.CreateUser.as_view(), name="users"),
    path("authenticate/", views.AuthenticateExporterUser.as_view(), name="authenticate"),
    path("<uuid:pk>/", views.UserDetail.as_view(), name="user"),
    path("me/", views.UserMeDetail.as_view(), name="me"),
    path("notifications/", views.NotificationViewSet.as_view(), name="notifications"),
    path("<uuid:pk>/sites/", views.AssignSites.as_view(), name="assign_sites"),
    path("<uuid:pk>/team-queues/", views.UserTeamQueues.as_view(), name="team_queues"),
]
