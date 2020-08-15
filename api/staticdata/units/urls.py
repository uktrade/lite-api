from django.urls import path

from api.static.units import views

app_name = "units"

urlpatterns = [path("", views.UnitsList.as_view(), name="units")]
