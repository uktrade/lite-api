from django.urls import path

from api.static.trade_control import views

app_name = "trade_control"

urlpatterns = [
    path("activities/", views.Activities.as_view(), name="activities"),
    path("product-categories/", views.ProductCategories.as_view(), name="product_categories"),
]
