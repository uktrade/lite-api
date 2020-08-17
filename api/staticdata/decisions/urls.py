from django.urls import path

from api.staticdata.decisions import views

app_name = "decisions"

urlpatterns = [
    path("", views.Decisions.as_view(), name="decisions"),
]
