from django.urls import path

from static.private_venture_gradings.views import PVGradingsList

app_name = "private_venture_gradings"

urlpatterns = [
    path("", PVGradingsList.as_view(), name="private_venture_gradings"),
]
