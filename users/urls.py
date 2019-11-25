from django.urls import path

from users import views

app_name = "users"

urlpatterns = [
    # ex: /users/
    path("", views.UserList.as_view(), name="users"),
    # ex: /users/authenticate/
    path("authenticate/", views.AuthenticateExporterUser.as_view(), name="authenticate"),
    # ex: /users/<uuid:pk>/
    path("<uuid:pk>/", views.UserDetail.as_view(), name="user"),
    # ex: /users/me/
    path("me/", views.UserMeDetail.as_view(), name="me"),
    # ex: /users/notifications/
    path("notifications/", views.NotificationViewSet.as_view(), name="notifications"),
    # ex: /users/case-notification/
    path("case-notification/", views.CaseNotification.as_view(), name="case_notification"),
]
