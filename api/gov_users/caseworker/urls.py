from django.urls import path

from api.gov_users.caseworker.views import GovUsersList, GovUserUpdate


app_name = "caseworker_gov_users"

urlpatterns = [
    path("", GovUsersList.as_view(), name="list"),
    path("<uuid:pk>/update/", GovUserUpdate.as_view(), name="update"),
]
