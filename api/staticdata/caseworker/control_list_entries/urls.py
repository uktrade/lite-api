from django.urls import path

from api.staticdata.caseworker.control_list_entries import views

app_name = "control_list_entries"

urlpatterns = [
    path("", views.ControlListEntriesList.as_view(), name="control_list_entries"),
]
