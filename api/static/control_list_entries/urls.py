from django.urls import path

from api.static.control_list_entries import views

app_name = "control_list_entries"

urlpatterns = [
    path("", views.ControlListEntriesList.as_view(), name="control_list_entries"),
    path("<str:rating>/", views.ControlListEntryDetail.as_view(), name="control_list_entry",),
]
