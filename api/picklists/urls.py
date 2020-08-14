from django.urls import path

from api.picklists import views

app_name = "picklist_items"

urlpatterns = [
    path("", views.PickListsView.as_view(), name="picklist_items"),
    path("<uuid:pk>/", views.PicklistItemDetail.as_view(), name="picklist_item"),
]
