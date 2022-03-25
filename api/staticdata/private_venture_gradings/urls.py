from django.urls import path

from api.staticdata.private_venture_gradings import views

app_name = "private_venture_gradings"

urlpatterns = [
    path("", views.PVGradingsList.as_view(), name="private_venture_gradings"),
    path("v2/", views.PVGradingsUpdatedList.as_view(), name="private_venture_gradings_v2"),
    path("gov/", views.GovPVGradingsList.as_view(), name="gov_private_venture_gradings"),
]
