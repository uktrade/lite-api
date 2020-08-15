from django.urls import path

from api.static.decisions import views

app_name = "decisions"

urlpatterns = [
    path("", views.Decisions.as_view(), name="decisions"),
]
