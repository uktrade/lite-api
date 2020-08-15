from django.urls import path

from api.staticdata.units import views

app_name = "units"

urlpatterns = [path("", views.UnitsList.as_view(), name="units")]
