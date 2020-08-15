from django.urls import path

from api.static.good_item_types import views

app_name = "item-types"

urlpatterns = [
    path("", views.GoodItemTypes.as_view(), name="item_types"),
]
