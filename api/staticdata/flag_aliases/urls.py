from django.urls import path

from api.staticdata.flag_aliases import views

app_name = "flag_aliases"

urlpatterns = [
    path("", views.FlagAliases.as_view(), name="flag-aliases"),
]
