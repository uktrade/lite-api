from django.urls import path

from users import views

app_name = "users"

urlpatterns = [
    path("", views.UserList.as_view(), name="users"),
    path("authenticate/", views.AuthenticateExporterUser.as_view(), name="authenticate"),
    path("<uuid:pk>/", views.UserDetail.as_view(), name="user"),
    path("me/", views.UserMeDetail.as_view(), name="me"),
    path("notifications/", views.NotificationViewSet.as_view(), name="notifications"),
]
