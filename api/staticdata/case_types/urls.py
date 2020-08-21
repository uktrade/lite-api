from django.urls import path

from api.staticdata.case_types import views

app_name = "case_types"

urlpatterns = [
    path("", views.CaseTypes.as_view(), name="case_types"),
]
