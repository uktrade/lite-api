from django.urls import path

from teams import views

app_name = "teams"

urlpatterns = [
    path("", views.TeamList.as_view(), name="teams"),
    path("<uuid:pk>/", views.TeamDetail.as_view(), name="team"),
    path("<uuid:pk>/users/", views.UsersByTeamsList.as_view(), name="team_users"),
]
