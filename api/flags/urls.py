from django.urls import path

from api.flags import views

app_name = "flags"

urlpatterns = [
    path("", views.FlagsListView.as_view(), name="flags"),
    path("<uuid:pk>/", views.FlagsRetrieveView.as_view(), name="flag"),
    path("assign/", views.AssignFlags.as_view(), name="assign_flags"),
]
