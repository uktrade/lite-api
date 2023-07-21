from django.urls import path, include

app_name = "queries"

urlpatterns = [
    path("end-user-advisories/", include("api.queries.end_user_advisories.urls")),
]
