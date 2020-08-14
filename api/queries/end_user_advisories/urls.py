from django.urls import path

from api.queries.end_user_advisories import views

app_name = "end_user_advisories"

urlpatterns = [
    path("", views.EndUserAdvisoriesList.as_view(), name="end_user_advisories"),
    path("<uuid:pk>/", views.EndUserAdvisoryDetail.as_view(), name="end_user_advisory"),
]
