from django.urls import path

from static.private_venture_gradings import views

app_name = "private_venture_gradings"

urlpatterns = [
    path("", views.PVGradingsList.as_view(), name="private_venture_gradings"),
    path("gov/", views.GovPVGradingsList.as_view(), name="gov_private_venture_gradings"),
]
