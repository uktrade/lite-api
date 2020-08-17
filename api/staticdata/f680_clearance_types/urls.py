from django.urls import path

from api.staticdata.f680_clearance_types import views

app_name = "f680_clearance_types"

urlpatterns = [path("", views.F680ClearanceTypesView.as_view(), name="f680_clearance_types")]
